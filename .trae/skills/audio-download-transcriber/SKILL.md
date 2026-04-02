---
name: audio-download-transcriber
description: Download audio/mp3 from a Bilibili or video URL and transcribe it into text. Use this skill whenever the user asks to download mp3, extract audio, convert speech to text, generate a transcript, or process a video into a text file, especially when they mention Bilibili links or want the result saved as mp3 plus txt.
---

# Audio Download Transcriber

Turn a video or audio source into an mp3 file and a readable text transcript.

Use this skill when the user wants:
- to download mp3 from a Bilibili/video URL
- to convert spoken content into text
- to generate a transcript or subtitle-style text file
- to process audio first and then transcribe it

The preferred workflow is to use the existing Bilibili subtitle extractor program in this workspace, because it already handles audio download and transcription in one place.

## Core workflow

1. Identify the source
   - Confirm the user gave a Bilibili URL, BV号, or another supported video source.

2. Download the audio
   - Run the existing downloader workflow so the audio is saved as an mp3 file.
   - Keep the audio in the temp audio folder if the workflow is temporary, or move it to a user-specified output folder if they asked for permanent storage.

3. Transcribe the audio
   - Convert the mp3 into text.
   - If helpful, also produce a timestamped version so the user can review the transcript more easily.

4. Report the outputs clearly
   - Tell the user where the mp3 was saved.
   - Tell the user where the transcript was saved.
   - Mention whether a timestamped text file was also generated.

## Output expectations

Default output files:
- `mp3` audio file
- plain text transcript
- optional timestamped transcript

Typical save locations in this workspace:
- `videos/temp_audio/` for mp3 files
- `videos/subtitles/` for transcript text files

## When to trigger

Use this skill when the user says things like:
- “下载 mp3，然后转文本”
- “把这个视频转成文字”
- “帮我提取音频并生成文本稿”
- “做一个音频转写”
- “把 B 站视频下载成音频，然后转录”
- “我要 mp3 和 transcript”

Also use it when the user is clearly asking for speech-to-text processing even if they do not use those exact words.

## Practical guidance

- Prefer the audio-to-text workflow when the user specifically wants mp3 or a transcript.
- If the source is a Bilibili video and the platform subtitle is available, you may still mention it as an alternative, but do not lose sight of the mp3 + transcription path.
- Keep the result concise: the user usually wants the actual files, not a long explanation.

## Good response pattern

- “我先把音频下载成 mp3，再把它转成文本。”
- “如果你要的话，我还可以一起给你时间轴版本。”
- “我会把 mp3 和转写文本分别放到对应目录里，方便你直接用。”

## Quality checklist

Before finishing, confirm:
- the audio file exists
- the transcript text exists
- the save path is clear
- the user can find the output without extra steps
