from pathlib import Path
import json

try:
    from opencc import OpenCC
except Exception:
    OpenCC = None


ROOT_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT_DIR / "videos"
TRANSCRIPT_PATH = VIDEOS_DIR / "whisper_transcript.json"
TIMESTAMP_PATH = VIDEOS_DIR / "完整字幕_时间戳.txt"
PLAIN_TEXT_PATH = VIDEOS_DIR / "完整字幕_纯文本.txt"

_opencc = OpenCC("t2s") if OpenCC else None


def _to_simplified(text: str) -> str:
    if not text or _opencc is None:
        return text
    return _opencc.convert(text)


def main() -> int:
    if not TRANSCRIPT_PATH.exists():
        raise FileNotFoundError(f"找不到字幕源文件: {TRANSCRIPT_PATH}")

    with open(TRANSCRIPT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    segments = data.get('segments', [])
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    with open(TIMESTAMP_PATH, 'w', encoding='utf-8') as f:
        for seg in segments:
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            text = _to_simplified(seg.get('text', ''))
            f.write(f"[{start:.2f} - {end:.2f}] {text}\n")

    with open(PLAIN_TEXT_PATH, 'w', encoding='utf-8') as f:
        for seg in segments:
            f.write(_to_simplified(seg.get('text', '')) + '\n')

    print(f"总段数: {len(segments)}")
    print("已保存到:")
    print(f"  - {TIMESTAMP_PATH.name}")
    print(f"  - {PLAIN_TEXT_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
