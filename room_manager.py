import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from config_manager import ConfigManager
from metadata import MetadataManager
from platform_parser import PlatformParser
from target_resolver import TargetResolver


class Room:
    def __init__(self, platform: str, room_id: str, name: str = "", auto_record: bool = True):
        self.platform = platform
        self.room_id = room_id
        self.name = name
        self.auto_record = auto_record
        self.is_live = False
        self.is_recording = False
        self.title = ""
        self.streamer_name = ""
        self.start_time = None
        self.recording_id = None
        self.last_check_time = None
        self.check_interval = 60

    def to_dict(self) -> Dict:
        return {
            "platform": self.platform,
            "room_id": self.room_id,
            "name": self.name,
            "auto_record": self.auto_record,
            "is_live": self.is_live,
            "is_recording": self.is_recording,
            "title": self.title,
            "streamer_name": self.streamer_name,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None,
            "check_interval": self.check_interval,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Room":
        room = cls(
            platform=data.get("platform", ""),
            room_id=data.get("room_id", ""),
            name=data.get("name", ""),
            auto_record=data.get("auto_record", True),
        )
        room.is_live = data.get("is_live", False)
        room.is_recording = data.get("is_recording", False)
        room.title = data.get("title", "")
        room.streamer_name = data.get("streamer_name", "")
        return room


class RoomManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.metadata = MetadataManager()
        self.parser = PlatformParser()
        self.target_resolver = TargetResolver()

        self.rooms: Dict[str, Room] = {}
        self.room_lock = threading.RLock()
        self.recorder = None

        self.monitor_thread: Optional[threading.Thread] = None
        self.running = False
        self.stop_event = threading.Event()

        self.monitor_interval_sec = max(1, int(self.config.get("monitor.interval_sec", 60)))
        self.monitor_max_workers = max(1, int(self.config.get("monitor.max_workers", 8)))
        self.monitor_request_timeout_sec = max(1, int(self.config.get("monitor.request_timeout_sec", 10)))

        self._load_rooms_from_config()

    def _load_rooms_from_config(self):
        rooms_data = self.config.get_rooms()
        with self.room_lock:
            for room_data in rooms_data:
                room = Room.from_dict(room_data)
                self.rooms[self._get_room_key(room.platform, room.room_id)] = room
                print(f"[RoomManager] Loaded room: {room.platform}/{room.room_id}")

    def _get_room_key(self, platform: str, room_id: str) -> str:
        return f"{platform}:{room_id}"

    def add_room(self, platform: str, room_id: str, name: str = "", auto_record: bool = True) -> bool:
        key = self._get_room_key(platform, room_id)
        with self.room_lock:
            if key in self.rooms:
                print(f"[RoomManager] Room already exists: {key}")
                return False

            room = Room(platform, room_id, name, auto_record)
            self.rooms[key] = room

        self.config.add_room(
            {
                "platform": platform,
                "room_id": room_id,
                "name": name,
                "auto_record": auto_record,
            }
        )
        print(f"[RoomManager] Added room: {key}")
        return True

    def remove_room(self, platform: str, room_id: str) -> bool:
        key = self._get_room_key(platform, room_id)
        with self.room_lock:
            room = self.rooms.get(key)
            if not room:
                return False

        if room.is_recording:
            self.stop_recording(platform, room_id)

        with self.room_lock:
            if key in self.rooms:
                del self.rooms[key]

        self.config.remove_room(platform, room_id)
        print(f"[RoomManager] Removed room: {key}")
        return True

    def get_room(self, platform: str, room_id: str) -> Optional[Room]:
        with self.room_lock:
            return self.rooms.get(self._get_room_key(platform, room_id))

    def get_all_rooms(self) -> List[Room]:
        with self.room_lock:
            return list(self.rooms.values())

    def get_room_list(self) -> List[Dict]:
        with self.room_lock:
            return [room.to_dict() for room in self.rooms.values()]

    def search_targets(self, platform: str, query: str, limit: int = 20) -> List[Dict]:
        return self.target_resolver.search_targets(platform, query, limit)

    def add_room_by_query(
        self,
        platform: str,
        query: str,
        name: str = "",
        auto_record: bool = True,
    ) -> Dict:
        candidates = self.search_targets(platform, query, limit=20)
        if not candidates:
            return {"success": False, "reason": "no_candidates", "candidates": []}
        if len(candidates) > 1:
            return {"success": False, "reason": "multiple_candidates", "candidates": candidates}

        candidate = candidates[0]
        room_name = name or candidate.get("nickname", "")
        ok = self.add_room(candidate["platform"], candidate["room_id"], room_name, auto_record)
        return {
            "success": ok,
            "reason": "added" if ok else "already_exists",
            "candidates": candidates,
            "target": candidate,
        }

    def _fetch_room_status(self, platform: str, room_id: str) -> Optional[Dict]:
        return self.parser.get_live_status(
            platform,
            room_id,
            timeout_sec=self.monitor_request_timeout_sec,
        )

    def _apply_room_status(self, room: Room, status: Dict) -> None:
        room.is_live = bool(status.get("is_live", False))
        room.title = status.get("title", "") or ""
        room.streamer_name = status.get("streamer_name", "") or room.streamer_name
        room.last_check_time = datetime.now()

    def check_room_status(self, platform: str, room_id: str) -> Optional[Dict]:
        status = self._fetch_room_status(platform, room_id)
        if not status:
            return None
        with self.room_lock:
            room = self.rooms.get(self._get_room_key(platform, room_id))
            if room:
                self._apply_room_status(room, status)
        return status

    def _handle_room_status(self, room: Room, status: Dict) -> None:
        was_live = room.is_live
        self._apply_room_status(room, status)
        is_live = room.is_live

        if is_live and not was_live:
            print(f"[RoomManager] Stream started: {room.platform}/{room.room_id} - {room.streamer_name}")
            if room.auto_record and not room.is_recording:
                self.start_recording(room.platform, room.room_id)
            return

        if not is_live and was_live and room.is_recording:
            print(f"[RoomManager] Stream ended: {room.platform}/{room.room_id}")
            self.stop_recording(room.platform, room.room_id)

    def start_recording(self, platform: str, room_id: str) -> bool:
        with self.room_lock:
            room = self.rooms.get(self._get_room_key(platform, room_id))

        if not room:
            print(f"[RoomManager] Room not found: {platform}/{room_id}")
            return False

        if room.is_recording:
            print(f"[RoomManager] Already recording: {platform}/{room_id}")
            return True

        if not self.recorder:
            print("[RoomManager] Recorder is not configured")
            return False

        stream_url = self.parser.get_stream_url(platform, room_id)
        if not stream_url:
            print(f"[RoomManager] Failed to get stream URL: {platform}/{room_id}")
            return False

        streamer_name = room.streamer_name or room.name or f"{platform}_{room_id}"
        success = self.recorder.start_recording(platform, room_id, stream_url, streamer_name)
        if success:
            with self.room_lock:
                room.is_recording = True
                room.start_time = datetime.now()
            print(f"[RoomManager] Recording started: {platform}/{room_id}")
        return success

    def stop_recording(self, platform: str, room_id: str) -> bool:
        with self.room_lock:
            room = self.rooms.get(self._get_room_key(platform, room_id))

        if not room or not room.is_recording:
            return False

        if not self.recorder:
            print("[RoomManager] Recorder is not configured")
            return False

        success = self.recorder.stop_recording(platform, room_id)
        if success:
            with self.room_lock:
                room.is_recording = False
            print(f"[RoomManager] Recording stopped: {platform}/{room_id}")
        return success

    def _safe_fetch_status(self, room: Room) -> Tuple[Room, Optional[Dict], Optional[Exception]]:
        try:
            return room, self._fetch_room_status(room.platform, room.room_id), None
        except Exception as exc:
            return room, None, exc

    def _monitor_once(self, rooms_snapshot: List[Room]) -> None:
        if not rooms_snapshot:
            return

        workers = max(1, min(self.monitor_max_workers, len(rooms_snapshot)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(self._safe_fetch_status, room) for room in rooms_snapshot]
            for future in as_completed(futures):
                if self.stop_event.is_set():
                    return

                room, status, error = future.result()
                if error:
                    print(f"[RoomManager] Monitor error for {room.platform}/{room.room_id}: {error}")
                    continue
                if not status:
                    continue

                room_key = self._get_room_key(room.platform, room.room_id)
                with self.room_lock:
                    current_room = self.rooms.get(room_key)
                    if current_room:
                        self._handle_room_status(current_room, status)

    def start_monitor(self):
        if self.running:
            return

        self.running = True
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("[RoomManager] Monitor started")

    def stop_monitor(self):
        self.running = False
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("[RoomManager] Monitor stopped")

    def _monitor_loop(self):
        while self.running and not self.stop_event.is_set():
            with self.room_lock:
                rooms_snapshot = list(self.rooms.values())

            self._monitor_once(rooms_snapshot)

            if self.stop_event.wait(self.monitor_interval_sec):
                break

    def set_recorder(self, recorder):
        required_methods = ("start_recording", "stop_recording")
        missing = [method for method in required_methods if not hasattr(recorder, method)]
        if missing:
            raise TypeError(
                f"Recorder contract mismatch. Missing method(s): {', '.join(missing)}"
            )
        self.recorder = recorder


if __name__ == "__main__":
    cfg = ConfigManager()
    manager = RoomManager(cfg)
    print("RoomManager initialized.")
    print(f"Loaded {len(manager.rooms)} room(s).")
