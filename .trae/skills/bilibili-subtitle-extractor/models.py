from dataclasses import dataclass
from enum import Enum
from typing import Optional
import time

class TaskStatus(Enum):
    PENDING = "等待中"
    DOWNLOADING = "下载中"
    TRANSCRIBING = "转录中"
    COMPLETED = "已完成"
    FAILED = "失败"
    STOPPED = "已停止"

class TranscribeStage(Enum):
    MODEL_LOADING = "加载模型"
    TRANSCRIBING = "识别语音"
    WRITING_FILE = "写入文件"

@dataclass
class VideoInfo:
    bvid: str
    title: str
    up主: str
    duration: int
    cover: Optional[str] = None
    is会员专属: bool = False
    page_count: int = 1
    source_type: str = "bilibili"
    source_name: Optional[str] = None
    source_path: Optional[str] = None

@dataclass
class Task:
    id: str
    video_info: VideoInfo
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    stage: Optional[TranscribeStage] = None
    stage_progress: float = 0.0
    error_msg: Optional[str] = None
    audio_path: Optional[str] = None
    subtitle_path: Optional[str] = None
    download_speed: Optional[str] = None
    created_at: float = None
    is_enqueued: bool = False

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

    @property
    def short_bvid(self) -> str:
        return self.video_info.bvid[:10] + "..."

    @property
    def display_title(self) -> str:
        return self.video_info.source_name or self.video_info.title

    @property
    def source_label(self) -> str:
        if self.video_info.source_type == "local":
            return self.video_info.source_name or self.video_info.title
        return self.video_info.bvid

    @property
    def duration_str(self) -> str:
        mins = self.video_info.duration // 60
        secs = self.video_info.duration % 60
        return f"{mins}:{secs:02d}"

    @property
    def status_text(self) -> str:
        if self.status == TaskStatus.DOWNLOADING:
            return f"下载中 {int(self.progress)}%"
        elif self.status == TaskStatus.TRANSCRIBING:
            if self.stage:
                return f"转录中 {int(self.progress)}% [{self.stage.value}]"
            return f"转录中 {int(self.progress)}%"
        elif self.status == TaskStatus.FAILED:
            return f"失败: {self.error_msg or '未知错误'}"
        return self.status.value
