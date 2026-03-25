import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict
from urllib.parse import parse_qs, urlparse

from room_manager import RoomManager


class APIHandler(BaseHTTPRequestHandler):
    room_manager: RoomManager = None

    def log_message(self, format, *args):
        print(f"[API] {args[0]}")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/rooms":
            self._handle_get_rooms()
        elif path.startswith("/api/room/"):
            parts = path.split("/")
            if len(parts) >= 5:
                platform, room_id = parts[3], parts[4]
                self._handle_get_room(platform, room_id)
            else:
                self._send_error(400, "Invalid path")
        elif path == "/api/recorders":
            self._handle_get_recorders()
        elif path == "/api/status":
            self._handle_get_status()
        elif path == "/api/platforms":
            self._handle_get_platforms()
        elif path == "/api/targets/search":
            self._handle_search_targets(query)
        else:
            self._send_error(404, "Not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if path == "/api/rooms":
            self._handle_add_room(data)
        elif path == "/api/room/start":
            self._handle_start_recording(data)
        elif path == "/api/room/stop":
            self._handle_stop_recording(data)
        elif path == "/api/monitor/start":
            self._handle_start_monitor()
        elif path == "/api/monitor/stop":
            self._handle_stop_monitor()
        else:
            self._send_error(404, "Not found")

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/room/"):
            parts = path.split("/")
            if len(parts) >= 5:
                platform, room_id = parts[3], parts[4]
                self._handle_delete_room(platform, room_id)
            else:
                self._send_error(400, "Invalid path")
        else:
            self._send_error(404, "Not found")

    def _handle_get_rooms(self):
        rooms = self.room_manager.get_room_list()
        self._send_json({"code": 0, "data": rooms})

    def _handle_get_room(self, platform: str, room_id: str):
        room = self.room_manager.get_room(platform, room_id)
        if room:
            self._send_json({"code": 0, "data": room.to_dict()})
        else:
            self._send_error(404, "Room not found")

    def _handle_add_room(self, data: dict):
        platform = (data.get("platform") or "").strip().lower()
        room_id = (data.get("room_id") or "").strip()
        name = data.get("name", "")
        auto_record = bool(data.get("auto_record", True))

        if not platform or not room_id:
            self._send_error(400, "Missing platform or room_id")
            return

        success = self.room_manager.add_room(platform, room_id, name, auto_record)
        if success:
            self._send_json({"code": 0, "message": "Room added"})
        else:
            self._send_error(400, "Room already exists or invalid")

    def _handle_delete_room(self, platform: str, room_id: str):
        success = self.room_manager.remove_room(platform, room_id)
        if success:
            self._send_json({"code": 0, "message": "Room deleted"})
        else:
            self._send_error(404, "Room not found")

    def _handle_start_recording(self, data: dict):
        platform = data.get("platform")
        room_id = data.get("room_id")

        if not platform or not room_id:
            self._send_error(400, "Missing platform or room_id")
            return

        success = self.room_manager.start_recording(platform, room_id)
        if success:
            self._send_json({"code": 0, "message": "Recording started"})
        else:
            self._send_error(500, "Failed to start recording")

    def _handle_stop_recording(self, data: dict):
        platform = data.get("platform")
        room_id = data.get("room_id")

        if not platform or not room_id:
            self._send_error(400, "Missing platform or room_id")
            return

        success = self.room_manager.stop_recording(platform, room_id)
        if success:
            self._send_json({"code": 0, "message": "Recording stopped"})
        else:
            self._send_error(500, "Failed to stop recording")

    def _handle_get_recorders(self):
        if hasattr(self.room_manager, "recorder") and self.room_manager.recorder:
            status = self.room_manager.recorder.get_all_recorders_status()
            self._send_json({"code": 0, "data": status})
        else:
            self._send_json({"code": 0, "data": []})

    def _handle_get_status(self):
        rooms = self.room_manager.get_room_list()
        self._send_json(
            {
                "code": 0,
                "data": {
                    "monitor_running": self.room_manager.running,
                    "room_count": len(rooms),
                    "recording_count": sum(1 for room in rooms if room.get("is_recording")),
                },
            }
        )

    def _handle_get_platforms(self):
        from platform_parser import PlatformParser

        platforms = PlatformParser.get_supported_platforms()
        self._send_json({"code": 0, "data": platforms})

    def _handle_search_targets(self, query: Dict):
        platform = (query.get("platform", ["douyin"])[0] or "douyin").strip().lower()
        q = (query.get("q", [""])[0] or "").strip()

        try:
            limit = int(query.get("limit", [20])[0])
        except Exception:
            self._send_error(400, "Invalid limit")
            return

        if not q:
            self._send_error(400, "Missing query parameter q")
            return

        if platform != "douyin":
            self._send_json({"code": 40002, "error": "Name search currently supports douyin only", "data": []})
            return

        candidates = self.room_manager.search_targets(platform, q, limit=limit)
        if not candidates:
            self._send_json({"code": 40401, "error": "No candidates found", "data": []})
            return

        self._send_json({"code": 0, "data": candidates})

    def _handle_start_monitor(self):
        self.room_manager.start_monitor()
        self._send_json({"code": 0, "message": "Monitor started"})

    def _handle_stop_monitor(self):
        self.room_manager.stop_monitor()
        self._send_json({"code": 0, "message": "Monitor stopped"})

    def _send_json(self, data: dict):
        response = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def _send_error(self, code: int, message: str):
        payload = json.dumps({"code": code, "error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class APIServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.server: HTTPServer = None
        self.thread: threading.Thread = None

    def start(self, room_manager: RoomManager):
        APIHandler.room_manager = room_manager

        self.server = HTTPServer((self.host, self.port), APIHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

        print(f"[APIServer] Started at http://{self.host}:{self.server.server_port}")
        print("[APIServer] Endpoints:")
        print("  GET  /api/rooms")
        print("  GET  /api/room/<platform>/<room_id>")
        print("  POST /api/rooms")
        print("  DEL  /api/room/<platform>/<room_id>")
        print("  POST /api/room/start")
        print("  POST /api/room/stop")
        print("  GET  /api/recorders")
        print("  GET  /api/status")
        print("  GET  /api/platforms")
        print("  GET  /api/targets/search?platform=douyin&q=<query>&limit=<n>")
        print("  POST /api/monitor/start")
        print("  POST /api/monitor/stop")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("[APIServer] Stopped")


if __name__ == "__main__":
    from config_manager import ConfigManager

    _ = ConfigManager()
    server = APIServer()
    server.start(None)
    input("Press Enter to stop server...\n")
    server.stop()
