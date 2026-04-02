import asyncio
import json
import aiohttp
import os
from pathlib import Path

from bilibili_api import Credential, video


ROOT_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT_DIR / "videos"

SESSDATA = "2a10e5f1%2C1788143404%2Ca06ca%2A32CjBtOOE7zXQPMvxfMGlwCX_vhqGkydiZ1kVS_Odcvz5EVr8_WoN-gmvrha_d9WMtG1MSVmZaOVVGdzVnQ3l1amNScFJXU2FERkgwRzFuTGdnTU9Xancwakt0eHp0TkxZUzhLZjFzanZ4ang3d2pSWU1kd1NteU0tRzZTdVllX3ZfRkpwdG1yRDBRIIEC"
BILI_JCT = "1adb2b2b8db4b697bc7e764e8e13e5a9"
BUVID3 = "5CE862AE-84A4-65DB-EADE-5C3965BC87BE33376infoc"

def sanitize_filename(filename):
    import re
    illegal_chars = r'[<>:"/\\|?*]'
    return re.sub(illegal_chars, '_', filename)

async def get_subtitle(bv_id, output_dir=VIDEOS_DIR):
    credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    v = video.Video(bvid=bv_id, credential=credential)
    info = await v.get_info()

    video_title = sanitize_filename(info['title'])
    print(f"视频标题: {info['title']}")
    print(f"BV号: {bv_id}")

    cid = info['pages'][0]['cid']
    subtitle_data = await v.get_subtitle(cid=cid)

    zh_subtitle = None
    for sub in subtitle_data.get('subtitles', []):
        if sub['lan'] == 'ai-zh':
            zh_subtitle = sub
            break

    if zh_subtitle:
        subtitle_url = "https:" + zh_subtitle['subtitle_url']
        async with aiohttp.ClientSession() as session:
            async with session.get(subtitle_url) as resp:
                content = await resp.json()

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        raw_path = output_path / f'{video_title}_subtitle_raw.json'
        with open(raw_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

        full_text = []
        for item in content.get('body', []):
            full_text.append(item.get('content', ''))

        result = '\n'.join(full_text)
        txt_path = output_path / f'{video_title}_b站字幕.txt'
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(result)

        print(f"✅ B站字幕获取成功！")
        print(f"  - 文件: {video_title}_b站字幕.txt")
        print(f"  - 字数: {len(result)}")
        return True

    print("❌ 未找到B站字幕")
    return False

if __name__ == "__main__":
    import sys
    bv_id = sys.argv[1] if len(sys.argv) > 1 else "BV1244y1n7Mz"
    asyncio.run(get_subtitle(bv_id))
