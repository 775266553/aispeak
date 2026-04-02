---
name: "video-content-extractor"
description: "Extracts text content from video websites (YouTube, Bilibili, etc.) and generates concise markdown summaries. Invoke when user provides video URLs and wants content extraction or summary generation."
---

# Video Content Extractor

This skill extracts textual content from video sharing platforms and generates refined markdown notes.

## Supported Platforms

- YouTube (via transcript/captions)
- Bilibili (via subtitles)
- Other video platforms with accessible text content

## Usage

Provide one or more video URLs, and the skill will:
1. Fetch the video page content
2. Extract available transcripts/subtitles
3. Generate a structured markdown summary

## Invocation

```
Extract content from: [video_url]
Generate summary from: [video_url]
Summarize this video: [video_url]
```

## Output

Generates a markdown file containing:
- Video title and metadata
- Key points and takeaways
- Timestamped sections (if available)
- Formatted notes in Chinese
