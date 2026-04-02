# Bilibili 字幕提取工具

一个用于从 Bilibili 视频提取字幕的 GUI 工具，支持 B站 AI 字幕下载和 Whisper 语音转录。

## 功能特点

- ✅ **视频信息解析** - 自动获取视频标题、UP主、时长等信息
- ✅ **音频下载** - 支持并发下载（最多3个同时下载）
- ✅ **语音转录** - 使用 faster-whisper 进行高质量语音转文字
- ✅ **图形界面** - 基于 CustomTkinter 的现代化深色界面
- ✅ **任务管理** - 支持开始、停止、重试、清空等操作
- ✅ **实时进度** - 显示下载和转录的实时进度

## 系统要求

- Python 3.10+
- Windows 10/11
- 至少 4GB 内存
- 约 500MB 磁盘空间（用于存储模型文件）

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- `customtkinter` - GUI 框架
- `bilibili-api-python` - B站 API 接口
- `faster-whisper` - 语音转录引擎
- `aiohttp` - 异步 HTTP 客户端

### 2. 配置 Cookie

首次使用需要配置 Bilibili Cookie：

1. 登录 Bilibili 网站
2. 按 F12 打开开发者工具
3. 切换到 Network/网络 标签
4. 刷新页面，找到任意请求
5. 复制请求头中的 Cookie 字符串
6. 运行程序后点击 "🔑 更新Cookie" 按钮
7. 粘贴 Cookie 并保存

需要的 Cookie 字段：
- `SESSDATA`（必需）
- `bili_jct`
- `DedeUserID`
- `buvid3`

## 使用方法

### 启动程序

```bash
python main.py
```

或使用启动脚本：
```bash
start.bat
```

### 基本操作流程

1. **添加视频**
   - 在输入框中输入 BV号 或 视频链接
   - 点击 "➕ 添加" 按钮或按回车键
   - 视频信息会自动解析并显示在列表中

2. **开始处理**
   - 点击 "▶ 开始" 按钮
   - 程序会自动下载音频并转录为字幕

3. **查看进度**
   - 任务列表显示当前状态：
     - ⏳ 等待中
     - 📥 下载中（显示进度百分比）
     - 🎙️ 转录中（显示进度百分比）
     - ✅ 已完成
     - ❌ 失败
     - ⏹️ 已停止

4. **其他操作**
   - **停止全部**：点击 "⏹ 停止全部" 按钮
   - **重试失败**：点击 "🔄 重试失败" 按钮
   - **清空已完成**：点击 "🗑️ 清空" 按钮

### 输出文件

处理完成后，文件保存在以下位置：

```
videos/
├── temp_audio/          # 临时音频文件
│   └── 视频标题.mp3
└── subtitles/           # 字幕文件
   ├── 视频标题.txt
   └── 视频标题_时间戳.txt
```

## 设置选项

点击 "⚙️ 设置" 按钮可以配置：

### 下载设置
- **并发数**：同时下载的视频数量（1-5）
- **输出目录**：自定义输出文件夹路径
- **删除临时音频**：转录完成后是否删除音频文件

### 转录设置
- **模型**：Whisper 模型大小
  - `tiny` - 最快，准确度较低
  - `base` - 平衡（推荐）
  - `small` - 较慢，准确度较高
  - `medium`/`large` - 最慢，准确度最高
- **设备**：计算设备
  - `auto` - 自动检测（推荐）
  - `cpu` - 使用 CPU
  - `cuda` - 使用 GPU（需要 NVIDIA 显卡）
- **输出格式**：字幕文件格式（txt/srt/json）

### 界面设置
- **日志级别**：debug/info/warning/error
- **自动打开目录**：完成后是否自动打开字幕文件夹

## 常见问题

### Q: 首次运行转录很慢？
A: 首次使用 faster-whisper 需要下载模型文件（约 150MB），根据网络情况可能需要 2-5 分钟。下载完成后后续使用会快很多。

### Q: Cookie 验证失败？
A: 请确保：
1. Cookie 字符串包含 `SESSDATA`
2. Cookie 未过期（重新登录 B站获取新 Cookie）
3. 复制完整的 Cookie 字符串

### Q: 下载失败？
A: 可能原因：
1. Cookie 无效或过期
2. 视频需要会员权限
3. 网络连接问题
4. 视频已被删除或下架

### Q: 转录质量不佳？
A: 可以尝试：
1. 更换更大的 Whisper 模型（small/medium/large）
2. 确保音频质量良好
3. 对于方言或特殊口音可能识别率较低

### Q: 程序崩溃或报错？
A: 请检查：
1. 是否安装了所有依赖
2. Python 版本是否为 3.10+
3. 查看日志文件获取详细错误信息

## 文件说明

```
.
├── main.py                 # 程序入口
├── controller.py           # 业务逻辑控制器
├── ui.py                   # 图形界面
├── models.py               # 数据模型
├── services/               # 服务模块
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── cookie_manager.py  # Cookie 管理
│   ├── downloader.py      # 下载器
│   ├── transcriber.py     # 转录器
│   └── logging.py         # 日志系统
├── tests/                  # 测试文件
├── requirements.txt        # 依赖列表
└── README.md              # 本文件
```

## 技术栈

- **GUI**: CustomTkinter
- **异步**: asyncio + aiohttp
- **B站 API**: bilibili-api-python
- **语音转录**: faster-whisper
- **模型**: OpenAI Whisper

## 许可证

MIT License

## 更新日志

### v1.0.0
- 初始版本发布
- 支持视频信息解析
- 支持音频下载
- 支持 Whisper 转录
- 支持图形界面操作
