from pathlib import Path
import json

import whisper


ROOT_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT_DIR / "videos"
INPUT_AUDIO_PATH = VIDEOS_DIR / "伊朗战争，和全球能源格局.mp3"
TRANSCRIPT_JSON_PATH = VIDEOS_DIR / "whisper_transcript.json"
TRANSCRIPT_TEXT_PATH = VIDEOS_DIR / "whisper_text.txt"

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

with open(TRANSCRIPT_JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

with open(TRANSCRIPT_TEXT_PATH, 'w', encoding='utf-8') as f:
    f.write(result['text'])

print("转录结果已保存到 whisper_transcript.json 和 whisper_text.txt")
