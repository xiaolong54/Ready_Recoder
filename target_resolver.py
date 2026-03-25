import re
from typing import Dict, List, Optional

from api_client import DouyinAPIClient
from platform_parser import PlatformParser


class TargetResolver:
    def __init__(self, douyin_client: Optional[DouyinAPIClient] = None):
        self.douyin_client = douyin_client or DouyinAPIClient()

    def search_targets(self, platform: str, query: str, limit: int = 20) -> List[Dict]:
        query = (query or "").strip()
        platform = (platform or "").strip().lower()
        limit = max(1, min(50, int(limit or 20)))

        if not query:
            return []

        parsed = PlatformParser.parse_url(query)
        if parsed:
            return [
                {
                    "platform": parsed["platform"],
                    "room_id": str(parsed["room_id"]),
                    "nickname": "",
                    "uid": str(parsed["room_id"]),
                    "source": "url",
                }
            ]

        if self._is_id_query(platform, query):
            normalized_platform = platform or "douyin"
            return [
                {
                    "platform": normalized_platform,
                    "room_id": str(query),
                    "nickname": "",
                    "uid": str(query),
                    "source": "id",
                }
            ]

        if platform == "douyin":
            users = self.douyin_client.search_user(query, limit=limit)
            candidates: List[Dict] = []
            for user in users:
                uid = user.get("uid")
                if not uid:
                    continue
                candidates.append(
                    {
                        "platform": "douyin",
                        "room_id": str(uid),
                        "nickname": user.get("nickname", "") or "",
                        "uid": str(uid),
                        "source": "name",
                    }
                )
            return self._deduplicate(candidates, limit)

        return []

    def _is_id_query(self, platform: str, query: str) -> bool:
        if not platform:
            return query.isdigit()
        if platform in ("douyin", "bilibili"):
            return query.isdigit()
        if platform == "douyu":
            return re.match(r"^[A-Za-z0-9_]+$", query) is not None
        return False

    def _deduplicate(self, candidates: List[Dict], limit: int) -> List[Dict]:
        result: List[Dict] = []
        seen = set()
        for item in candidates:
            key = (item.get("platform"), item.get("room_id"))
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
            if len(result) >= limit:
                break
        return result
