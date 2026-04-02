import asyncio
import json
import re
import os
import aiohttp
from pathlib import Path
from bilibili_api import video
from .cookie_manager import get_credential, load_cookies
from .config import config
from .logging import get_logger
from typing import Optional, Callable

try:
    from opencc import OpenCC
except Exception:  # pragma: no cover - optional dependency fallback
    OpenCC = None

logger = get_logger(__name__)

_opencc = OpenCC("t2s") if OpenCC else None


def _to_simplified(text: str) -> str:
    if not text or _opencc is None:
        return text
    return _opencc.convert(text)

MAX_RETRIES = 3
RETRY_DELAY = 2


def _safe_title(title: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', title).strip() or '未命名标题'

def extract_bvid(url_or_bvid: str) -> str:
    if 'bilibili.com' in url_or_bvid:
        match = re.search(r'BV[\w]+', url_or_bvid)
        if match:
            return match.group()
    if url_or_bvid.startswith('BV'):
        return url_or_bvid
    return url_or_bvid

async def get_video_info(bvid: str):
    credential = get_credential()
    v = video.Video(bvid=bvid, credential=credential)
    info = await v.get_info()

    from models import VideoInfo
    video_info = VideoInfo(
        bvid=bvid,
        title=info.get('title', '未知标题'),
        up主=info.get('owner', {}).get('name', '未知UP主'),
        duration=info.get('duration', 0),
        cover=info.get('pic') or info.get('cover'),
        is会员专属=info.get('teenagers', False),
        page_count=len(info.get('pages', [1]))
    )
    return video_info


async def download_ai_subtitle(
    bvid: str,
    output_dir: Path,
) -> Optional[str]:
    credential = get_credential()
    v = video.Video(bvid=bvid, credential=credential)
    info = await v.get_info()

    cid = info['pages'][0]['cid']
    title = info.get('title', '未知标题')
    safe_title = _safe_title(title)

    subtitle_data = await v.get_subtitle(cid=cid)
    subtitle_item = None
    for sub in subtitle_data.get('subtitles', []):
        if sub.get('lan') == 'ai-zh':
            subtitle_item = sub
            break

    if not subtitle_item:
        return None

    subtitle_url = subtitle_item.get('subtitle_url') or ''
    if subtitle_url.startswith('//'):
        subtitle_url = f'https:{subtitle_url}'
    elif subtitle_url.startswith('/'):
        subtitle_url = f'https://www.bilibili.com{subtitle_url}'

    if not subtitle_url:
        return None

    async with aiohttp.ClientSession() as session:
        async with session.get(subtitle_url) as resp:
            resp.raise_for_status()
            content = await resp.json()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_path = output_dir / f"{safe_title}_AI文稿_raw.json"
    txt_path = output_dir / f"{safe_title}_AI文稿.txt"

    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    lines = []
    for item in content.get('body', []):
        text = (item.get('content') or '').strip()
        if text:
            lines.append(_to_simplified(text))

    full_text = '\n'.join(lines).strip()
    if not full_text:
        return None

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(full_text)

    logger.info(f"AI subtitle saved: {txt_path}")
    return str(txt_path)

async def download_audio(
    bvid: str,
    output_dir: Path,
    progress_callback: Optional[Callable] = None
) -> str:
    credential = get_credential()
    v = video.Video(bvid=bvid, credential=credential)
    info = await v.get_info()

    cid = info['pages'][0]['cid']
    title = info['title']
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)

    audio_path = output_dir / f"{safe_title}.mp3"
    part_path = output_dir / f"{safe_title}.mp3.part"

    # 清理已存在的临时文件
    if part_path.exists():
        part_path.unlink()

    cookies = load_cookies()

    for attempt in range(MAX_RETRIES):
        try:
            stream_url = await v.get_download_url(page_index=0)
            playurl = stream_url.get('dash', {}).get('audio', [{}])
            if playurl:
                audio_url = playurl[0].get('baseUrl') or playurl[0].get('backupUrl', [''])[0]
            else:
                playurl = stream_url.get('durl', [{}])
                audio_url = playurl[0].get('url', '')

            if not audio_url:
                raise Exception("无法获取音频地址")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com',
                'Cookie': f"SESSDATA={cookies.get('SESSDATA', '')}"
            }

            total_size = playurl[0].get('size', 0) if playurl else 0
            downloaded = 0

            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url, headers=headers) as resp:
                    resp.raise_for_status()
                    with open(part_path, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                speed = len(chunk) / 1024
                                progress_callback(progress, f"{speed:.1f}KB/s")

            if part_path.exists():
                if audio_path.exists():
                    audio_path.unlink()
                part_path.rename(audio_path)

            logger.info(f"Download complete: {audio_path}")
            return str(audio_path)

        except Exception as e:
            logger.warning(f"Download attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                raise e

async def check_bilibili_subtitle(bvid: str) -> tuple:
    credential = get_credential()
    v = video.Video(bvid=bvid, credential=credential)
    info = await v.get_info()
    cid = info['pages'][0]['cid']

    try:
        subtitle_data = await v.get_subtitle(cid=cid)
        for sub in subtitle_data.get('subtitles', []):
            if sub['lan'] == 'ai-zh':
                return True, sub
        return False, None
    except Exception as e:
        logger.error(f"Failed to get subtitle: {e}")
        return False, None
