"""
应用程序核心类
整合所有服务,提供统一的接口
"""
from typing import Optional, List, Dict, Any
from config_manager import ConfigManager
from recorder_core import RecorderManager
from services import RoomService, SearchService, MonitorService
from models import SearchResult, MonitoredRoom, OperationResult


class LiveRecorderApp:
    """直播录制应用程序核心"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        初始化应用程序
        
        Args:
            config_file: 配置文件路径
        """
        # 初始化配置
        self.config = ConfigManager(config_file)
        
        # 初始化录制器
        output_dir = self.config.get("record.output_dir", "recordings")
        self.recorder_manager = RecorderManager(output_dir)
        
        # 初始化服务
        self.room_service = RoomService(self.config)
        self.search_service = SearchService()
        
        # 配置房间服务的录制器
        self.room_service.set_recorder(self.recorder_manager)
        
        # 初始化监控服务
        monitor_interval = self.config.get("monitor.interval_sec", 60)
        monitor_max_workers = self.config.get("monitor.max_workers", 8)
        self.monitor_service = MonitorService(
            self.room_service,
            interval=monitor_interval,
            max_workers=monitor_max_workers
        )
        
        # API服务器(可选)
        self.api_server = None
    
    # ========== 房间管理 ==========
    
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
        return self.room_service.add_room(platform, room_id, name, auto_record)
    
    def add_room_by_url(
        self,
        url: str,
        name: str = "",
        auto_record: bool = True
    ) -> bool:
        """
        通过URL添加房间
        
        Args:
            url: 直播间URL
            name: 房间名称
            auto_record: 是否自动录制
            
        Returns:
            是否添加成功
        """
        from platforms import PlatformRegistry
        
        parsed = PlatformRegistry.parse_url(url)
        if not parsed:
            return False
        
        return self.add_room(
            parsed["platform"],
            parsed["room_id"],
            name,
            auto_record
        )
    
    def remove_room(self, platform: str, room_id: str) -> bool:
        """
        移除监控房间
        
        Args:
            platform: 平台名称
            room_id: 房间ID
            
        Returns:
            是否移除成功
        """
        return self.room_service.remove_room(platform, room_id)
    
    def get_rooms(self) -> List[Dict]:
        """获取所有房间"""
        return self.room_service.get_room_list()
    
    def get_room(self, platform: str, room_id: str) -> Optional[Dict]:
        """获取单个房间"""
        room = self.room_service.get_room(platform, room_id)
        return room.to_dict() if room else None
    
    def check_room_status(self, platform: str, room_id: str) -> Optional[Dict]:
        """
        检查房间状态
        
        Args:
            platform: 平台名称
            room_id: 房间ID
            
        Returns:
            房间状态字典
        """
        from platforms import PlatformRegistry
        
        room_info = PlatformRegistry.get_room_info(platform, room_id)
        return room_info.to_dict() if room_info else None
    
    # ========== 搜索功能 ==========
    
    def search_targets(
        self,
        platform: str,
        query: str,
        limit: int = 20
    ):
        """
        搜索目标直播间
        
        Args:
            platform: 平台名称
            query: 搜索内容
            limit: 返回结果数量限制
            
        Returns:
            搜索结果列表 (为了兼容GUI,直接返回字典列表)
        """
        from exceptions import (
            SearchNoResultError,
            SearchAPIError,
            PlatformNotFoundError,
            OperationResult,
            ExceptionHandler,
            ErrorContext
        )
        
        query = (query or "").strip()
        if not query:
            return OperationResult.failure_result(
                ExceptionHandler.create_error_context(
                    operation="search_targets",
                    platform=platform
                ),
                message="搜索内容不能为空"
            )
        
        try:
            results = self.search_service.search_targets(platform, query, limit)
            result_dicts = [result.to_dict() for result in results]
            
            if not result_dicts:
                return OperationResult.failure_result(
                    SearchNoResultError(platform or "unknown", query),
                    message=f"未找到相关结果: {query}"
                )
            
            return OperationResult.success_result(
                message=f"找到 {len(result_dicts)} 个结果",
                data=result_dicts
            )
        except Exception as e:
            return OperationResult.failure_result(
                SearchAPIError(platform or "unknown", query, str(e)),
                message="搜索失败,请稍后重试"
            )
    
    # ========== 录制控制 ==========
    
    def start_recording(self, platform: str, room_id: str) -> bool:
        """
        开始录制
        
        Args:
            platform: 平台名称
            room_id: 房间ID
            
        Returns:
            是否开始成功
        """
        return self.room_service.start_recording(platform, room_id)
    
    def stop_recording(self, platform: str, room_id: str) -> bool:
        """
        停止录制
        
        Args:
            platform: 平台名称
            room_id: 房间ID
            
        Returns:
            是否停止成功
        """
        return self.room_service.stop_recording(platform, room_id)
    
    def get_recorders_status(self) -> Dict:
        """获取录制器状态"""
        return self.recorder_manager.get_all_recorders_status()
    
    # ========== 监控控制 ==========
    
    def start_monitor(self) -> None:
        """启动监控"""
        self.monitor_service.start()
    
    def stop_monitor(self) -> None:
        """停止监控"""
        self.monitor_service.stop()
    
    @property
    def monitor_running(self) -> bool:
        """监控是否运行中"""
        return self.monitor_service.is_running
    
    # ========== API服务 ==========
    
    def start_api_server(self) -> None:
        """启动API服务器"""
        if not self.config.get("api.enable", True):
            return
        
        host = self.config.get("api.host", "0.0.0.0")
        port = self.config.get("api.port", 8080)
        
        from api_server import APIServer
        self.api_server = APIServer(host, port)
        self.api_server.start(self.room_service)
    
    def stop_api_server(self) -> None:
        """停止API服务器"""
        if self.api_server:
            self.api_server.stop()
    
    # ========== 统一控制 ==========
    
    def start_all(self) -> None:
        """启动所有服务"""
        self.start_api_server()
        self.start_monitor()
    
    def stop_all(self) -> None:
        """停止所有服务"""
        self.stop_monitor()
        self.stop_api_server()
        self.recorder_manager.stop_all()
    
    # ========== 支持的平台 ==========
    
    def get_supported_platforms(self) -> List[str]:
        """获取支持的平台列表"""
        from platforms import PlatformRegistry
        return PlatformRegistry.get_supported_platforms()


if __name__ == "__main__":
    # 测试应用程序核心
    print("应用程序核心测试:")
    print("=" * 60)
    
    app = LiveRecorderApp()
    
    print(f"支持的平台: {app.get_supported_platforms()}")
    print(f"房间数量: {len(app.get_rooms())}")
    print(f"监控状态: {'运行中' if app.monitor_running else '已停止'}")
    
    # 测试添加房间
    print("\n添加房间测试:")
    success = app.add_room("douyin", "123456", "测试房间")
    print(f"添加结果: {success}")
    
    # 测试URL添加
    print("\nURL添加测试:")
    success = app.add_room_by_url("https://live.douyin.com/789012", "URL测试")
    print(f"添加结果: {success}")
    
    # 测试搜索
    print("\n搜索测试:")
    results = app.search_targets("douyin", "测试", limit=5)
    print(f"找到 {len(results)} 个结果")
    
    # 测试获取房间
    print("\n获取房间测试:")
    rooms = app.get_rooms()
    print(f"房间数量: {len(rooms)}")
    
    print("\n测试完成!")
