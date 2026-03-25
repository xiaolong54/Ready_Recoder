import time

from room_manager import RoomManager


class DummyConfig:
    def __init__(self):
        self.rooms = []
        self.values = {
            "monitor": {
                "interval_sec": 1,
                "max_workers": 4,
                "request_timeout_sec": 1,
            }
        }

    def get(self, key, default=None):
        parts = key.split(".")
        value = self.values
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return default
        return default if value is None else value

    def get_rooms(self):
        return list(self.rooms)

    def add_room(self, room):
        self.rooms.append(room)

    def remove_room(self, platform, room_id):
        self.rooms = [
            r for r in self.rooms if not (r.get("platform") == platform and r.get("room_id") == room_id)
        ]


class FakeRecorder:
    def __init__(self):
        self.start_calls = []
        self.stop_calls = []

    def start_recording(self, platform, room_id, stream_url, streamer_name):
        self.start_calls.append((platform, room_id, stream_url, streamer_name))
        return True

    def stop_recording(self, platform, room_id):
        self.stop_calls.append((platform, room_id))
        return True


def make_manager():
    return RoomManager(DummyConfig())


def test_start_stop_recording_uses_recorder_manager_contract(monkeypatch):
    manager = make_manager()
    manager.add_room("douyin", "1001", "anchor-1", True)

    recorder = FakeRecorder()
    manager.set_recorder(recorder)

    monkeypatch.setattr(manager.parser, "get_stream_url", lambda platform, room_id: "http://example.com/live")

    assert manager.start_recording("douyin", "1001") is True
    assert recorder.start_calls == [("douyin", "1001", "http://example.com/live", "anchor-1")]

    room = manager.get_room("douyin", "1001")
    assert room is not None
    assert room.is_recording is True

    assert manager.stop_recording("douyin", "1001") is True
    assert recorder.stop_calls == [("douyin", "1001")]
    assert room.is_recording is False


def test_monitor_status_edge_triggers_once(monkeypatch):
    manager = make_manager()
    manager.add_room("douyin", "1002", "anchor-2", True)
    room = manager.get_room("douyin", "1002")

    events = []

    def fake_start(platform, room_id):
        events.append(("start", platform, room_id))
        room.is_recording = True
        return True

    def fake_stop(platform, room_id):
        events.append(("stop", platform, room_id))
        room.is_recording = False
        return True

    monkeypatch.setattr(manager, "start_recording", fake_start)
    monkeypatch.setattr(manager, "stop_recording", fake_stop)

    manager._handle_room_status(room, {"is_live": False, "title": "t0", "streamer_name": "s"})
    manager._handle_room_status(room, {"is_live": True, "title": "t1", "streamer_name": "s"})
    manager._handle_room_status(room, {"is_live": True, "title": "t2", "streamer_name": "s"})
    manager._handle_room_status(room, {"is_live": False, "title": "t3", "streamer_name": "s"})

    assert events == [
        ("start", "douyin", "1002"),
        ("stop", "douyin", "1002"),
    ]


def test_auto_record_false_does_not_start_on_live(monkeypatch):
    manager = make_manager()
    manager.add_room("douyin", "1003", "anchor-3", False)
    room = manager.get_room("douyin", "1003")

    calls = []

    def fake_start(platform, room_id):
        calls.append((platform, room_id))
        return True

    monkeypatch.setattr(manager, "start_recording", fake_start)

    manager._handle_room_status(room, {"is_live": True, "title": "live", "streamer_name": "s"})
    assert calls == []


def test_monitor_once_runs_in_parallel(monkeypatch):
    manager = make_manager()
    manager.monitor_max_workers = 2
    manager.add_room("douyin", "2001", "a", True)
    manager.add_room("douyin", "2002", "b", True)

    def fake_fetch(platform, room_id):
        time.sleep(0.25)
        return {"is_live": False, "title": "", "streamer_name": ""}

    monkeypatch.setattr(manager, "_fetch_room_status", fake_fetch)

    started = time.perf_counter()
    manager._monitor_once(manager.get_all_rooms())
    elapsed = time.perf_counter() - started

    assert elapsed < 0.52


def test_monitor_stop_is_interruptible(monkeypatch):
    manager = make_manager()
    manager.monitor_interval_sec = 3

    monkeypatch.setattr(manager, "_monitor_once", lambda rooms: time.sleep(0.2))

    manager.start_monitor()
    time.sleep(0.05)

    started = time.perf_counter()
    manager.stop_monitor()
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0
