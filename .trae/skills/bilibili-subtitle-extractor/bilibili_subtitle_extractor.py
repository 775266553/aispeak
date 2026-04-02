#!/usr/bin/env python3
"""
Bilibili Subtitle Extractor
Two-stage fallback: B站AI字幕 → Whisper ASR
"""

import asyncio
import json
import os
import re
import sys
import whisper

try:
    from bilibili_api import video, Credential
    import aiohttp
except ImportError:
    print("缺少依赖，请运行: pip install bilibili-api-python aiohttp openai-whisper")
    sys.exit(1)

def sanitize_filename(filename):
    illegal_chars = r'[<>:"/\\|?*]'
    return re.sub(illegal_chars, '_', filename)

def load_cookies(cookie_file=".trae/skills/bilibili-subtitle-extractor/cookies.txt"):
    if not os.path.exists(cookie_file):
        return None
    cookies = {}
    with open(cookie_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 7:
                name = parts[5]
                value = parts[6]
                if name in ['SESSDATA', 'bili_jct', 'BUVID3']:
                    cookies[name] = value
    return cookies

async def get_bilibili_subtitle(bv_id, output_dir=".", credentials=None):
    if not credentials:
        print("未提供B站凭证，跳过B站字幕...")
        return None, None

    try:
        credential = Credential(
            sessdata=credentials.get('SESSDATA'),
            bili_jct=credentials.get('BILI_JCT'),
            buvid3=credentials.get('BUVID3')
        )
        v = video.Video(bvid=bv_id, credential=credential)
        info = await v.get_info()

        video_title = sanitize_filename(info['title'])
        print(f"视频标题: {info['title']}")

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

            subtitle_dir = os.path.join(output_dir, "subtitles")
            os.makedirs(subtitle_dir, exist_ok=True)

            raw_path = f'{subtitle_dir}/{video_title}_raw.json'
            with open(raw_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)

            full_text = []
            for item in content.get('body', []):
                full_text.append(item.get('content', ''))

            result = '\n'.join(full_text)
            txt_path = f'{subtitle_dir}/{video_title}_b站字幕.txt'
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(result)

            print(f"✅ B站字幕获取成功！")
            print(f"  - 文件: subtitles/{video_title}_b站字幕.txt")
            print(f"  - 字数: {len(result)}")
            return result, video_title

        print("未找到中文字幕")
        return None, None

    except Exception as e:
        print(f"B站字幕获取失败: {e}")
        return None, None

def transcribe_with_whisper(audio_path, video_title, output_dir=".", model_name="base"):
    print(f"使用 Whisper ({model_name}) 转录音频...")

    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(audio_path, language="zh", task="transcribe")

        subtitle_dir = os.path.join(output_dir, "subtitles")
        os.makedirs(subtitle_dir, exist_ok=True)

        txt_path = f'{subtitle_dir}/{video_title}_Whisper字幕.txt'
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(result['text'])

        ts_path = f'{subtitle_dir}/{video_title}_Whisper字幕_时间戳.txt'
        with open(ts_path, 'w', encoding='utf-8') as f:
            for seg in result['segments']:
                f.write(f"[{seg['start']:.2f} - {seg['end']:.2f}] {seg['text']}\n")

        print(f"✅ Whisper转录完成！")
        print(f"  - 文件: subtitles/{video_title}_Whisper字幕.txt")
        print(f"  - 字数: {len(result['text'])}")
        return result['text']

    except Exception as e:
        print(f"Whisper转录失败: {e}")
        return None

async def main():
    if len(sys.argv) < 2:
        print("用法: python bilibili_subtitle_extractor.py <BV号或URL> [输出目录]")
        print("示例: python bilibili_subtitle_extractor.py BV1QGXABxEbq")
        print("示例: python bilibili_subtitle_extractor.py https://www.bilibili.com/video/BV1QGXABxEbq/ ./output")
        return

    url_or_bv = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    bv_id = url_or_bv
    if 'bilibili.com' in url_or_bv:
        match = re.search(r'BV[\w]+', url_or_bv)
        if match:
            bv_id = match.group()
        else:
            print("无法从URL提取BV号")
            return

    print(f"{'='*50}")
    print(f"开始提取字幕: {bv_id}")
    print(f"输出目录: {output_dir}")
    print(f"{'='*50}")

    cookies = load_cookies()
    if cookies:
        print("已加载B站凭证，尝试获取B站字幕...")

    subtitle, video_title = await get_bilibili_subtitle(bv_id, output_dir, cookies)

    if subtitle:
        print(f"\n✅ B站字幕提取完成！")
    else:
        print(f"\n❌ B站字幕不可用")
        print(f"提示: 请下载视频后使用 Whisper 转录")

if __name__ == "__main__":
    asyncio.run(main())
