import logging
import sys
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"

def setup_logging(log_level: str = "info"):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR
    }
    level = level_map.get(log_level.lower(), logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    return root_logger

def get_logger(name: str = __name__):
    return logging.getLogger(name)

class UserLog:
    def __init__(self):
        self._logs = []
        self._max_logs = 100

    def add(self, message: str, level: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "time": timestamp,
            "message": message,
            "level": level
        }
        self._logs.append(log_entry)
        if len(self._logs) > self._max_logs:
            self._logs.pop(0)

        log_methods = {
            "info": get_logger().info,
            "warning": get_logger().warning,
            "error": get_logger().error,
            "debug": get_logger().debug
        }
        log_func = log_methods.get(level, get_logger().info)
        log_func(message)

    def get_all(self):
        return self._logs.copy()

    def clear(self):
        self._logs.clear()

user_log = UserLog()
