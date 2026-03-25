import json
import re
import urllib.parse
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import requests


class BaseParser(ABC):
    @abstractmethod
    def parse_url(self, url: str) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def get_live_status(
        self, platform: str, room_id: str, timeout_sec: Optional[int] = None
    ) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def get_stream_url(self, platform: str, room_id: str) -> Optional[str]:
        raise NotImplementedError


class DouyinParser(BaseParser):
    DOMAINS = ["douyin.com", "live.douyin.com"]

    def parse_url(self, url: str) -> Optional[Dict]:
        room_id = self._extract_room_id(url)
        if room_id:
            return {"platform": "douyin", "room_id": room_id}
        return None

    def _extract_room_id(self, url: str) -> Optional[str]:
        patterns = [
            r"live\.douyin\.com/(\w+)",
            r"douyin\.com/(\w+)",
            r"v\.douyin\.com/(\w+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_live_status(
        self, platform: str, room_id: str, timeout_sec: Optional[int] = None
    ) -> Optional[Dict]:
        url = f"https://live.douyin.com/webcast/room/web/anchor_info/?anchor_uid={room_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://live.douyin.com/",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=timeout_sec or 10)
            data = resp.json()
            if data.get("status_code") == 0:
                room = data.get("data", {}).get("room", {})
                anchor = data.get("data", {}).get("anchor", {})
                return {
                    "is_live": room.get("status") == 2,
                    "room_id": room.get("id"),
                    "title": room.get("title"),
                    "streamer_name": anchor.get("nickname"),
                    "streamer_uid": anchor.get("uid"),
                    "cover": room.get("cover", {}).get("url_list", [None])[0],
                }
        except Exception as exc:
            print(f"[Douyin] Failed to get live status: {exc}")
        return None

    def get_stream_url(self, platform: str, room_id: str) -> Optional[str]:
        url = f"https://live.douyin.com/{room_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://live.douyin.com/",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            html = resp.text
            match = re.search(r'"play_url_json":"([^"]+)"', html)
            if match:
                url_info = json.loads(urllib.parse.unquote(match.group(1)))
                return url_info.get("main_play_url")
        except Exception as exc:
            print(f"[Douyin] Failed to get stream URL: {exc}")
        return None


class BilibiliParser(BaseParser):
    DOMAINS = ["bilibili.com", "live.bilibili.com"]

    def parse_url(self, url: str) -> Optional[Dict]:
        room_id = self._extract_room_id(url)
        if room_id:
            return {"platform": "bilibili", "room_id": room_id}
        return None

    def _extract_room_id(self, url: str) -> Optional[str]:
        patterns = [
            r"live\.bilibili\.com/(\d+)",
            r"bilibili\.com/(\d+)",
            r"live\.bilibili\.com/live/(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_live_status(
        self, platform: str, room_id: str, timeout_sec: Optional[int] = None
    ) -> Optional[Dict]:
        url = f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = requests.get(url, headers=headers, timeout=timeout_sec or 10)
            data = resp.json()
            if data.get("code") == 0:
                room = data.get("data", {})
                return {
                    "is_live": room.get("live_status") == 1,
                    "room_id": room.get("room_id"),
                    "title": room.get("title"),
                    "streamer_name": room.get("uname", ""),
                    "cover": room.get("user_cover", ""),
                }
        except Exception as exc:
            print(f"[Bilibili] Failed to get live status: {exc}")
        return None

    def get_stream_url(self, platform: str, room_id: str) -> Optional[str]:
        url = f"https://api.live.bilibili.com/live/getH5PlayUrl?room_id={room_id}&quality=4&platform=web"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("durl", [{}])[0].get("url")
        except Exception as exc:
            print(f"[Bilibili] Failed to get stream URL: {exc}")
        return None


class DouyuParser(BaseParser):
    DOMAINS = ["douyu.com", "live.douyu.com"]

    def parse_url(self, url: str) -> Optional[Dict]:
        room_id = self._extract_room_id(url)
        if room_id:
            return {"platform": "douyu", "room_id": room_id}
        return None

    def _extract_room_id(self, url: str) -> Optional[str]:
        patterns = [
            r"douyu\.com/(\w+)",
            r"live\.douyu\.com/(\w+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_live_status(
        self, platform: str, room_id: str, timeout_sec: Optional[int] = None
    ) -> Optional[Dict]:
        url = f"https://open.douyucdn.cn/api/RoomApi/room/{room_id}"
        try:
            resp = requests.get(url, timeout=timeout_sec or 10)
            data = resp.json()
            if not isinstance(data, dict):
                return None
            if data.get("error") == 0:
                room = data.get("data", {})
                return {
                    "is_live": room.get("room_status") == "1",
                    "room_id": room.get("room_id"),
                    "title": room.get("room_name"),
                    "streamer_name": room.get("nickname"),
                    "cover": room.get("room_thumb", ""),
                }
        except Exception as exc:
            print(f"[Douyu] Failed to get live status: {exc}")
        return None

    def get_stream_url(self, platform: str, room_id: str) -> Optional[str]:
        url = f"https://m.douyu.com/{room_id}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            html = resp.text
            match = re.search(r'"rtmp_url":"([^"]+)"', html)
            if match:
                rtmp_url = match.group(1)
                match2 = re.search(r'"rtmp_live":"([^"]+)"', html)
                if match2:
                    return f"{rtmp_url}/{match2.group(1)}"
        except Exception as exc:
            print(f"[Douyu] Failed to get stream URL: {exc}")
        return None


class PlatformParser:
    PARSERS = {
        "douyin": DouyinParser(),
        "bilibili": BilibiliParser(),
        "douyu": DouyuParser(),
    }

    @classmethod
    def parse_url(cls, url: str) -> Optional[Dict]:
        for parser in cls.PARSERS.values():
            result = parser.parse_url(url)
            if result:
                return result

        for parser in cls.PARSERS.values():
            for domain in parser.DOMAINS:
                if domain in url:
                    return parser.parse_url(url)

        return None

    @classmethod
    def get_live_status(
        cls, platform: str, room_id: str, timeout_sec: Optional[int] = None
    ) -> Optional[Dict]:
        parser = cls.PARSERS.get(platform)
        if parser:
            return parser.get_live_status(platform, room_id, timeout_sec=timeout_sec)
        return None

    @classmethod
    def get_stream_url(cls, platform: str, room_id: str) -> Optional[str]:
        parser = cls.PARSERS.get(platform)
        if parser:
            return parser.get_stream_url(platform, room_id)
        return None

    @classmethod
    def get_supported_platforms(cls) -> List[str]:
        return list(cls.PARSERS.keys())


if __name__ == "__main__":
    parser = PlatformParser()
    result = parser.parse_url("https://live.douyin.com/123456")
    print(f"Parse result: {result}")
    print(f"Supported platforms: {parser.get_supported_platforms()}")
