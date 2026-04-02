---
name: oral-script-optimizer
description: Create or rewrite Chinese spoken scripts from articles, notes, reference scripts, or rough outlines. Use this skill whenever the user asks for 口播稿、演讲稿、视频文案、解说词、稿子润色、按时长生成稿件，or wants to borrow the strengths of excellent reference scripts without making the result look copied.
---

# Oral Script Optimizer

Turn source material into original, audience-friendly Chinese spoken scripts.

This skill is for situations where the user gives you one or more of the following:
- An article or long-form text
- Bullet-point notes or rough information
- One or more reference scripts they like
- A desired duration such as 3 minutes, 5 minutes, 8 minutes, or 10 minutes
- A tone request such as sharp, calm, story-like, analytical, emotional, or conversational

Your job is to preserve the useful properties of strong口播稿, then rewrite the content into a new script that sounds natural when spoken.

## Core principle

Use the reference material as a source of style and structure, not as text to copy.

Allowed:
- Near-synonym rewriting when it improves fluency
- Small amounts of shared paragraph order when the flow is genuinely useful
- Borrowing opening hooks, pacing patterns, contrast moves, and conclusion style
- Compressing or expanding sections to fit the requested duration
- Reorganizing examples, adding fresh examples, and changing the angle

Not allowed:
- Copying long phrases or consecutive sentences from the source
- Replacing only a few words while keeping the same sentence skeleton throughout
- Keeping the original logic too intact when the task asks for a new稿
- Producing text that would obviously be recognized as a lightly edited version of the source

When in doubt, make the piece feel more like a new script than a rewritten article.

## When to trigger

Use this skill when the user says things like:
- “帮我把这篇文章改成口播稿”
- “模仿这个稿子的节奏，写一篇新的”
- “给我一个 3 分钟版本 / 10 分钟版本”
- “参考这些优秀口播，生成一个更像视频文案的稿子”
- “润色一下，让它更适合说出来”
- “我给你材料，你帮我组织成适合播出的讲稿”

Also use it when the user provides excellent reference scripts and asks for a new script that borrows their strengths while staying original.

## Recommended workflow

1. Identify the user goal
   - Is the user asking for a rewrite, a summary, a stronger hook, or a complete new script?
   - Determine the target duration and audience.

2. Analyze the source material
   - Extract the core viewpoint, key facts, tension points, and emotional arc.
   - Identify what makes the reference scripts work:
     - opening hook
     - pacing
     - transition style
     - paragraph rhythm
     - contrast and suspense
     - ending payoff

3. Choose a rewriting strategy
   - If the source is already strong, preserve the overall flow but re-express it.
   - If the source is weak or scattered, rebuild the logic from scratch.
   - If the user wants only inspiration, keep the structure looser and more original.

4. Rebuild the script
   - Write for the ear, not the eye.
   - Prefer short-to-medium spoken sentences.
   - Put the key point early.
   - Use transitions that guide listeners forward.
   - Make every section earn its place.

5. Fit the target duration
   - 3 minutes: sharp opening, one main thread, fast turns, tight conclusion.
   - 5 minutes: clearer setup, 2–3 supporting points, moderate buildup.
   - 10 minutes: fuller background, layered analysis, richer examples, slower release of tension.

6. Sanity-check originality
   - Compare the draft against the source mentally.
   - Replace any phrase that still feels too close.
   - Change examples, sequencing, or framing if needed.

## Duration guide

Use these rough targets unless the user specifies otherwise:
- 3 minutes: about 450–700 Chinese characters, depending on speaking speed
- 5 minutes: about 800–1200 Chinese characters
- 10 minutes: about 1500–2200 Chinese characters

Adjust for tone and pacing. Faster, denser评论类口播 can be shorter in characters; narrative or explanatory scripts may need more.

## Output modes

Default to one polished script unless the user asks for variants.

If the user wants options, provide:
- Version A: more犀利 / 更抓人
- Version B: more稳重 / 更易播
- Version C: more故事感 / 更情绪化

## Output structure

When generating a script, use this structure unless the user asks otherwise:
1. Title
2. Hook or opening line
3. Main body in short spoken paragraphs
4. Transition lines between major ideas
5. Strong ending or closing takeaway

If useful, add a short note section after the script:
- Recommended speaking speed
- Places to pause or emphasize
- Optional cut points for video editing

## Quality checklist

Before finalizing, confirm the script:
- Sounds natural when read aloud
- Has a strong opening in the first 1–3 lines
- Maintains a clear thread without drifting
- Avoids obvious source copying
- Fits the requested duration
- Uses fresh wording and fresh examples where possible
- Preserves the value of the reference scripts without imitating them too closely

## How to respond to the user

If the user provides reference scripts, briefly tell them what you learned from the style before presenting the new稿.

A useful response pattern is:
- “我先提炼它们的节奏、钩子和推进方式，再给你一个新的原创版本。”
- “这个版本会保留它的口播感，但会换掉表达、例子和局部结构。”

## Examples of good requests

- “把这篇文章改成 3 分钟口播，偏犀利一点。”
- “参考这三篇优秀稿子，生成一个新的 10 分钟解说稿。”
- “这段内容太像论文了，帮我改成适合视频的说法。”
- “你可以借鉴这些稿子的节奏，但不要写得像洗稿。”

## Example prompts by duration

Use these as ready-made request patterns when the user is vague or when you want to suggest a clearer direction.

### 3-minute examples

- “把这篇材料改成 3 分钟短视频口播，开头要猛一点，节奏快，尽量每 20 到 30 秒有一个新的转折。”
- “参考这些优秀口播稿，给我写一个 3 分钟版本，重点是抓人、直接、不能拖。”
- “这篇文章帮我压缩成 3 分钟，适合抖音/视频号，要求一上来就有钩子。”

### 5-minute examples

- “把这组内容整理成 5 分钟口播稿，保留冲突感，但比 3 分钟更完整一点，别像洗稿。”
- “参考这些稿子的节奏，写一个 5 分钟版本，前面要强开场，中间多一个层次，最后收得干净。”
- “给我一个 5 分钟短视频稿，语气要自然，信息密度高一点，但不要太像文章。”

### 10-minute examples

- “把这些材料写成 10 分钟专题口播，层次清楚，案例更足，结尾要落到趋势判断。”
- “参考这几篇优秀稿子，生成一个 10 分钟解说稿，要求有背景、有分析、有结论。”
- “帮我做一个 10 分钟版本，适合长一点的视频，结构要完整，表达要像人说话。”

### 15-minute examples

- “给我一个 15 分钟深度口播，适合专题视频，前面先搭框架，中间多举例，最后要有完整总结。”
- “把这批信息扩成 15 分钟稿，要求层层展开、案例更多、结尾更完整。”
- “参考这些参考稿的风格，写一个 15 分钟版本，节奏不要太赶，但每一段都要有新信息。”

### 30-minute examples

- “把这些材料写成 30 分钟长稿，像深度解读视频，要求层层展开、案例更多、结尾更完整。”
- “给我一个 30 分钟的完整讲稿，适合做长视频，前中后结构都要稳，不能松散。”
- “参考这些优秀口播稿的结构感，生成一个 30 分钟版本，内容要足、逻辑要强、收束要完整。”

## Notes on originality

This skill should help the user borrow the strengths of优秀口播稿 responsibly.

Treat close paraphrase as a fallback only when the user explicitly wants a low-risk rewrite of factual material, and even then change the structure enough that the result still reads like a new script.

If the source text is itself very short or very generic, create a more original structure rather than staying close to it.
