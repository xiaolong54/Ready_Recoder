import requests
from datetime import datetime
from config import HEADERS, Douyin_SEARCH_URL, Douyin_VIDEO_LIST_URL, Douyin_LIVE_INFO_URL


class DouyinAPIClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def search_user(self, keyword, limit=20):
        print(f"[API] 搜索用户: {keyword}")
        params = {
            "keyword": keyword,
            "search_channel": "aweme_user_web",
            "enable_history": "1",
            "source": "normal_search",
            "aid": 6383,
            "count": limit,
        }
        try:
            resp = self.session.get(Douyin_SEARCH_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            users = []
            for item in data.get("data", []):
                user = item.get("user_info", {})
                if user and user.get("uid"):
                    users.append({
                        "uid": user.get("uid"),
                        "sec_uid": user.get("sec_uid"),
                        "nickname": user.get("nickname"),
                        "avatar": user.get("avatar_url"),
                        "following_count": user.get("following_count", 0),
                        "follower_count": user.get("follower_count", 0),
                    })
            print(f"[API] 搜索到 {len(users)} 个用户")
            return users
        except Exception as e:
            print(f"[API] 搜索失败: {e}")
            return []

    def get_user_videos(self, sec_uid, limit=20):
        print(f"[API] 获取用户视频列表: sec_uid={sec_uid}")
        params = {
            "sec_user_id": sec_uid,
            "count": limit,
            "max_cursor": 0,
            "aid": 6383,
            "cookie_enabled": True,
            "platform": "PC",
        }
        try:
            resp = self.session.get(Douyin_VIDEO_LIST_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            videos = []
            for item in data.get("aweme_list", []):
                video = item.get("video", {})
                if not video:
                    continue
                create_time = item.get("create_time", 0)
                videos.append({
                    "aweme_id": item.get("aweme_id"),
                    "title": item.get("desc", ""),
                    "create_time": datetime.fromtimestamp(create_time).strftime("%Y-%m-%d %H:%M:%S") if create_time else "",
                    "duration": video.get("duration", 0) // 1000,
                    "play_url": video.get("play_addr", {}).get("url_list", [None])[0],
                    "cover_url": video.get("cover", {}).get("url_list", [None])[0],
                })
            print(f"[API] 获取到 {len(videos)} 个视频")
            return videos
        except Exception as e:
            print(f"[API] 获取视频列表失败: {e}")
            return []

    def get_live_status(self, room_id):
        print(f"[API] 获取直播间状态: room_id={room_id}")
        url = f"{Douyin_LIVE_INFO_URL}?anchor_uid={room_id}"
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status_code") == 0:
                room = data.get("data", {}).get("room", {})
                anchor = data.get("data", {}).get("anchor", {})
                return {
                    "is_live": room.get("status") == 2,
                    "room_id": room.get("id"),
                    "title": room.get("title"),
                    "nickname": anchor.get("nickname"),
                    "room_url": f"https://live.douyin.com/{room.get('id')}",
                }
            return None
        except Exception as e:
            print(f"[API] 获取直播状态失败: {e}")
            return None


if __name__ == "__main__":
    client = DouyinAPIClient()
    users = client.search_user("测试")
    print(users)
