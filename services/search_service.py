"""
搜索服务
提供直播间和主播搜索功能
"""
import re
import threading
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import SearchResult, PlatformType, LiveStatus
from platforms import PlatformRegistry
from url_utils import resolve_douyin_short_url


class SearchService:
    """搜索服务"""
    
    def __init__(self):
        """初始化搜索服务"""
        self.platform_registry = PlatformRegistry
    
    def search_targets(
        self,
        platform: str,
        query: str,
        limit: int = 20
    ) -> List[SearchResult]:
        """
        搜索目标直播间
        
        Args:
            platform: 平台名称
            query: 搜索内容(URL/ID/名称)
            limit: 返回结果数量限制
            
        Returns:
            SearchResult列表
        """
        query = (query or "").strip()
        platform = (platform or "").strip().lower()
        limit = max(1, min(50, int(limit or 20)))
        
        if not query:
            return []
        
        try:
            # 1. 尝试URL解析
            parsed = self.platform_registry.parse_url(query)
            if parsed:
                return [self._create_result_from_url(parsed)]
            
            # 2. 尝试ID查询
            if self._is_id_query(platform, query):
                return [self._create_result_from_id(platform or "douyin", query)]
            
            # 3. 尝试名称搜索
            if platform == "douyin":
                results = self.platform_registry.search_streamer(platform, query, limit=limit)
                # 异步查询开播状态
                self._enrich_with_live_status(results)
                # 去重
                return self._deduplicate(results, limit)
            
            # 其他平台暂不支持名称搜索
            return []
            
        except Exception as e:
            print(f"[SearchService] 搜索失败: {e}")
            return []
    
    def _create_result_from_url(self, parsed: dict) -> SearchResult:
        """从URL解析结果创建搜索结果"""
        platform = PlatformType(parsed["platform"])
        room_id = str(parsed["room_id"])
        
        # 检查是否是抖音短链接标记
        if room_id.startswith("short:") and parsed.get("is_short_link"):
            # 解析短链接获取真实房间ID
            short_url = parsed.get("url", "")
            if short_url:
                real_room_id = resolve_douyin_short_url(short_url)
                if real_room_id:
                    room_id = real_room_id
                    print(f"[SearchService] 抖音短链接解析成功: {short_url} -> {room_id}")
                else:
                    print(f"[SearchService] 抖音短链接解析失败: {short_url}")
        
        return SearchResult(
            platform=platform,
            room_id=room_id,
            nickname="",
            source="url",
        )
    
    def _create_result_from_id(self, platform: str, room_id: str) -> SearchResult:
        """从ID创建搜索结果"""
        return SearchResult(
            platform=PlatformType(platform),
            room_id=str(room_id),
            nickname="",
            source="id",
        )
    
    def _is_id_query(self, platform: str, query: str) -> bool:
        """判断是否是ID查询"""
        if not platform:
            return query.isdigit()
        
        if platform in ("douyin", "bilibili"):
            return query.isdigit()
        
        if platform == "douyu":
            return re.match(r"^[A-Za-z0-9_]+$", query) is not None
        
        return False
    
    def _enrich_with_live_status(self, results: List[SearchResult]) -> None:
        """
        异步查询搜索结果的开播状态
        
        Args:
            results: 搜索结果列表,会原地修改添加is_live字段
        """
        if not results:
            return
        
        def query_status(result: SearchResult):
            """查询单个结果的开播状态"""
            try:
                room_info = self.platform_registry.get_room_info(
                    result.platform.value,
                    result.room_id,
                    timeout=5
                )
                is_live = room_info.live_status == LiveStatus.LIVE if room_info else None
                return {"result": result, "is_live": is_live}
            except Exception as e:
                print(f"[SearchService] 查询开播状态失败 {result.platform.value}/{result.room_id}: {e}")
                return {"result": result, "is_live": None}
        
        # 使用线程池并发查询
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(query_status, result) for result in results]
            for future in as_completed(futures, timeout=10):
                try:
                    result_data = future.result()
                    if result_data:
                        result = result_data["result"]
                        result.is_live = result_data["is_live"]
                except Exception:
                    continue
    
    def _deduplicate(self, results: List[SearchResult], limit: int) -> List[SearchResult]:
        """去重并限制结果数量"""
        result_list: List[SearchResult] = []
        seen = set()
        
        for item in results:
            key = (item.platform.value, item.room_id)
            if key in seen:
                continue
            seen.add(key)
            result_list.append(item)
            if len(result_list) >= limit:
                break
        
        return result_list


if __name__ == "__main__":
    # 测试搜索服务
    service = SearchService()
    
    print("搜索服务测试:")
    print("=" * 60)
    
    # 测试URL搜索
    print("\nURL搜索测试:")
    test_urls = [
        "https://live.douyin.com/123456",
        "https://v.douyin.com/abc123",
        "https://live.bilibili.com/789012",
    ]
    
    for url in test_urls:
        results = service.search_targets("", url, limit=5)
        print(f"  {url}")
        for result in results:
            print(f"    -> {result.platform.value}/{result.room_id}")
    
    # 测试ID搜索
    print("\nID搜索测试:")
    results = service.search_targets("douyin", "123456", limit=5)
    for result in results:
        print(f"  {result.platform.value}/{result.room_id}")
    
    print("\n测试完成!")
