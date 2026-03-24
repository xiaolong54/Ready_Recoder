'''
Author: xiaolong
LastEditors: xiaolong
Date: 2026-03-24 15:32:08
LastEditTime: 2026-03-24 15:32:13
Email: 1525194049@qq.com
Description: 
'''
import json
from pathlib import Path
from datetime import datetime
from config import METADATA_FILE


class MetadataManager:
    def __init__(self):
        self.file_path = METADATA_FILE
        self.data = self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Metadata] 加载失败: {e}")
        return {"recordings": [], "streamers": []}

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Metadata] 保存失败: {e}")

    def add_recording(self, info):
        record = {
            "id": len(self.data["recordings"]) + 1,
            "type": info.get("type"),
            "filename": info.get("filename"),
            "streamer_name": info.get("streamer_name"),
            "streamer_sec_uid": info.get("streamer_sec_uid", ""),
            "record_time": info.get("record_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "start_time": info.get("start_time", ""),
            "end_time": info.get("end_time", ""),
            "duration_seconds": info.get("duration_seconds", 0),
            "file_size": info.get("file_size", 0),
            "source_url": info.get("source_url", ""),
            "tool": info.get("tool", ""),
        }
        self.data["recordings"].append(record)
        self._save()
        print(f"[Metadata] 添加录像记录: {record['filename']}")
        return record

    def add_streamer(self, info):
        streamer = {
            "uid": info.get("uid"),
            "sec_uid": info.get("sec_uid"),
            "nickname": info.get("nickname"),
            "avatar": info.get("avatar", ""),
            "added_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        existing = [s for s in self.data["streamers"] if s["sec_uid"] == streamer["sec_uid"]]
        if not existing:
            self.data["streamers"].append(streamer)
            self._save()
            print(f"[Metadata] 添加主播: {streamer['nickname']}")
        return streamer

    def get_recordings(self):
        return self.data.get("recordings", [])

    def get_streamers(self):
        return self.data.get("streamers", [])

    def delete_recording(self, record_id):
        self.data["recordings"] = [r for r in self.data["recordings"] if r["id"] != record_id]
        self._save()

    def clear_all(self):
        self.data = {"recordings": [], "streamers": []}
        self._save()
