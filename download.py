'''
Author: xiaolong
LastEditors: xiaolong
Date: 2026-03-24 15:32:28
LastEditTime: 2026-03-24 15:32:32
Email: 1525194049@qq.com
Description: 
'''
import requests
import subprocess
import os
from pathlib import Path
from datetime import datetime
from config import RECORDINGS_DIR, HEADERS
from metadata import MetadataManager


class VideoDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.metadata = MetadataManager()

    def download_with_requests(self, url, filename, streamer_name, sec_uid):
        filepath = RECORDINGS_DIR / filename
        print(f"[Download] 开始下载: {url[:50]}...")

        try:
            resp = self.session.get(url, headers=HEADERS, stream=True, timeout=60)
            resp.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = filepath.stat().st_size
            self.metadata.add_recording({
                "type": "published",
                "filename": filename,
                "streamer_name": streamer_name,
                "streamer_sec_uid": sec_uid,
                "record_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "file_size": file_size,
                "source_url": url,
            })
            print(f"[Download] 下载完成: {filename} ({file_size} bytes)")
            return True
        except Exception as e:
            print(f"[Download] 下载失败: {e}")
            if filepath.exists():
                os.remove(filepath)
            return False

    def download_with_ytdlp(self, url, filename, streamer_name, sec_uid):
        filepath = RECORDINGS_DIR / filename
        print(f"[Download] 使用yt-dlp下载: {url[:50]}...")

        cmd = ["yt-dlp", "-o", str(filepath), url]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0 and filepath.exists():
                file_size = filepath.stat().st_size
                self.metadata.add_recording({
                    "type": "published",
                    "filename": filename,
                    "streamer_name": streamer_name,
                    "streamer_sec_uid": sec_uid,
                    "record_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "file_size": file_size,
                    "source_url": url,
                    "tool": "yt-dlp",
                })
                print(f"[Download] yt-dlp下载完成: {filename}")
                return True
            else:
                print(f"[Download] yt-dlp失败: {result.stderr}")
        except Exception as e:
            print(f"[Download] yt-dlp异常: {e}")
        return False

    def download(self, url, filename, streamer_name, sec_uid):
        if self._check_ytdlp():
            return self.download_with_ytdlp(url, filename, streamer_name, sec_uid)
        else:
            return self.download_with_requests(url, filename, streamer_name, sec_uid)

    def _check_ytdlp(self):
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
            return True
        except:
            return False


if __name__ == "__main__":
    downloader = VideoDownloader()
    print("VideoDownloader initialized")
