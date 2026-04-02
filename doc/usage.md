# 使用说明

## 1. 准备环境

1. 安装 Python 3.10+。
2. 安装项目依赖。
3. 确保 `ffmpeg` 可用。
4. 如需处理 B 站内容，准备好 Cookie。

## 2. 启动 GUI

直接运行根目录下的 `start.bat`，会启动桌面 GUI。

## 3. 启动 Web

直接运行根目录下的 `start_web.bat`，会启动 Web 页面并自动打开浏览器。

## 4. 运行测试脚本

测试脚本已移动到 `tests/` 目录下，可直接执行：

```bash
python tests/test_bilibili.py
```

## 5. 输出位置

- 转写结果默认保存在 `videos/`
- 临时音频和中间文件会放在 `videos/temp_audio/` 等子目录

## 6. 常见注意事项

- 如果提示 Cookie 未配置，需要先在 GUI 或 Web 中补充 Cookie。
- 如果转写失败，先检查 `ffmpeg`、Python 依赖和网络连通性。