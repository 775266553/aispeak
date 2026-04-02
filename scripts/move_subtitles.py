from pathlib import Path
import glob
import os
import shutil


ROOT_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT_DIR / "videos"
SUBTITLES_DIR = VIDEOS_DIR / "subtitles"

SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)

patterns = [
    "*_b站字幕.txt",
    "*_subtitle_raw.json",
    "*_Whisper字幕.txt",
    "*_Whisper字幕_时间戳.txt",
    "*_transcript.json",
    "*_精华笔记*.md",
    "whisper_*.txt",
    "whisper_*.json",
    "完整字幕_*.txt",
]

moved_count = 0
for pattern in patterns:
    files = glob.glob(str(VIDEOS_DIR / pattern))
    for file_path in files:
        source = Path(file_path)
        destination = SUBTITLES_DIR / source.name
        try:
            shutil.move(str(source), str(destination))
            print(f"✅ 移动: {source.name}")
            moved_count += 1
        except Exception as exc:
            print(f"❌ 移动失败: {source.name} - {exc}")

print(f"\n共移动 {moved_count} 个文件到 subtitles/ 目录")
