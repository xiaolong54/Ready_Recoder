"""
斗鱼平台解析器实现
"""
import re
import requests
from typing import Optional, Dict, List
from .base import BasePlatformParser
from models import (
    PlatformType,
    RoomInfo,
    StreamInfo,
    StreamerInfo,
    LiveStatus,
    SearchResult
)
from exceptions import (
    PlatformAPIError,
    SearchNoResultError,
    ErrorContext
)


class DouyuParser(BasePlatformParser):
    """斗鱼平台解析器"""
    
    @property
    def platform(self) -> PlatformType:
        return PlatformType.DOUYU
    
    @property
    def supported_domains(self) -> List[str]:
        return ["douyu.com", "live.douyu.com", "m.douyu.com"]
    
    def parse_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        解析斗鱼URL
        
        Args:
            url: 斗鱼URL
            
        Returns:
            包含platform和room_id的字典,或None
        """
        try:
            url = self._normalize_url(url)
            
            patterns = [
                r'douyu\.com/(\w+)',
                r'live\.douyu\.com/(\w+)',
                r'm\.douyu\.com/(\w+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return {
                        "platform": self.platform.value,
                        "room_id": match.group(1),
                        "url": url,
                    }
            
            return None
        except Exception as exc:
            print(f"[DouyuParser] URL解析失败: {exc}")
            return None
    
    def get_room_info(self, room_id: str, timeout: int = 10) -> Optional[RoomInfo]:
        """
        获取直播间信息
        
        Args:
            room_id: 房间ID
            timeout: 请求超时时间(秒)
            
        Returns:
            RoomInfo对象,或None
        """
        url = f"https://open.douyucdn.cn/api/RoomApi/room/{room_id}"
        headers = self.DEFAULT_HEADERS
        
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            
            data = resp.json()
            if not isinstance(data, dict):
                print(f"[DouyuParser] 无效的响应格式")
                return None
            
            if data.get("error") != 0:
                raise PlatformAPIError(
                    platform=self.platform.value,
                    endpoint=url,
                    message=data.get('msg', 'API返回错误'),
                    status_code=data.get('error'),
                    response_data=data
                )
            
            room_data = data.get("data", {})
            
            # 构建主播信息
            streamer = StreamerInfo(
                uid=room_id,
                nickname=room_data.get("nickname", ""),
                avatar=room_data.get("avatar", ""),
            )
            
            # 构建房间信息
            room_info = RoomInfo(
                platform=self.platform,
                room_id=room_data.get("room_id", room_id),
                title=room_data.get("room_name", ""),
                streamer=streamer,
                live_status=LiveStatus.LIVE if room_data.get("room_status") == "1" else LiveStatus.OFFLINE,
                cover=room_data.get("room_thumb", ""),
                url=f"https://www.douyu.com/{room_data.get('room_id', room_id)}",
            )
            
            return room_info
            
        except requests.exceptions.Timeout:
            print(f"[DouyuParser] 请求超时: {room_id}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[DouyuParser] 网络请求失败: {e}")
            return None
        except Exception as exc:
            print(f"[DouyuParser] 获取房间信息失败: {exc}")
            return None
    
    def get_stream_info(self, room_id: str, timeout: int = 10) -> Optional[StreamInfo]:
        """
        获取流媒体信息
        
        Args:
            room_id: 房间ID
            timeout: 请求超时时间(秒)
            
        Returns:
            StreamInfo对象,或None
        """
        url = f"https://m.douyu.com/{room_id}"
        headers = {
            **self.DEFAULT_HEADERS,
            "Referer": "https://www.douyu.com/",
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            
            html = resp.text
            
            # 尝试提取RTMP地址
            rtmp_url_match = re.search(r'"rtmp_url":"([^"]+)"', html)
            if rtmp_url_match:
                rtmp_url = rtmp_url_match.group(1)
                rtmp_live_match = re.search(r'"rtmp_live":"([^"]+)"', html)
                if rtmp_live_match:
                    stream_url = f"{rtmp_url}/{rtmp_live_match.group(1)}"
                    return StreamInfo(
                        platform=self.platform,
                        room_id=room_id,
                        stream_url=stream_url,
                    )
            
            print(f"[DouyuParser] 未找到流地址: {room_id}")
            return None
            
        except requests.exceptions.RequestException as exc:
            print(f"[DouyuParser] 获取流信息失败: {exc}")
            return None
        except Exception as exc:
            print(f"[DouyuParser] 获取流信息失败: {exc}")
            return None


if __name__ == "__main__":
    # 测试斗鱼解析器
    parser = DouyuParser()
    
    print("斗鱼解析器测试:")
    print("=" * 60)
    
    # 测试URL解析
    test_urls = [
        "https://www.douyu.com/123456",
        "https://m.douyu.com/abc123",
    ]
    
    print("\nURL解析测试:")
    for url in test_urls:
        result = parser.parse_url(url)
        print(f"  {url} -> {result}")
    
    print(f"\n平台类型: {parser.platform}")
    print(f"支持域名: {parser.supported_domains}")
