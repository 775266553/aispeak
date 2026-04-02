import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ROOT_DIR = BASE_DIR.parent.parent.parent
COOKIES_FILE = ROOT_DIR / "scripts" / "bilibili_cookies.txt"
OUTPUT_DIR = ROOT_DIR / "videos"
TEMP_AUDIO_DIR = OUTPUT_DIR / "temp_audio"
SUBTITLES_DIR = OUTPUT_DIR / "subtitles"
LOG_DIR = BASE_DIR / "logs"
SETTINGS_FILE = BASE_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "download_concurrency": 3,
    "output_dir": str(OUTPUT_DIR),
    "delete_audio_after_transcribe": False,
    "whisper_model": "base",
    "whisper_device": "auto",
    "output_format": "txt",
    "auto_open_dir": True,
    "log_level": "info"
}

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = None
        return cls._instance

    def load_settings(self) -> dict:
        if self._settings is None:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
            else:
                self._settings = DEFAULT_SETTINGS.copy()
        return self._settings

    def save_settings(self, settings: dict):
        self._settings = settings
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        settings = self.load_settings()
        return settings.get(key, DEFAULT_SETTINGS.get(key, default))

    @property
    def output_dir(self) -> Path:
        return Path(self.get("output_dir", str(OUTPUT_DIR)))

    @property
    def temp_audio_dir(self) -> Path:
        return self.output_dir / "temp_audio"

    @property
    def subtitles_dir(self) -> Path:
        return self.output_dir / "subtitles"

    @property
    def log_dir(self) -> Path:
        return LOG_DIR

def ensure_dirs():
    for d in [config.output_dir, config.temp_audio_dir, config.subtitles_dir, LOG_DIR]:
        os.makedirs(d, exist_ok=True)

def get_cookie_paths():
    return COOKIES_FILE

config = Config()
