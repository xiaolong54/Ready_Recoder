"""
监控服务
提供直播间自动监控功能
"""
import threading
import time
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.room_service import RoomService
from models import MonitoredRoom, LiveStatus


class MonitorService:
    """监控服务"""
    
    def __init__(self, room_service: RoomService, interval: int = 60, max_workers: int = 8):
        """
        初始化监控服务
        
        Args:
            room_service: 房间服务
            interval: 监控间隔(秒)
            max_workers: 最大并发数
        """
        self.room_service = room_service
        self.interval = interval
        self.max_workers = max_workers
        
        self.running = False
        self.stop_event = threading.Event()
        self.monitor_thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """启动监控"""
        if self.running:
            print("[MonitorService] 监控已在运行")
            return
        
        self.running = True
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("[MonitorService] 监控已启动")
    
    def stop(self) -> None:
        """停止监控"""
        self.running = False
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("[MonitorService] 监控已停止")
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        while self.running and not self.stop_event.is_set():
            self._check_all_rooms()
            
            # 等待下一个周期
            if self.stop_event.wait(self.interval):
                break
    
    def _check_all_rooms(self) -> None:
        """检查所有房间状态"""
        rooms = self.room_service.get_all_rooms()
        if not rooms:
            return
        
        workers = max(1, min(self.max_workers, len(rooms)))
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._check_room, room): room
                for room in rooms
            }
            
            for future in as_completed(futures):
                if self.stop_event.is_set():
                    break
                
                room = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"[MonitorService] 检查房间失败 {room.key}: {e}")
    
    def _check_room(self, room: MonitoredRoom) -> None:
        """
        检查单个房间状态
        
        Args:
            room: 监控房间对象
        """
        try:
            # 检查房间状态
            room_info = self.room_service.check_room_status(
                room.platform.value,
                room.room_id,
                timeout=10
            )
            
            if not room_info:
                return
            
            # 处理开播事件
            self._handle_live_status_change(room, room_info)
            
        except Exception as e:
            print(f"[MonitorService] 检查房间异常 {room.key}: {e}")
    
    def _handle_live_status_change(
        self,
        room: MonitoredRoom,
        room_info: any
    ) -> None:
        """
        处理直播状态变化
        
        Args:
            room: 监控房间对象
            room_info: 房间信息
        """
        was_live = room.is_live
        is_live = room_info.live_status == LiveStatus.LIVE
        
        # 开播
        if is_live and not was_live:
            print(f"[MonitorService] 开播: {room.key} - {room_info.streamer_name}")
            if room.auto_record and not room.is_recording:
                self.room_service.start_recording(room.platform.value, room.room_id)
        
        # 下播
        elif not is_live and was_live and room.is_recording:
            print(f"[MonitorService] 下播: {room.key}")
            self.room_service.stop_recording(room.platform.value, room.room_id)
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self.running


if __name__ == "__main__":
    # 测试监控服务
    from services.room_service import RoomService
    from config_manager import ConfigManager
    
    config = ConfigManager()
    room_service = RoomService(config)
    monitor_service = MonitorService(room_service, interval=10)
    
    print("监控服务测试:")
    print("=" * 60)
    
    # 添加测试房间
    room_service.add_room("douyin", "123456", "测试房间")
    
    print("\n启动监控...")
    monitor_service.start()
    
    try:
        # 运行30秒
        print("监控运行中,按Ctrl+C停止...")
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n收到停止信号")
    finally:
        monitor_service.stop()
        print("监控已停止")
