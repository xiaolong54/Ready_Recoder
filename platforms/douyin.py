"""
抖音平台解析器实现
"""
import re
import json
import urllib.parse
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


class DouyinParser(BasePlatformParser):
    """抖音平台解析器"""
    
    @property
    def platform(self) -> PlatformType:
        return PlatformType.DOUYIN
    
    @property
    def supported_domains(self) -> List[str]:
        return ["douyin.com", "live.douyin.com", "v.douyin.com", "webcast.amemv.com"]
    
    def parse_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        解析抖音URL
        
        Args:
            url: 抖音URL
            
        Returns:
            包含platform和room_id的字典,或None
        """
        try:
            url = self._normalize_url(url)
            
            # 标准URL模式
            patterns = [
                r'live\.douyin\.com/(\w+)',
                r'douyin\.com/user/(\w+)',
                r'iesdouyin\.com/share/user/(\w+)',
                r'webcast\.amemv\.com/douyin/webcast/reflow/(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return {
                        "platform": self.platform.value,
                        "room_id": match.group(1),
                        "url": url,
                    }
            
            # 短链接处理
            if 'v.douyin.com' in url:
                short_link_match = re.search(r'v\.douyin\.com/(\w+)', url)
                if short_link_match:
                    return {
                        "platform": self.platform.value,
                        "room_id": f"short:{short_link_match.group(1)}",
                        "url": url,
                        "is_short_link": True,
                    }
            
            return None
        except Exception as exc:
            print(f"[DouyinParser] URL解析失败: {exc}")
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
        url = f"https://live.douyin.com/webcast/room/web/anchor_info/?anchor_uid={room_id}"
        headers = {
            **self.DEFAULT_HEADERS,
            "Referer": "https://live.douyin.com/",
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            
            data = resp.json()
            if data.get("status_code") != 0:
                raise PlatformAPIError(
                    platform=self.platform.value,
                    endpoint=url,
                    message="API返回错误",
                    status_code=data.get('status_code'),
                    response_data=data
                )
            
            room_data = data.get("data", {}).get("room", {})
            anchor_data = data.get("data", {}).get("anchor", {})
            
            # 构建主播信息
            streamer = StreamerInfo(
                uid=anchor_data.get("uid", room_id),
                nickname=anchor_data.get("nickname", ""),
                avatar=anchor_data.get("avatar_url"),
            )
            
            # 构建房间信息
            room_info = RoomInfo(
                platform=self.platform,
                room_id=room_data.get("id", room_id),
                title=room_data.get("title", ""),
                streamer=streamer,
                live_status=self._build_live_status(room_data.get("status", 0)),
                cover=room_data.get("cover", {}).get("url_list", [None])[0],
                url=f"https://live.douyin.com/{room_data.get('id', room_id)}",
            )
            
            return room_info
            
        except requests.exceptions.Timeout:
            print(f"[DouyinParser] 请求超时: {room_id}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[DouyinParser] 网络请求失败: {e}")
            return None
        except Exception as exc:
            print(f"[DouyinParser] 获取房间信息失败: {exc}")
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
        url = f"https://live.douyin.com/{room_id}"
        headers = {
            **self.DEFAULT_HEADERS,
            "Referer": "https://live.douyin.com/",
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            
            html = resp.text
            
            # 尝试多种匹配模式
            patterns = [
                r'"play_url_json":"([^"]+)"',
                r'"main_play_url":"([^"]+)"',
                r'"play_addr":\{[^}]*"url_list":\s*\[[^\]]*"([^"]+)"',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    try:
                        url_info = json.loads(urllib.parse.unquote(match.group(1)))
                        stream_url = url_info.get("main_play_url") or url_info.get("url")
                        if stream_url:
                            return StreamInfo(
                                platform=self.platform,
                                room_id=room_id,
                                stream_url=stream_url,
                            )
                    except Exception:
                        continue
            
            print(f"[DouyinParser] 未找到流地址: {room_id}")
            return None
            
        except requests.exceptions.RequestException as exc:
            print(f"[DouyinParser] 获取流信息失败: {exc}")
            return None
        except Exception as exc:
            print(f"[DouyinParser] 获取流信息失败: {exc}")
            return None
    
    def search_streamer(self, keyword: str, limit: int = 20) -> List[SearchResult]:
        """
        搜索主播
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            SearchResult列表
        """
        from api_client import DouyinAPIClient
        
        client = DouyinAPIClient()
        users = client.search_user(keyword, limit=limit)
        
        if not users:
            raise SearchNoResultError(
                platform=self.platform.value,
                query=keyword
            )
        
        results = []
        for user in users:
            results.append(SearchResult(
                platform=self.platform,
                room_id=str(user.get("uid", "")),
                nickname=user.get("nickname", ""),
                follower_count=user.get("follower_count", 0),
                is_live=None,  # 需要单独查询
                source="name",
            ))
        
        return results
    
    def get_streamer_info(self, uid: str, timeout: int = 10) -> Optional[StreamerInfo]:
        """
        获取主播信息
        
        Args:
            uid: 主播ID
            timeout: 请求超时时间(秒)
            
        Returns:
            StreamerInfo对象,或None
        """
        # 抖音主播信息通常包含在直播间信息中
        room_info = self.get_room_info(uid, timeout=timeout)
        if room_info:
            return room_info.streamer
        return None
    
    def resolve_short_url(self, short_url: str, timeout: int = 10) -> Optional[str]:
        """
        解析短链接,获取真实房间ID
        
        Args:
            short_url: 短链接URL
            timeout: 超时时间(秒)
            
        Returns:
            真实房间ID,或None
        """
        try:
            headers = {
                'User-Agent': self.DEFAULT_HEADERS['User-Agent'],
            }
            
            # 使用HEAD请求获取重定向URL
            response = requests.head(short_url, headers=headers, allow_redirects=True, timeout=timeout)
            final_url = response.url
            print(f"[DouyinParser] 短链接重定向到: {final_url}")
            
            # 从最终URL提取房间ID
            patterns = [
                r'live\.douyin\.com/(\d+)',
                r'live\.douyin\.com/(\w+)',
                r'webcast\.amemv\.com/douyin/webcast/reflow/(\d+)',
                r'webcast\.amemv\.com.*reflow[/?]([^\&\s]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, final_url)
                if match:
                    room_id = match.group(1)
                    print(f"[DouyinParser] 从URL提取房间ID: {room_id}")
                    return room_id
            
            return None
            
        except requests.exceptions.Timeout:
            print(f"[DouyinParser] 解析短链接超时: {short_url}")
            return None
        except Exception as exc:
            print(f"[DouyinParser] 解析短链接失败: {exc}")
            return None


if __name__ == "__main__":
    # 测试抖音解析器
    parser = DouyinParser()
    
    print("抖音解析器测试:")
    print("=" * 60)
    
    # 测试URL解析
    test_urls = [
        "https://live.douyin.com/123456",
        "https://v.douyin.com/abc123",
        "live.douyin.com/789012",
    ]
    
    print("\nURL解析测试:")
    for url in test_urls:
        result = parser.parse_url(url)
        print(f"  {url} -> {result}")
    
    print(f"\n平台类型: {parser.platform}")
    print(f"支持域名: {parser.supported_domains}")
