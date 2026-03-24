import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager
from room_manager import RoomManager
from recorder_core import RecorderManager
from api_server import APIServer
from platform_parser import PlatformParser


class LiveRecorderApp:
    def __init__(self, config_file: str = "config.yaml"):
        self.config = ConfigManager(config_file)
        self.recorder_manager = RecorderManager(self.config.get("record.output_dir", "recordings"))
        self.room_manager = RoomManager(self.config)
        self.room_manager.set_recorder(self.recorder_manager)
        self.api_server = None

    def add_room_by_url(self, url: str, name: str = "", auto_record: bool = True) -> bool:
        result = PlatformParser.parse_url(url)
        if result:
            return self.room_manager.add_room(
                result["platform"],
                result["room_id"],
                name,
                auto_record
            )
        return False

    def add_room(self, platform: str, room_id: str, name: str = "", auto_record: bool = True) -> bool:
        return self.room_manager.add_room(platform, room_id, name, auto_record)

    def remove_room(self, platform: str, room_id: str) -> bool:
        return self.room_manager.remove_room(platform, room_id)

    def start_recording(self, platform: str, room_id: str) -> bool:
        return self.room_manager.start_recording(platform, room_id)

    def stop_recording(self, platform: str, room_id: str) -> bool:
        return self.room_manager.stop_recording(platform, room_id)

    def get_rooms(self):
        return self.room_manager.get_room_list()

    def check_room_status(self, platform: str, room_id: str):
        return self.room_manager.check_room_status(platform, room_id)

    def start_monitor(self):
        self.room_manager.start_monitor()

    def stop_monitor(self):
        self.room_manager.stop_monitor()

    def start_api_server(self):
        if self.config.get("api.enable", True):
            host = self.config.get("api.host", "0.0.0.0")
            port = self.config.get("api.port", 8080)
            self.api_server = APIServer(host, port)
            self.api_server.start(self.room_manager)

    def stop_api_server(self):
        if self.api_server:
            self.api_server.stop()

    def get_recorders_status(self):
        return self.recorder_manager.get_all_recorders_status()

    def stop_all(self):
        self.stop_monitor()
        self.stop_api_server()
        self.recorder_manager.stop_all()


def main():
    print("=" * 60)
    print("抖音直播录像工具 - 参考 bililive-go")
    print("=" * 60)
    print()

    app = LiveRecorderApp()

    print("支持的平台:", PlatformParser.get_supported_platforms())
    print()

    print("使用方法:")
    print("  1. GUI模式: python gui.py")
    print("  2. API服务: 程序内置HTTP API")
    print()

    app.start_api_server()
    app.start_monitor()

    print("\n按 Ctrl+C 停止服务...")

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        app.stop_all()
        print("服务已停止")


if __name__ == "__main__":
    main()
