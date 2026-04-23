import os
import json

CONFIG_DIR = os.path.join(os.environ.get('APPDATA', ''), 'Project_MiFan_Console')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

DEFAULT_CONFIG = {
    "fan_ip": "",
    "fan_token": "",
    "fan_model": "dmaker.fan.p5",
    "window_x": None,
    "window_y": None,
    "log_enabled": False
}

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(CONFIG_DIR):
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
            except Exception as e:
                print(f"Failed to create config directory: {e}")
                
        if not os.path.exists(CONFIG_FILE):
            self._save(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
            
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Merge with default backwards compatibility
                merged = DEFAULT_CONFIG.copy()
                merged.update(data)
                return merged
        except Exception as e:
            print(f"Failed to load config, using default: {e}")
            return DEFAULT_CONFIG.copy()

    def save_config(self):
        self._save(self.config)

    def _save(self, data):
        if not os.path.exists(CONFIG_DIR):
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
            except Exception:
                pass
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()
