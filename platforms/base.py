"""
平台解析器基类和接口定义
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from models import (
    PlatformType,
    RoomInfo,
    StreamInfo,
    StreamerInfo,
    LiveStatus,
    SearchResult
)


class IPlatformParser(ABC):
    """平台解析器接口"""
    
    @property
    @abstractmethod
    def platform(self) -> PlatformType:
        """获取平台类型"""
        pass
    
    @property
    @abstractmethod
    def supported_domains(self) -> List[str]:
        """获取支持的平台域名列表"""
        pass
    
    @abstractmethod
    def parse_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        解析URL,提取房间ID
        
        Args:
            url: 直播间URL
            
        Returns:
            包含platform和room_id的字典,或None
        """
        pass
    
    @abstractmethod
    def get_room_info(self, room_id: str, timeout: int = 10) -> Optional[RoomInfo]:
        """
        获取直播间信息
        
        Args:
            room_id: 房间ID
            timeout: 请求超时时间(秒)
            
        Returns:
            RoomInfo对象,或None
        """
        pass
    
    @abstractmethod
    def get_stream_info(self, room_id: str, timeout: int = 10) -> Optional[StreamInfo]:
        """
        获取流媒体信息
        
        Args:
            room_id: 房间ID
            timeout: 请求超时时间(秒)
            
        Returns:
            StreamInfo对象,或None
        """
        pass
    
    @abstractmethod
    def search_streamer(self, keyword: str, limit: int = 20) -> List[SearchResult]:
        """
        搜索主播
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            SearchResult列表
        """
        pass
    
    @abstractmethod
    def get_streamer_info(self, uid: str, timeout: int = 10) -> Optional[StreamerInfo]:
        """
        获取主播信息
        
        Args:
            uid: 主播ID
            timeout: 请求超时时间(秒)
            
        Returns:
            StreamerInfo对象,或None
        """
        pass


class BasePlatformParser(IPlatformParser):
    """平台解析器基类,提供通用功能"""
    
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    
    def __init__(self):
        self._session = None
    
    @property
    @abstractmethod
    def platform(self) -> PlatformType:
        pass
    
    @property
    @abstractmethod
    def supported_domains(self) -> List[str]:
        pass
    
    @abstractmethod
    def parse_url(self, url: str) -> Optional[Dict[str, str]]:
        pass
    
    @abstractmethod
    def get_room_info(self, room_id: str, timeout: int = 10) -> Optional[RoomInfo]:
        pass
    
    @abstractmethod
    def get_stream_info(self, room_id: str, timeout: int = 10) -> Optional[StreamInfo]:
        pass
    
    def search_streamer(self, keyword: str, limit: int = 20) -> List[SearchResult]:
        """
        搜索主播(默认实现,子类可覆盖)
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            SearchResult列表
        """
        return []
    
    def get_streamer_info(self, uid: str, timeout: int = 10) -> Optional[StreamerInfo]:
        """
        获取主播信息(默认实现,子类可覆盖)
        
        Args:
            uid: 主播ID
            timeout: 请求超时时间(秒)
            
        Returns:
            StreamerInfo对象,或None
        """
        return None
    
    def _normalize_url(self, url: str) -> str:
        """标准化URL"""
        import urllib.parse
        
        url = url.strip()
        
        # 添加协议
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # 移除查询参数
        try:
            parsed = urllib.parse.urlparse(url)
            normalized = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                '',
                '',
                ''
            ))
            return normalized
        except Exception:
            return url
    
    def _is_supported_domain(self, url: str) -> bool:
        """检查是否是支持的域名"""
        return any(domain in url for domain in self.supported_domains)
    
    def _build_live_status(self, status_code: int) -> LiveStatus:
        """根据状态码构建LiveStatus枚举"""
        status_map = {
            1: LiveStatus.LIVE,
            2: LiveStatus.LIVE,
            0: LiveStatus.OFFLINE,
        }
        return status_map.get(status_code, LiveStatus.UNKNOWN)


if __name__ == "__main__":
    # 测试基类
    print("测试平台解析器基类:")
    print("=" * 60)
    
    # 创建测试解析器
    class TestParser(BasePlatformParser):
        @property
        def platform(self) -> PlatformType:
            return PlatformType.DOUYIN
        
        @property
        def supported_domains(self) -> List[str]:
            return ["test.com"]
        
        def parse_url(self, url: str) -> Optional[Dict[str, str]]:
            url = self._normalize_url(url)
            if "test.com" in url:
                return {"platform": "test", "room_id": "123456"}
            return None
        
        def get_room_info(self, room_id: str, timeout: int = 10) -> Optional[RoomInfo]:
            return None
        
        def get_stream_info(self, room_id: str, timeout: int = 10) -> Optional[StreamInfo]:
            return None
    
    parser = TestParser()
    print(f"平台类型: {parser.platform}")
    print(f"支持域名: {parser.supported_domains}")
    print(f"标准化URL: {parser._normalize_url('test.com/123')}")
    print(f"域名支持: {parser._is_supported_domain('https://test.com/123')}")
    print(f"状态转换: {parser._build_live_status(1)}")
