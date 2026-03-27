import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_core import LiveRecorderApp as AppCore


# 为了向后兼容,创建一个包装类
class LiveRecorderApp:
    """向后兼容的包装类"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self._app = AppCore(config_file)
    
    @property
    def room_manager(self):
        """为了向后兼容,提供room_manager属性"""
        return self._app.room_service
    
    def add_room_by_url(self, url: str, name: str = "", auto_record: bool = True) -> bool:
        """通过URL添加房间"""
        return self._app.add_room_by_url(url, name, auto_record)
    
    def add_room(self, platform: str, room_id: str, name: str = "", auto_record: bool = True) -> bool:
        """添加房间"""
        return self._app.add_room(platform, room_id, name, auto_record)
    
    def search_targets(self, platform: str, query: str, limit: int = 20):
        """搜索目标"""
        return self._app.search_targets(platform, query, limit)
    
    def add_room_by_query(self, platform: str, query: str, name: str = "", auto_record: bool = True):
        """通过查询添加房间"""
        results = self.search_targets(platform, query, limit=20)
        if results and len(results) > 0:
            candidate = results[0]
            return self.add_room(
                candidate.get("platform"),
                candidate.get("room_id"),
                name or candidate.get("nickname", ""),
                auto_record
            )
        return {"success": False, "reason": "no_candidates"}
    
    def remove_room(self, platform: str, room_id: str) -> bool:
        """移除房间"""
        return self._app.remove_room(platform, room_id)
    
    def start_recording(self, platform: str, room_id: str) -> bool:
        """开始录制"""
        return self._app.start_recording(platform, room_id)
    
    def stop_recording(self, platform: str, room_id: str) -> bool:
        """停止录制"""
        return self._app.stop_recording(platform, room_id)
    
    def get_rooms(self):
        """获取所有房间"""
        return self._app.get_rooms()
    
    def check_room_status(self, platform: str, room_id: str):
        """检查房间状态"""
        return self._app.check_room_status(platform, room_id)
    
    def start_monitor(self):
        """启动监控"""
        self._app.start_monitor()
    
    def stop_monitor(self):
        """停止监控"""
        self._app.stop_monitor()
    
    def start_api_server(self):
        """启动API服务器"""
        self._app.start_api_server()
    
    def stop_api_server(self):
        """停止API服务器"""
        self._app.stop_api_server()
    
    def get_recorders_status(self):
        """获取录制器状态"""
        return self._app.get_recorders_status()
    
    def stop_all(self):
        """停止所有服务"""
        self._app.stop_all()


def main():
    print("=" * 60)
    print("SocialMediaCut - Live Recorder")
    print("=" * 60)
    print()

    app = LiveRecorderApp()

    print("Supported platforms:", app._app.get_supported_platforms())
    print("Usage:")
    print("  1. GUI mode: python gui.py")
    print("  2. API service: built-in HTTP API")

    app.start_api_server()
    app.start_monitor()

    print("\nPress Ctrl+C to stop...")

    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
        app.stop_all()
        print("Stopped.")


if __name__ == "__main__":
    main()
