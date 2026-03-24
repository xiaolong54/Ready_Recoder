import threading
import time
from typing import Dict, List, Optional
from datetime import datetime
from platform_parser import PlatformParser
from config_manager import ConfigManager
from metadata import MetadataManager


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
            "check_interval": self.check_interval
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Room":
        room = cls(
            platform=data.get("platform", ""),
            room_id=data.get("room_id", ""),
            name=data.get("name", ""),
            auto_record=data.get("auto_record", True)
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
        self.rooms: Dict[str, Room] = {}
        self.recorder = None
        self.monitor_thread = None
        self.running = False

        self._load_rooms_from_config()

    def _load_rooms_from_config(self):
        rooms_data = self.config.get_rooms()
        for room_data in rooms_data:
            room = Room.from_dict(room_data)
            key = self._get_room_key(room.platform, room.room_id)
            self.rooms[key] = room
            print(f"[RoomManager] 加载房间: {room.platform}/{room.room_id}")

    def _get_room_key(self, platform: str, room_id: str) -> str:
        return f"{platform}:{room_id}"

    def add_room(self, platform: str, room_id: str, name: str = "", auto_record: bool = True) -> bool:
        key = self._get_room_key(platform, room_id)
        if key in self.rooms:
            print(f"[RoomManager] 房间已存在: {key}")
            return False

        room = Room(platform, room_id, name, auto_record)
        self.rooms[key] = room

        self.config.add_room({
            "platform": platform,
            "room_id": room_id,
            "name": name,
            "auto_record": auto_record
        })

        print(f"[RoomManager] 添加房间成功: {key}")
        return True

    def remove_room(self, platform: str, room_id: str) -> bool:
        key = self._get_room_key(platform, room_id)
        if key in self.rooms:
            room = self.rooms[key]
            if room.is_recording:
                self.stop_recording(platform, room_id)

            del self.rooms[key]
            self.config.remove_room(platform, room_id)
            print(f"[RoomManager] 删除房间: {key}")
            return True
        return False

    def get_room(self, platform: str, room_id: str) -> Optional[Room]:
        key = self._get_room_key(platform, room_id)
        return self.rooms.get(key)

    def get_all_rooms(self) -> List[Room]:
        return list(self.rooms.values())

    def get_room_list(self) -> List[Dict]:
        return [room.to_dict() for room in self.rooms.values()]

    def check_room_status(self, platform: str, room_id: str) -> Optional[Dict]:
        status = self.parser.get_live_status(platform, room_id)
        room = self.get_room(platform, room_id)
        if room and status:
            room.is_live = status.get("is_live", False)
            room.title = status.get("title", "")
            room.streamer_name = status.get("streamer_name", "")
            room.last_check_time = datetime.now()
        return status

    def start_recording(self, platform: str, room_id: str) -> bool:
        room = self.get_room(platform, room_id)
        if not room:
            print(f"[RoomManager] 房间不存在: {platform}/{room_id}")
            return False

        if room.is_recording:
            print(f"[RoomManager] 房间已在录制中: {platform}/{room_id}")
            return True

        stream_url = self.parser.get_stream_url(platform, room_id)
        if not stream_url:
            print(f"[RoomManager] 无法获取直播流地址: {platform}/{room_id}")
            return False

        if self.recorder:
            success = self.recorder.start(platform, room_id, stream_url, room.streamer_name)
            if success:
                room.is_recording = True
                room.start_time = datetime.now()
                print(f"[RoomManager] 开始录制: {platform}/{room_id}")
            return success

        print(f"[RoomManager] 未设置录制器")
        return False

    def stop_recording(self, platform: str, room_id: str) -> bool:
        room = self.get_room(platform, room_id)
        if not room or not room.is_recording:
            return False

        if self.recorder:
            success = self.recorder.stop()
            if success:
                room.is_recording = False
                print(f"[RoomManager] 停止录制: {platform}/{room_id}")
            return success

        return False

    def start_monitor(self):
        if self.running:
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("[RoomManager] 开始监控房间")

    def stop_monitor(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("[RoomManager] 停止监控")

    def _monitor_loop(self):
        while self.running:
            for room in self.rooms.values():
                try:
                    status = self.check_room_status(room.platform, room.room_id)
                    if status:
                        was_live = room.is_live
                        is_live = status.get("is_live", False)

                        if is_live and not was_live:
                            print(f"[RoomManager] 主播开播: {room.platform}/{room.room_id} - {room.streamer_name}")
                            if room.auto_record and not room.is_recording:
                                self.start_recording(room.platform, room.room_id)

                        elif not is_live and was_live and room.is_recording:
                            print(f"[RoomManager] 主播下播: {room.platform}/{room.room_id}")
                            self.stop_recording(room.platform, room.room_id)

                except Exception as e:
                    print(f"[RoomManager] 检查房间失败 {room.platform}/{room.room_id}: {e}")

            time.sleep(60)

    def set_recorder(self, recorder):
        self.recorder = recorder


if __name__ == "__main__":
    config = ConfigManager()
    manager = RoomManager(config)
    print("房间管理器初始化成功")
    print(f"已加载 {len(manager.rooms)} 个房间")
