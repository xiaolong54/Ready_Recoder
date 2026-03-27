"""
B站平台解析器实现
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


class BilibiliParser(BasePlatformParser):
    """B站平台解析器"""
    
    @property
    def platform(self) -> PlatformType:
        return PlatformType.BILIBILI
    
    @property
    def supported_domains(self) -> List[str]:
        return ["bilibili.com", "live.bilibili.com"]
    
    def parse_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        解析B站URL
        
        Args:
            url: B站URL
            
        Returns:
            包含platform和room_id的字典,或None
        """
        try:
            url = self._normalize_url(url)
            
            patterns = [
                r'live\.bilibili\.com/(\d+)',
                r'bilibili\.com/(\d+)',
                r'live\.bilibili\.com/live/(\d+)',
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
            print(f"[BilibiliParser] URL解析失败: {exc}")
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
        url = f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}"
        headers = {
            **self.DEFAULT_HEADERS,
            "Referer": "https://live.bilibili.com/",
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            
            data = resp.json()
            if data.get("code") != 0:
                raise PlatformAPIError(
                    platform=self.platform.value,
                    endpoint=url,
                    message=data.get('message', 'API返回错误'),
                    status_code=data.get('code'),
                    response_data=data
                )
            
            room_data = data.get("data", {})
            
            # 构建主播信息
            streamer = StreamerInfo(
                uid=str(room_data.get("uid", room_id)),
                nickname=room_data.get("uname", ""),
                avatar=room_data.get("user_cover", ""),
            )
            
            # 构建房间信息
            room_info = RoomInfo(
                platform=self.platform,
                room_id=room_data.get("room_id", room_id),
                title=room_data.get("title", ""),
                streamer=streamer,
                live_status=self._build_live_status(room_data.get("live_status", 0)),
                cover=room_data.get("user_cover", ""),
                url=f"https://live.bilibili.com/{room_data.get('room_id', room_id)}",
            )
            
            return room_info
            
        except requests.exceptions.Timeout:
            print(f"[BilibiliParser] 请求超时: {room_id}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[BilibiliParser] 网络请求失败: {e}")
            return None
        except Exception as exc:
            print(f"[BilibiliParser] 获取房间信息失败: {exc}")
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
        url = f"https://api.live.bilibili.com/live/getH5PlayUrl?room_id={room_id}&quality=4&platform=web"
        headers = {
            **self.DEFAULT_HEADERS,
            "Referer": "https://live.bilibili.com/",
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            
            data = resp.json()
            if data.get("code") == 0:
                durl = data.get("data", {}).get("durl", [{}])[0]
                return StreamInfo(
                    platform=self.platform,
                    room_id=room_id,
                    stream_url=durl.get("url"),
                )
            
            raise PlatformAPIError(
                platform=self.platform.value,
                endpoint=url,
                message=data.get('message', 'API返回错误'),
                status_code=data.get('code'),
                response_data=data
            )
            
        except requests.exceptions.RequestException as exc:
            print(f"[BilibiliParser] 获取流信息失败: {exc}")
            return None
        except Exception as exc:
            print(f"[BilibiliParser] 获取流信息失败: {exc}")
            return None


if __name__ == "__main__":
    # 测试B站解析器
    parser = BilibiliParser()
    
    print("B站解析器测试:")
    print("=" * 60)
    
    # 测试URL解析
    test_urls = [
        "https://live.bilibili.com/123456",
        "live.bilibili.com/789012",
    ]
    
    print("\nURL解析测试:")
    for url in test_urls:
        result = parser.parse_url(url)
        print(f"  {url} -> {result}")
    
    print(f"\n平台类型: {parser.platform}")
    print(f"支持域名: {parser.supported_domains}")
