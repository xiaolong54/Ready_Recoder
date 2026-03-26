import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from api_client import DouyinAPIClient
from platform_parser import PlatformParser
from utils import format_follower_count, get_live_status_text


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
                    "follower_count": 0,
                    "is_live": None,
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
                    "follower_count": 0,
                    "is_live": None,
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
                        "follower_count": user.get("follower_count", 0) or 0,
                        "is_live": None,
                    }
                )
            
            # 异步查询开播状态
            self._enrich_with_live_status(candidates)
            
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

    def _enrich_with_live_status(self, candidates: List[Dict]) -> None:
        """
        异步查询候选列表的开播状态
        
        Args:
            candidates: 候选列表,会原地修改添加is_live字段
        """
        if not candidates:
            return
        
        def query_status(candidate: Dict) -> Dict:
            """查询单个候选的开播状态"""
            platform = candidate.get("platform")
            room_id = candidate.get("room_id")
            try:
                status = PlatformParser.get_live_status(platform, room_id, timeout_sec=5)
                return {"candidate": candidate, "is_live": status.get("is_live", False) if status else None}
            except Exception as e:
                print(f"[TargetResolver] Query live status failed for {platform}/{room_id}: {e}")
                return {"candidate": candidate, "is_live": None}
        
        # 使用线程池并发查询
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(query_status, candidate) for candidate in candidates]
            for future in as_completed(futures, timeout=10):
                try:
                    result = future.result()
                    if result:
                        candidate = result["candidate"]
                        candidate["is_live"] = result["is_live"]
                except Exception:
                    continue

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
