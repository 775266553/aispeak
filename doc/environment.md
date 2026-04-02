# 环境要求

## 运行环境

- Windows 10 / 11
- Python 3.10 或更高版本，建议 3.11+
- 建议使用独立虚拟环境或 Conda 环境

## 依赖包

核心依赖包括：

- `customtkinter`
- `bilibili-api`
- `aiohttp`
- `faster-whisper`
- `opencc-python-reimplemented`
- `torch`，如需 GPU 加速则安装对应 CUDA 版本

## 系统依赖

- `ffmpeg`：用于音频处理和转写流程
- 可访问哔哩哔哩网络接口
- 如需拉取视频字幕或音频，需配置有效的 B 站 Cookie

## 存储要求

- 建议保留足够磁盘空间用于音频缓存和转写结果
- 默认输出目录为 `videos/`

## 说明

- GUI 启动走 `start.bat`
- Web 启动走 `start_web.bat`
- 转写结果和中间文件会写入 `videos/` 下的相关目录