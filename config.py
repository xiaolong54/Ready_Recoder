'''
Author: xiaolong
LastEditors: xiaolong
Date: 2026-03-24 15:31:12
LastEditTime: 2026-03-24 15:31:17
Email: 1525194049@qq.com
Description: 
'''
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
RECORDINGS_DIR = BASE_DIR / "recordings"
METADATA_FILE = RECORDINGS_DIR / "metadata.json"

RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": "https://www.douyin.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

Douyin_SEARCH_URL = "https://www.douyin.com/aweme/v1/web/search/item/"
Douyin_VIDEO_LIST_URL = "https://www.iesdouyin.com/aweme/v1/web/aweme/post/"
Douyin_LIVE_INFO_URL = "https://live.douyin.com/webcast/room/web/anchor_info/"
