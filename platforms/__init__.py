"""
平台解析器模块
提供插件化的平台解析支持
"""
from typing import Dict, Optional
from .base import IPlatformParser, BasePlatformParser
from .douyin import DouyinParser
from .bilibili import BilibiliParser
from .douyu import DouyuParser

__all__ = [
    "IPlatformParser",
    "BasePlatformParser",
    "DouyinParser",
    "BilibiliParser",
    "DouyuParser",
]


class PlatformRegistry:
    """平台注册中心"""
    
    _parsers: Dict[str, IPlatformParser] = {}
    
    @classmethod
    def register(cls, parser: IPlatformParser) -> None:
        """注册平台解析器"""
        platform_name = parser.platform.value
        cls._parsers[platform_name] = parser
        print(f"[PlatformRegistry] 注册平台解析器: {platform_name}")
    
    @classmethod
    def get(cls, platform: str) -> Optional[IPlatformParser]:
        """获取平台解析器"""
        return cls._parsers.get(platform.lower())
    
    @classmethod
    def get_all(cls) -> Dict[str, IPlatformParser]:
        """获取所有平台解析器"""
        return cls._parsers.copy()
    
    @classmethod
    def get_supported_platforms(cls) -> list[str]:
        """获取支持的平台列表"""
        return list(cls._parsers.keys())
    
    @classmethod
    def parse_url(cls, url: str) -> Optional[Dict[str, str]]:
        """
        使用所有平台解析器解析URL
        
        Args:
            url: 直播间URL
            
        Returns:
            包含platform和room_id的字典,或None
        """
        # 先检查域名
        for parser in cls._parsers.values():
            if parser._is_supported_domain(url):
                return parser.parse_url(url)
        
        # 尝试所有解析器
        for parser in cls._parsers.values():
            result = parser.parse_url(url)
            if result:
                return result
        
        return None
    
    @classmethod
    def get_room_info(cls, platform: str, room_id: str, timeout: int = 10):
        """获取房间信息"""
        parser = cls.get(platform)
        if parser:
            return parser.get_room_info(room_id, timeout=timeout)
        return None
    
    @classmethod
    def get_stream_info(cls, platform: str, room_id: str, timeout: int = 10):
        """获取流信息"""
        parser = cls.get(platform)
        if parser:
            return parser.get_stream_info(room_id, timeout=timeout)
        return None
    
    @classmethod
    def search_streamer(cls, platform: str, keyword: str, limit: int = 20):
        """搜索主播"""
        parser = cls.get(platform)
        if parser:
            return parser.search_streamer(keyword, limit=limit)
        return []


# 自动注册平台解析器
def _register_default_platforms():
    """注册默认平台解析器"""
    PlatformRegistry.register(DouyinParser())
    PlatformRegistry.register(BilibiliParser())
    PlatformRegistry.register(DouyuParser())
    # 可以在此添加其他平台解析器
    # PlatformRegistry.register(HuyaParser())
    # PlatformRegistry.register(KuaishouParser())


# 初始化时注册默认平台
_register_default_platforms()


if __name__ == "__main__":
    # 测试平台注册中心
    print("平台注册中心测试:")
    print("=" * 60)
    
    print(f"支持的平台: {PlatformRegistry.get_supported_platforms()}")
    
    # 测试URL解析
    test_urls = [
        "https://live.douyin.com/123456",
        "https://v.douyin.com/abc123",
        "https://live.bilibili.com/789012",
    ]
    
    print("\nURL解析测试:")
    for url in test_urls:
        result = PlatformRegistry.parse_url(url)
        print(f"  {url}")
        if result:
            print(f"    -> 平台: {result['platform']}, 房间ID: {result['room_id']}")
        else:
            print(f"    -> 无法解析")
