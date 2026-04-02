import re
import os
from pathlib import Path
from bilibili_api import user, Credential
from .config import get_cookie_paths
from .logging import get_logger

logger = get_logger(__name__)

def parse_cookie_string(cookie_str: str) -> dict:
    cookies = {}
    for line in cookie_str.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        for key in ['SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'BUVID3', 'buvid3']:
            pattern = rf'{key}=([^;]+)'
            match = re.search(pattern, line)
            if match:
                cookies[key] = match.group(1)
    return cookies

def format_cookies_to_netscape(cookies: dict, expiry: int = 1774861740) -> str:
    lines = ["# Netscape HTTP Cookie File"]
    for name, value in cookies.items():
        if name in ['SESSDATA', 'bili_jct', 'BUVID3', 'DedeUserID', 'DedeUserID__ckMd5']:
            domain = ".bilibili.com"
            flag = "TRUE" if name == "SESSDATA" or name == "DedeUserID" else "FALSE"
            path = "/"
            secure = "TRUE" if name == "SESSDATA" else "FALSE"
            exp = expiry if name == "SESSDATA" else "0"
            lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{exp}\t{name}\t{value}")
    return '\n'.join(lines)

def save_cookies(cookies: dict) -> bool:
    try:
        cookie_file = get_cookie_paths()
        cookie_file.parent.mkdir(parents=True, exist_ok=True)
        netscape_str = format_cookies_to_netscape(cookies)
        with open(cookie_file, 'w', encoding='utf-8') as f:
            f.write(netscape_str)
        logger.info(f"Cookies saved to {cookie_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save cookies: {e}")
        return False

async def verify_cookie(cookies: dict = None) -> tuple:
    if cookies is None:
        cookies = load_cookies()

    if not cookies:
        return False, "Cookie文件不存在或为空"

    try:
        credential = Credential(
            sessdata=cookies.get('SESSDATA'),
            bili_jct=cookies.get('bili_jct'),
            buvid3=cookies.get('BUVID3')
        )
        u = user.User(uid=int(cookies.get('DedeUserID', 0)), credential=credential)
        user_info = await u.get_user_info()
        uname = user_info.get('card', {}).get('uname') or user_info.get('info', {}).get('uname', 'Unknown')
        return True, uname
    except Exception as e:
        logger.error(f"Cookie verification failed: {e}")
        return False, str(e)

def load_cookies() -> dict:
    cookie_file = get_cookie_paths()
    if not cookie_file.exists():
        return {}

    cookies = {}
    with open(cookie_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 7:
                name = parts[5]
                value = parts[6]
                cookies[name] = value
    return cookies

def get_credential() -> Credential:
    cookies = load_cookies()
    return Credential(
        sessdata=cookies.get('SESSDATA'),
        bili_jct=cookies.get('bili_jct'),
        buvid3=cookies.get('BUVID3')
    )
