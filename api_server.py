import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Callable, Dict
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
        else:
            self._send_error(404, "Not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except:
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
        platform = data.get("platform")
        room_id = data.get("room_id")
        name = data.get("name", "")
        auto_record = data.get("auto_record", True)

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
        if hasattr(self.room_manager, 'recorder') and self.room_manager.recorder:
            status = self.room_manager.recorder.get_all_recorders_status()
            self._send_json({"code": 0, "data": status})
        else:
            self._send_json({"code": 0, "data": []})

    def _handle_get_status(self):
        self._send_json({
            "code": 0,
            "data": {
                "monitor_running": self.room_manager.running,
                "room_count": len(self.room_manager.rooms),
                "recording_count": sum(1 for r in self.room_manager.rooms.values() if r.is_recording)
            }
        })

    def _handle_get_platforms(self):
        from platform_parser import PlatformParser
        platforms = PlatformParser.get_supported_platforms()
        self._send_json({"code": 0, "data": platforms})

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
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)

    def _send_error(self, code: int, message: str):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        error = json.dumps({"code": code, "error": message}, ensure_ascii=False).encode("utf-8")
        self.wfile.write(error)


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
        print(f"[APIServer] 启动成功 http://{self.host}:{self.port}")
        print(f"[APIServer] API端点:")
        print(f"  GET  /api/rooms          - 获取所有房间")
        print(f"  GET  /api/room/<p>/<id>   - 获取指定房间")
        print(f"  POST /api/rooms          - 添加房间")
        print(f"  DEL  /api/room/<p>/<id>  - 删除房间")
        print(f"  POST /api/room/start     - 开始录制")
        print(f"  POST /api/room/stop      - 停止录制")
        print(f"  GET  /api/recorders      - 获取录制器状态")
        print(f"  GET  /api/status         - 获取系统状态")
        print(f"  GET  /api/platforms      - 获取支持的平台")
        print(f"  POST /api/monitor/start  - 启动监控")
        print(f"  POST /api/monitor/stop   - 停止监控")

    def stop(self):
        if self.server:
            self.server.shutdown()
            print("[APIServer] 已停止")


if __name__ == "__main__":
    from config_manager import ConfigManager
    config = ConfigManager()
    server = APIServer()
    server.start(None)
    input("按Enter键停止服务器...\n")
    server.stop()
