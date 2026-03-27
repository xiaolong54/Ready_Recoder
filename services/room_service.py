"""
房间管理服务
提供直播间管理的核心业务逻辑
"""
import threading
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import MonitoredRoom, PlatformType, RoomInfo, LiveStatus
from platforms import PlatformRegistry
from config_manager import ConfigManager
from exceptions import (
    RoomAlreadyExistsException,
    RoomNotFoundError,
    RoomOperationException,
    PlatformNotFoundError,
    ExceptionHandler
)


class RoomService:
    """房间管理服务"""
    
    def __init__(self, config: ConfigManager):
        """
        初始化房间服务
        
        Args:
            config: 配置管理器
        """
        self.config = config
        self.rooms: Dict[str, MonitoredRoom] = {}
        self.room_lock = threading.RLock()
        self.recorder = None
        
        self._load_rooms()
    
    def _load_rooms(self) -> None:
        """从配置文件加载房间"""
        rooms_data = self.config.get_rooms()
        with self.room_lock:
            for room_data in rooms_data:
                room = MonitoredRoom.from_dict(room_data)
                self.rooms[room.key] = room
                print(f"[RoomService] 加载房间: {room.key}")
    
    def add_room(
        self,
        platform: str,
        room_id: str,
        name: str = "",
        auto_record: bool = True
    ) -> bool:
        """
        添加监控房间
        
        Args:
            platform: 平台名称
            room_id: 房间ID
            name: 房间名称
            auto_record: 是否自动录制
            
        Returns:
            是否添加成功
        """
        try:
            platform_type = PlatformType(platform.lower())
        except ValueError:
            raise PlatformNotFoundError(platform)
        
        key = f"{platform_type.value}:{room_id}"
        
        with self.room_lock:
            if key in self.rooms:
                raise RoomAlreadyExistsException(platform, room_id)
            
            room = MonitoredRoom(
                platform=platform_type,
                room_id=room_id,
                name=name,
                auto_record=auto_record,
            )
            self.rooms[key] = room
        
        # 保存到配置
        self.config.add_room({
            "platform": platform,
            "room_id": room_id,
            "name": name,
            "auto_record": auto_record,
        })
        
        print(f"[RoomService] 添加房间: {key}")
        return True
    
    def remove_room(self, platform: str, room_id: str) -> bool:
        """
        移除监控房间
        
        Args:
            platform: 平台名称
            room_id: 房间ID
            
        Returns:
            是否移除成功
        """
        key = f"{platform.lower()}:{room_id}"
        
        with self.room_lock:
            room = self.rooms.get(key)
            if not room:
                raise RoomNotFoundError(platform, room_id)
            
            # 停止录制
            if room.is_recording:
                self.stop_recording(platform, room_id)
            
            del self.rooms[key]
        
        # 从配置移除
        self.config.remove_room(platform, room_id)
        
        print(f"[RoomService] 移除房间: {key}")
        return True
    
    def get_room(self, platform: str, room_id: str) -> Optional[MonitoredRoom]:
        """
        获取监控房间
        
        Args:
            platform: 平台名称
            room_id: 房间ID
            
        Returns:
            MonitoredRoom对象,或None
        """
        key = f"{platform.lower()}:{room_id}"
        with self.room_lock:
            return self.rooms.get(key)
    
    def get_all_rooms(self) -> List[MonitoredRoom]:
        """获取所有监控房间"""
        with self.room_lock:
            return list(self.rooms.values())
    
    def get_room_list(self) -> List[Dict]:
        """获取房间列表(字典格式)"""
        return [room.to_dict() for room in self.get_all_rooms()]
    
    def update_room_info(self, room: MonitoredRoom, room_info: RoomInfo) -> None:
        """
        更新房间信息
        
        Args:
            room: 监控房间对象
            room_info: 房间信息
        """
        room.room_info = room_info
        room.last_check_time = datetime.now()
    
    def check_room_status(self, platform: str, room_id: str, timeout: int = 10) -> Optional[RoomInfo]:
        """
        检查房间状态
        
        Args:
            platform: 平台名称
            room_id: 房间ID
            timeout: 请求超时时间(秒)
            
        Returns:
            RoomInfo对象,或None
        """
        room = self.get_room(platform, room_id)
        if not room:
            return None
        
        room_info = PlatformRegistry.get_room_info(platform, room_id, timeout=timeout)
        if room_info:
            self.update_room_info(room, room_info)
        
        return room_info
    
    def check_all_rooms_status(
        self,
        max_workers: int = 8,
        timeout: int = 10
    ) -> None:
        """
        检查所有房间状态(并发)
        
        Args:
            max_workers: 最大并发数
            timeout: 请求超时时间(秒)
        """
        rooms = self.get_all_rooms()
        if not rooms:
            return
        
        workers = max(1, min(max_workers, len(rooms)))
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    PlatformRegistry.get_room_info,
                    room.platform.value,
                    room.room_id,
                    timeout
                ): room
                for room in rooms
            }
            
            for future in as_completed(futures):
                room = futures[future]
                try:
                    room_info = future.result()
                    if room_info:
                        self.update_room_info(room, room_info)
                except Exception as e:
                    print(f"[RoomService] 检查房间状态失败 {room.key}: {e}")
    
    def start_recording(self, platform: str, room_id: str) -> bool:
        """
        开始录制
        
        Args:
            platform: 平台名称
            room_id: 房间ID
            
        Returns:
            是否开始成功
        """
        room = self.get_room(platform, room_id)
        if not room:
            print(f"[RoomService] 房间不存在: {platform}/{room_id}")
            return False
        
        if room.is_recording:
            print(f"[RoomService] 已在录制: {room.key}")
            return True
        
        if not self.recorder:
            print("[RoomService] 录制器未配置")
            return False
        
        # 获取流地址
        stream_info = PlatformRegistry.get_stream_info(platform, room_id)
        if not stream_info or not stream_info.stream_url:
            print(f"[RoomService] 获取流地址失败: {room.key}")
            return False
        
        # 开始录制
        streamer_name = room.streamer_name or room.name or f"{platform}_{room_id}"
        success = self.recorder.start_recording(
            platform,
            room_id,
            stream_info.stream_url,
            streamer_name
        )
        
        if success:
            room.is_recording = True
            print(f"[RoomService] 开始录制: {room.key}")
        else:
            print(f"[RoomService] 录制启动失败: {room.key}")
        
        return success
    
    def stop_recording(self, platform: str, room_id: str) -> bool:
        """
        停止录制
        
        Args:
            platform: 平台名称
            room_id: 房间ID
            
        Returns:
            是否停止成功
        """
        room = self.get_room(platform, room_id)
        if not room or not room.is_recording:
            return False
        
        if not self.recorder:
            print("[RoomService] 录制器未配置")
            return False
        
        success = self.recorder.stop_recording(platform, room_id)
        if success:
            room.is_recording = False
            print(f"[RoomService] 停止录制: {room.key}")
        
        return success
    
    def set_recorder(self, recorder) -> None:
        """
        设置录制器
        
        Args:
            recorder: 录制器对象,需要实现start_recording和stop_recording方法
        """
        required_methods = ("start_recording", "stop_recording")
        missing = [m for m in required_methods if not hasattr(recorder, m)]
        if missing:
            raise TypeError(
                f"录制器缺少必要方法: {', '.join(missing)}"
            )
        self.recorder = recorder


if __name__ == "__main__":
    # 测试房间服务
    from config_manager import ConfigManager
    
    config = ConfigManager()
    service = RoomService(config)
    
    print("房间服务测试:")
    print("=" * 60)
    
    # 测试添加房间
    print("\n添加房间测试:")
    service.add_room("douyin", "123456", "测试房间1")
    service.add_room("bilibili", "789012", "测试房间2")
    
    # 测试获取房间
    print("\n获取房间测试:")
    room = service.get_room("douyin", "123456")
    if room:
        print(f"  房间: {room.to_dict()}")
    
    # 测试获取所有房间
    print("\n所有房间:")
    for room in service.get_all_rooms():
        print(f"  {room.key} - {room.name}")
    
    # 测试移除房间
    print("\n移除房间测试:")
    service.remove_room("douyin", "123456")
    print(f"  剩余房间数量: {len(service.get_all_rooms())}")
