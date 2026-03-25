import json
import urllib.error
import urllib.request

from api_server import APIServer


class DummyRoomManager:
    def __init__(self):
        self.running = False
        self.recorder = None

    def get_room_list(self):
        return []

    def get_room(self, platform, room_id):
        return None

    def add_room(self, platform, room_id, name, auto_record):
        return True

    def remove_room(self, platform, room_id):
        return True

    def start_recording(self, platform, room_id):
        return True

    def stop_recording(self, platform, room_id):
        return True

    def start_monitor(self):
        self.running = True

    def stop_monitor(self):
        self.running = False

    def search_targets(self, platform, query, limit=20):
        if query == "none":
            return []
        return [
            {
                "platform": "douyin",
                "room_id": "1234",
                "nickname": "tester",
                "uid": "1234",
                "source": "name",
            }
        ]


def test_targets_search_endpoint_returns_candidates():
    server = APIServer("127.0.0.1", 0)
    manager = DummyRoomManager()
    server.start(manager)
    try:
        port = server.server.server_port
        url = f"http://127.0.0.1:{port}/api/targets/search?platform=douyin&q=test&limit=5"
        with urllib.request.urlopen(url, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        assert payload["code"] == 0
        assert payload["data"][0]["room_id"] == "1234"
    finally:
        server.stop()


def test_targets_search_endpoint_validates_query_param():
    server = APIServer("127.0.0.1", 0)
    manager = DummyRoomManager()
    server.start(manager)
    try:
        port = server.server.server_port
        url = f"http://127.0.0.1:{port}/api/targets/search?platform=douyin"
        try:
            urllib.request.urlopen(url, timeout=5)
            assert False, "Expected HTTPError"
        except urllib.error.HTTPError as exc:
            assert exc.code == 400
            payload = json.loads(exc.read().decode("utf-8"))
            assert payload["error"] == "Missing query parameter q"
    finally:
        server.stop()
