from pathlib import Path
import json

import whisper


ROOT_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT_DIR / "videos"
INPUT_AUDIO_PATH = VIDEOS_DIR / "海湾陷落，全球断裂，美以伊战争后的世界会如何？.mp3"
VIDEO_TITLE = "海湾陷落，全球断裂，美以伊战争后的世界会如何？"

print("加载Whisper模型...")
model = whisper.load_model("base")

print("开始转录音频...")
result = model.transcribe(
    str(INPUT_AUDIO_PATH),
    language="zh",
    task="transcribe"
)

print(f"转录完成！")
print(f"总字数: {len(result['text'])}")
print(f"分段数: {len(result['segments'])}")

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

with open(VIDEOS_DIR / f'{VIDEO_TITLE}_Whisper字幕.txt', 'w', encoding='utf-8') as f:
    f.write(result['text'])

with open(VIDEOS_DIR / f'{VIDEO_TITLE}_Whisper字幕_时间戳.txt', 'w', encoding='utf-8') as f:
    for seg in result['segments']:
        start = seg['start']
        end = seg['end']
        text = seg['text']
        f.write(f"[{start:.2f} - {end:.2f}] {text}\n")

with open(VIDEOS_DIR / f'{VIDEO_TITLE}_transcript.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("转录结果已保存！")
