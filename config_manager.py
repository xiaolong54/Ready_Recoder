import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional


class ConfigManager:
    DEFAULT_CONFIG = {
        "version": "1.0",
        "log": {
            "level": "info",
            "console": True,
            "file": "logs/app.log"
        },
        "record": {
            "output_dir": "recordings",
            "filename_template": "{platform}/{room_id}/{year}/{month}/{day}/{title}_{time}",
            "format": "flv",
            "quality": "origin"
        },
        "api": {
            "host": "0.0.0.0",
            "port": 8080,
            "enable": True
        },
        "monitor": {
            "interval_sec": 60,
            "max_workers": 8,
            "request_timeout_sec": 10
        },
        "webhook": {
            "enable": False,
            "url": "",
            "events": ["live_start", "live_end", "download_complete"]
        },
        "danmaku": {
            "enable": False,
            "output_dir": "recordings/danmaku"
        },
        "rooms": []
    }

    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return self._merge_default(config)
            except Exception as e:
                print(f"[Config] 加载配置文件失败: {e}")

        os.makedirs(self.config_file.parent, exist_ok=True)
        self._save_config(self.DEFAULT_CONFIG)
        return self.DEFAULT_CONFIG.copy()

    def _merge_default(self, config: Dict) -> Dict:
        result = self.DEFAULT_CONFIG.copy()
        if config:
            self._deep_merge(result, config)
        return result

    def _deep_merge(self, base: Dict, update: Dict):
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _save_config(self, config: Dict):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save(self):
        self._save_config(self.config)

    def add_room(self, room: Dict):
        rooms = self.config.get("rooms", [])
        existing = [r for r in rooms if r.get("room_id") == room.get("room_id") and r.get("platform") == room.get("platform")]
        if not existing:
            rooms.append(room)
            self.config["rooms"] = rooms
            self.save()
            print(f"[Config] 添加房间: {room.get('platform')}/{room.get('room_id')}")
            return True
        return False

    def remove_room(self, platform: str, room_id: str):
        rooms = self.config.get("rooms", [])
        self.config["rooms"] = [r for r in rooms if not (r.get("platform") == platform and r.get("room_id") == room_id)]
        self.save()
        print(f"[Config] 删除房间: {platform}/{room_id}")

    def get_rooms(self) -> List[Dict]:
        return self.config.get("rooms", [])

    def update_room(self, platform: str, room_id: str, updates: Dict):
        rooms = self.config.get("rooms", [])
        for room in rooms:
            if room.get("platform") == platform and room.get("room_id") == room_id:
                room.update(updates)
                self.save()
                return True
        return False


if __name__ == "__main__":
    config = ConfigManager()
    print("配置加载成功")
    print(config.config)
