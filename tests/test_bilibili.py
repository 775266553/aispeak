from __future__ import annotations

import asyncio
import json
from pathlib import Path

import aiohttp
from bilibili_api import Credential, video


ROOT_DIR = Path(__file__).resolve().parents[1]
VIDEOS_DIR = ROOT_DIR / "videos"

SESSDATA = "2a10e5f1%2C1788143404%2Ca06ca%2A32CjBtOOE7zXQPMvxfMGlwCX_vhqGkydiZ1kVS_Odcvz5EVr8_WoN-gmvrha_d9WMtG1MSVmZaOVVGdzVnQ3l1amNScFJXU2FERkgwRzFuTGdnTU9Xancwakt0eHp0TkxZUzhLZjFzanZ4ang3d2pSWU1kd1NteU0tRzZTdVllX3ZfRkpwdG1yRDBRIIEC"
BILI_JCT = "1adb2b2b8db4b697bc7e764e8e13e5a9"
BUVID3 = "5CE862AE-84A4-65DB-EADE-5C3965BC87BE33376infoc"


async def get_subtitle_content(bv_id: str) -> str | None:
    credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    v = video.Video(bvid=bv_id, credential=credential)
    info = await v.get_info()
    print(f"视频标题: {info['title']}")

    cid = info['pages'][0]['cid']
    subtitle_data = await v.get_subtitle(cid=cid)

    zh_subtitle = None
    for sub in subtitle_data['subtitles']:
        if sub['lan'] == 'ai-zh':
            zh_subtitle = sub
            break

    if not zh_subtitle:
        print("未找到中文字幕")
        return None

    subtitle_url = "https:" + zh_subtitle['subtitle_url']
    print(f"字幕URL: {subtitle_url}")

    async with aiohttp.ClientSession() as session:
        async with session.get(subtitle_url) as resp:
            content = await resp.json()

    print(f"字幕段数: {len(content.get('body', []))}")

    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = VIDEOS_DIR / 'subtitle_raw.json'
    text_path = VIDEOS_DIR / 'subtitle_text.txt'

    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    full_text = []
    for item in content.get('body', []):
        text = item.get('content', '')
        full_text.append(text)

    result = '\n'.join(full_text)
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"\n字幕已保存到 {text_path.name}")
    print(f"总字数: {len(result)}")
    return result


def main() -> int:
    asyncio.run(get_subtitle_content("BV1QGXABxEbq"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())