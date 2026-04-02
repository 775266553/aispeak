from pathlib import Path
import json
import os

import whisper


ROOT_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT_DIR / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

print("加载Whisper模型...")
model = whisper.load_model("base")

videos = [
    {
        "title": "韩国法国叙利亚，一个周末崩了仨，这个世界怎么了？",
        "mp3": VIDEOS_DIR / "韩国法国叙利亚，一个周末崩了仨，这个世界怎么了？.mp3"
    },
    {
        "title": "特朗普关税王八拳，打中国，打美元，国际贸易必然重塑",
        "mp3": VIDEOS_DIR / "特朗普关税王八拳，打中国，打美元，国际贸易必然重塑.mp3"
    }
]

for v in videos:
    if not os.path.exists(v["mp3"]):
        print(f"⏳ 等待音频文件: {v['title']}")
        continue

    print(f"\n{'='*50}")
    print(f"转录: {v['title']}")
    print(f"{'='*50}")

    result = model.transcribe(str(v["mp3"]), language="zh", task="transcribe")

    with open(VIDEOS_DIR / f'{v["title"]}_Whisper字幕.txt', 'w', encoding='utf-8') as f:
        f.write(result['text'])

    with open(VIDEOS_DIR / f'{v["title"]}_Whisper字幕_时间戳.txt', 'w', encoding='utf-8') as f:
        for seg in result['segments']:
            f.write(f"[{seg['start']:.2f} - {seg['end']:.2f}] {seg['text']}\n")

    print(f"✅ 完成！字数: {len(result['text'])}")

print("\n所有转录完成！")
