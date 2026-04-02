---
name: "bilibili-subtitle-extractor"
description: "Extracts complete subtitles from Bilibili videos. Uses BiliBili AI subtitles first, falls back to Whisper ASR if needed. Invoke when user provides Bilibili video URLs and wants full subtitle extraction."
---

# Bilibili Subtitle Extractor

Extracts complete subtitles from Bilibili videos using a two-stage fallback strategy.

## Directory Structure

```
output_dir/
├── videos/                    # 音频文件（默认）
│   └── 视频标题.mp3           # 从视频提取的音频
└── subtitles/                 # 字幕文件（自动创建）
    ├── 视频标题_b站字幕.txt   # B站AI字幕
    ├── 视频标题_raw.json      # 原始字幕JSON
    ├── 视频标题_Whisper字幕.txt    # Whisper转录
    └── 视频标题_Whisper字幕_时间戳.txt  # 带时间戳版本
```

## Workflow

```
Step 1: Try BiliBili AI Subtitles (via bilibili-api-python)
        ↓ (if fails or incomplete)
Step 2: Download audio only (mp3) → Whisper ASR transcription
```

## Prerequisites

### Required Python Packages

```bash
pip install bilibili-api-python aiohttp openai-whisper
```

### Required Files

1. **Cookies file** at `.trae/skills/bilibili-subtitle-extractor/cookies.txt`
   - Format: Netscape HTTP Cookie File
   - Required cookies: SESSDATA, bili_jct, BUVID3

## Usage

### Step 1: Configure Cookies

Edit `cookies.txt` with your Bilibili cookies:

```
# Netscape HTTP Cookie File
.bilibili.com	TRUE	/	TRUE	EXPIRY	SESSDATA	your_sessdata_value
.bilibili.com	TRUE	/	TRUE	0	bili_jct	your_bili_jct_value
.bilibili.com	TRUE	/	FALSE	0	BUVID3	your_buvid3_value
```

### Step 2: Run Extraction

```bash
python .trae/skills/bilibili-subtitle-extractor/bilibili_subtitle_extractor.py <BV号或URL> [输出目录]
```

**Examples:**

```bash
# By BV号
python bilibili_subtitle_extractor.py BV1QGXABxEbq

# By URL
python bilibili_subtitle_extractor.py https://www.bilibili.com/video/BV1QGXABxEbq/

# Specify output directory
python bilibili_subtitle_extractor.py BV1QGXABxEbq ./output_folder
```

### Step 3: Whisper Fallback (if B站 subtitles unavailable)

If B站 subtitles extraction fails, the script will prompt you to download audio and transcribe:

```bash
# 1. Download audio only (recommended - faster and uses less storage)
you-get --cookies .trae/skills/bilibili-subtitle-extractor/cookies.txt \
    --audio-only -o ./videos <video_url>

# 2. Or download video first, then extract audio
you-get --cookies .trae/skills/bilibili-subtitle-extractor/cookies.txt \
    -o ./videos <video_url>
ffmpeg -i ./videos/video.mp4 -vn -acodec mp3 -ab 192k ./videos/video.mp3

# 3. Run Whisper transcription
python -c "
import whisper
model = whisper.load_model('base')
result = model.transcribe('./videos/video.mp3', language='zh', task='transcribe')
with open('./subtitles/video_Whisper字幕.txt', 'w', encoding='utf-8') as f:
    f.write(result['text'])
"
```

## Output Files

All subtitle files are saved to `subtitles/` subdirectory:

| File Pattern | Source | Description |
|--------------|--------|-------------|
| `{视频标题}_b站字幕.txt` | B站 API | Complete Chinese subtitle text |
| `{视频标题}_raw.json` | B站 API | Original JSON with timestamps |
| `{视频标题}_Whisper字幕.txt` | Whisper ASR | Full transcription text |
| `{视频标题}_Whisper字幕_时间戳.txt` | Whisper ASR | Transcription with timestamps |

**Example output structure:**

```
./output/
├── videos/
│   └── 伊朗战争，和全球能源格局.mp3    # 音频文件
└── subtitles/
    ├── 伊朗战争，和全球能源格局_b站字幕.txt
    ├── 伊朗战争，和全球能源格局_raw.json
    ├── 伊朗战争，和全球能源格局_Whisper字幕.txt
    └── 伊朗战争，和全球能源格局_Whisper字幕_时间戳.txt
```

## File Naming Convention

- Automatically sanitizes illegal filename characters (`<>:"/\|?*`) to `_`
- Uses video title as prefix for all output files
- Subtitles are always saved to `subtitles/` subdirectory
- Audio files are saved to `videos/` subdirectory

## Invocation

```
Extract subtitles from: [bilibili_url]
Get video transcript: [bilibili_url]
下载这个视频的字幕: [bilibili_url]
```

## Tips

1. **Prefer B站 subtitles first** - Faster and usually accurate
2. **Use Whisper as fallback** - For videos without subtitles or incomplete captions
3. **Audio-only download** - Saves time and storage space
4. **Use "base" model for speed** - Use "large" model for better Chinese accuracy

## Error Handling

| Error | Solution |
|-------|----------|
| Credential Error | Update cookies.txt with fresh B站 credentials |
| Network Error | Check internet connection, try again |
| No B站 Subtitle | Use Whisper fallback workflow |
| Whisper Slow | Use smaller model or GPU for faster transcription |

## Technical Details

- **B站 API**: Uses `bilibili-api-python` with Credential authentication
- **Whisper Models**: base (fast), small, medium, large (accurate)
- **Audio Format**: MP3 192kbps for Whisper compatibility
- **Language**: Optimized for Chinese (zh) transcription
