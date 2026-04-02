import asyncio
import hashlib
import threading
import queue
import os
from pathlib import Path
from typing import Dict, Callable, Set
from models import Task, TaskStatus, VideoInfo
from services import (
    config, setup_logging, get_logger, user_log,
    extract_bvid, get_video_info, download_audio, check_bilibili_subtitle,
    download_ai_subtitle,
    create_transcriber
)

logger = get_logger(__name__)

SUPPORTED_LOCAL_MEDIA_EXTENSIONS = {
    ".mp3",
    ".mp4",
    ".m4a",
    ".wav",
    ".flac",
    ".aac",
    ".mov",
    ".mkv",
    ".avi",
    ".webm",
}

class Controller:
    def __init__(self):
        self.app = None
        self.tasks: Dict[str, Task] = {}
        self.download_queue = queue.Queue()
        self.transcribe_queue = queue.Queue()
        self.download_thread = None
        self.transcribe_thread = None
        self.stop_event = threading.Event()
        self.is_running = False
        self.concurrency = 3
        self.settings = {}
        self.video_info_cache = {}
        self._active_download_tasks: Set[asyncio.Task] = set()
        self._transcribe_stop_flag = threading.Event()
        self._fetching_bvids: Set[str] = set()  # 正在获取视频信息的 BV 号

    @staticmethod
    def is_supported_local_media(file_path: str) -> bool:
        return Path(file_path).suffix.lower() in SUPPORTED_LOCAL_MEDIA_EXTENSIONS

    def _queue_task_for_processing(self, task: Task):
        task.is_enqueued = True
        if task.video_info.source_type == "local":
            self.transcribe_queue.put(task)
        else:
            self.download_queue.put(task)

    def set_app(self, app):
        self.app = app

    def load_settings(self):
        self.settings = config.load_settings()
        self.concurrency = self.settings.get("download_concurrency", 3)
        setup_logging(self.settings.get("log_level", "info"))
        return self.settings

    def save_settings(self, new_settings: dict):
        config.save_settings(new_settings)
        self.settings = new_settings
        self.concurrency = new_settings.get("download_concurrency", 3)
        setup_logging(new_settings.get("log_level", "info"))

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.stop_event.clear()

        self.download_thread = threading.Thread(target=self._download_worker, daemon=True)
        self.download_thread.start()

        self.transcribe_thread = threading.Thread(target=self._transcribe_worker, daemon=True)
        self.transcribe_thread.start()

        logger.info("Controller started")

    def stop(self):
        if not self.is_running:
            return

        logger.info("Stopping controller...")

        self.is_running = False
        self.stop_event.set()
        self._transcribe_stop_flag.set()

        for task in self._active_download_tasks:
            task.cancel()

        pending_tasks = []
        while True:
            try:
                t = self.download_queue.get_nowait()
                pending_tasks.append(t)
            except queue.Empty:
                break

        while True:
            try:
                t = self.transcribe_queue.get_nowait()
                pending_tasks.append(t)
            except queue.Empty:
                break

        for task in pending_tasks:
            if task.status in [TaskStatus.PENDING, TaskStatus.DOWNLOADING, TaskStatus.TRANSCRIBING]:
                task.status = TaskStatus.STOPPED
                task.progress = 0
                self._update_task_ui(task)

        for task in self.tasks.values():
            if task.status in [TaskStatus.DOWNLOADING, TaskStatus.TRANSCRIBING]:
                task.status = TaskStatus.STOPPED
                task.progress = 0
                self._update_task_ui(task)

        if self.download_thread:
            self.download_thread.join(timeout=3)
        if self.transcribe_thread:
            self.transcribe_thread.join(timeout=3)

        self._active_download_tasks.clear()
        logger.info("Controller stopped")

    def add_input(self, url_or_bvid: str):
        bvid = extract_bvid(url_or_bvid)
        if not bvid:
            user_log.add(f"❌ 无效的输入: {url_or_bvid}", "error")
            self.app.add_log(f"❌ 无效的输入格式")
            return

        # 检查是否已在任务列表中
        for task in self.tasks.values():
            if task.video_info.bvid == bvid:
                self.app.add_log(f"⚠️ 视频已在列表中: {bvid}")
                return

        # 检查是否正在获取信息中
        if bvid in self._fetching_bvids:
            self.app.add_log(f"⏳ 正在获取视频信息，请稍候: {bvid}")
            return

        # 标记为正在获取
        self._fetching_bvids.add(bvid)

        user_log.add(f"⏳ 正在解析视频信息: {bvid}", "info")
        self.app.add_log(f"⏳ 正在解析视频信息: {bvid}")

        thread = threading.Thread(target=self._fetch_video_info, args=(bvid,), daemon=True)
        thread.start()

    def add_local_file(self, file_path: str, source_name: str | None = None):
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if not self.is_supported_local_media(file_path):
            raise ValueError(f"不支持的媒体格式: {path.suffix or '未知'}")

        resolved_path = str(path.resolve())
        for task in self.tasks.values():
            if task.video_info.source_type == "local" and task.video_info.source_path == resolved_path:
                self.app.add_log(f"⚠️ 本地文件已在列表中: {path.name}")
                return task

        source_key = hashlib.sha1(resolved_path.encode("utf-8")).hexdigest()[:10]
        display_name = source_name or path.name
        task = Task(
            id=f"task_local_{source_key}",
            video_info=VideoInfo(
                bvid=f"LOCAL_{source_key}",
                title=path.stem,
                up主="本地文件",
                duration=0,
                page_count=1,
                source_type="local",
                source_name=display_name,
                source_path=resolved_path,
            ),
            status=TaskStatus.PENDING,
            audio_path=resolved_path,
        )

        self.tasks[task.id] = task
        self.app.add_task(task)
        user_log.add(f"✅ 已添加本地文件: {display_name}", "info")
        self.app.add_log(f"✅ 已添加本地文件: {display_name}")

        if self.is_running and not self.stop_event.is_set():
            self._queue_task_for_processing(task)

        return task

    def add_local_files(self, file_paths: list[str]):
        tasks = []
        for file_path in file_paths:
            task = self.add_local_file(file_path)
            if task:
                tasks.append(task)
        return tasks

    def _fetch_video_info(self, bvid: str):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                video_info = loop.run_until_complete(get_video_info(bvid))
                task = Task(
                    id=f"task_{bvid}",
                    video_info=video_info,
                    status=TaskStatus.PENDING
                )
                self.tasks[task.id] = task
                self.app.add_task(task)
                user_log.add(f"✅ 已添加: {video_info.title}", "info")
                self.app.add_log(f"✅ 已添加: {video_info.title} ({video_info.up主})")
            except Exception as e:
                logger.error(f"Failed to get video info: {e}")
                user_log.add(f"❌ 获取视频信息失败: {bvid}", "error")
                self.app.add_log(f"❌ 获取视频信息失败: {e}")
            finally:
                loop.close()
        finally:
            # 移除正在获取的标记
            self._fetching_bvids.discard(bvid)

    def _download_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_download(task):
            try:
                await self._do_download(task, loop)
            finally:
                self._active_download_tasks.discard(asyncio.current_task())

        async def main_loop():
            pending_tasks = []

            while not self.stop_event.is_set():
                # 从队列获取新任务
                while len(self._active_download_tasks) < self.concurrency:
                    try:
                        task = self.download_queue.get_nowait()
                        pending_tasks.append(task)
                    except queue.Empty:
                        break

                # 启动待处理的任务
                while pending_tasks and len(self._active_download_tasks) < self.concurrency:
                    task = pending_tasks.pop(0)
                    download_task = asyncio.ensure_future(run_download(task))
                    self._active_download_tasks.add(download_task)

                # 让出控制权给事件循环
                await asyncio.sleep(0.1)

            # 停止时处理
            for task in pending_tasks:
                self.download_queue.put(task)

            for download_task in list(self._active_download_tasks):
                download_task.cancel()

            if self._active_download_tasks:
                await asyncio.gather(*self._active_download_tasks, return_exceptions=True)

        try:
            loop.run_until_complete(main_loop())
        finally:
            loop.close()

    async def _do_download(self, task: Task, loop):
        if self.stop_event.is_set():
            task.status = TaskStatus.STOPPED
            self._update_task_ui(task)
            return

        try:
            task.status = TaskStatus.DOWNLOADING
            task.progress = 0
            self._update_task_ui(task)

            self._log_task(f"🔎 优先检查 AI 文稿: {task.video_info.title}")

            subtitle_dir = config.subtitles_dir
            subtitle_dir.mkdir(parents=True, exist_ok=True)
            ai_subtitle_path = await download_ai_subtitle(task.video_info.bvid, subtitle_dir)
            if ai_subtitle_path:
                task.subtitle_path = ai_subtitle_path
                task.progress = 100
                task.status = TaskStatus.COMPLETED
                self._log_task(f"✅ AI 文稿已保存: {task.video_info.title}")

                if self.settings.get("auto_open_dir", True):
                    import subprocess
                    subprocess.Popen(f'explorer /select,"{ai_subtitle_path}"')

                self._update_task_ui(task)
                return

            self._log_task(f"⚠️ 未找到 AI 文稿，切换为 mp3 下载转写: {task.video_info.title}")

            bvid = task.video_info.bvid
            audio_dir = config.temp_audio_dir
            audio_dir.mkdir(parents=True, exist_ok=True)

            self._log_task(f"⬇️ 开始下载 mp3: {task.video_info.title}")

            def progress_callback(progress, speed):
                if self.stop_event.is_set():
                    raise asyncio.CancelledError()
                task.progress = progress
                task.download_speed = speed
                self._update_task_ui(task)

            audio_path = await download_audio(bvid, audio_dir, progress_callback)

            if self.stop_event.is_set():
                task.status = TaskStatus.STOPPED
                self._update_task_ui(task)
                return

            task.audio_path = audio_path
            task.progress = 100

            self._log_task(f"🎧 mp3 下载完成，准备转写: {task.video_info.title}")

            user_log.add(f"📥 下载完成: {task.video_info.title}", "info")
            self.app.add_log(f"📥 下载完成: {task.video_info.title}")

            if not self.stop_event.is_set():
                self.transcribe_queue.put(task)
            else:
                task.status = TaskStatus.STOPPED
                self._update_task_ui(task)

        except asyncio.CancelledError:
            task.status = TaskStatus.STOPPED
            task.progress = 0
            self._update_task_ui(task)
            logger.info(f"Download cancelled: {task.video_info.title}")
        except Exception as e:
            if not self.stop_event.is_set():
                task.status = TaskStatus.FAILED
                task.error_msg = str(e)[:50]
                user_log.add(f"❌ 下载失败: {task.video_info.title} - {e}", "error")
                self.app.add_log(f"❌ 下载失败: {task.video_info.title}")
                logger.error(f"Download failed: {e}")
        finally:
            self._update_task_ui(task)

    def _transcribe_worker(self):
        self._transcribe_stop_flag.clear()
        while not self.stop_event.is_set():
            try:
                task = self.transcribe_queue.get(timeout=0.3)
                if self.stop_event.is_set() or self._transcribe_stop_flag.is_set():
                    task.status = TaskStatus.STOPPED
                    self._update_task_ui(task)
                    continue
                self._do_transcribe(task)
            except queue.Empty:
                continue

    def _do_transcribe(self, task: Task):
        if self.stop_event.is_set() or self._transcribe_stop_flag.is_set():
            task.status = TaskStatus.STOPPED
            self._update_task_ui(task)
            return

        try:
            task.status = TaskStatus.TRANSCRIBING
            task.progress = 0
            task.stage = None
            self._update_task_ui(task)

            from models import TranscribeStage
            transcriber = create_transcriber()

            self._log_task(f"📝 开始转写文稿: {task.video_info.title}")

            last_stage = None

            def progress_callback(stage, progress):
                nonlocal last_stage
                if self.stop_event.is_set() or self._transcribe_stop_flag.is_set():
                    raise InterruptedError("Transcription stopped")
                task.stage = stage
                task.progress = progress
                if stage != last_stage:
                    last_stage = stage
                    stage_messages = {
                        TranscribeStage.MODEL_LOADING: "正在加载模型",
                        TranscribeStage.TRANSCRIBING: "正在识别语音",
                        TranscribeStage.WRITING_FILE: "正在写入文稿文件",
                    }
                    self._log_task(f"📍 {stage_messages.get(stage, stage.value)}: {task.video_info.title}")
                self._update_task_ui(task)

            subtitle_dir = config.subtitles_dir
            subtitle_dir.mkdir(parents=True, exist_ok=True)

            safe_title = task.video_info.title.replace('"', '').replace(':', '').replace('\\', '').replace('/', '').replace('*', '').replace('?', '').replace('<', '').replace('>', '').replace('|', '')
            output_path = subtitle_dir / f"{safe_title}.txt"

            if self.stop_event.is_set() or self._transcribe_stop_flag.is_set():
                task.status = TaskStatus.STOPPED
                self._update_task_ui(task)
                return

            transcriber.transcribe(
                task.audio_path,
                str(output_path),
                progress_callback
            )

            if self.stop_event.is_set() or self._transcribe_stop_flag.is_set():
                task.status = TaskStatus.STOPPED
                self._update_task_ui(task)
                return

            task.subtitle_path = str(output_path)
            task.status = TaskStatus.COMPLETED
            task.progress = 100

            self._log_task(f"✅ 文稿转写完成: {task.video_info.title}")

            if self.settings.get("delete_audio_after_transcribe", False) and task.audio_path and os.path.exists(task.audio_path):
                os.remove(task.audio_path)

            user_log.add(f"✅ 转录完成: {task.video_info.title}", "info")
            self.app.add_log(f"✅ 转录完成: {task.video_info.title}")

            if self.settings.get("auto_open_dir", True):
                import subprocess
                subprocess.Popen(f'explorer /select,"{output_path}"')

        except InterruptedError:
            task.status = TaskStatus.STOPPED
            task.progress = 0
            user_log.add(f"⏹️ 转录已停止: {task.video_info.title}", "info")
            self._update_task_ui(task)
        except Exception as e:
            if not self.stop_event.is_set() and not self._transcribe_stop_flag.is_set():
                task.status = TaskStatus.FAILED
                task.error_msg = str(e)[:50]
                user_log.add(f"❌ 转录失败: {task.video_info.title} - {e}", "error")
                self.app.add_log(f"❌ 转录失败: {task.video_info.title}")
                logger.error(f"Transcription failed: {e}")
            else:
                task.status = TaskStatus.STOPPED
                user_log.add(f"⏹️ 转录已停止: {task.video_info.title}", "info")

        self._update_task_ui(task)

    def _update_task_ui(self, task: Task):
        if self.app:
            self.app.after(0, lambda: self.app.update_task(task.id, task))

    def _log_task(self, message: str, level: str = "info"):
        user_log.add(message, level)
        if self.app:
            self.app.add_log(message)

    def start_processing(self):
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING and not task.is_enqueued:
                self._queue_task_for_processing(task)
                logger.info(f"Queued task: {task.video_info.title}")

    def retry_failed(self):
        for task in self.tasks.values():
            if task.status == TaskStatus.FAILED:
                task.status = TaskStatus.PENDING
                task.error_msg = None
                task.progress = 0
                self._queue_task_for_processing(task)
                self._update_task_ui(task)
                logger.info(f"Retrying task: {task.video_info.title}")

    def retry_task(self, task_id: str):
        task = self.tasks.get(task_id)
        if not task:
            return

        if task.status not in [TaskStatus.FAILED, TaskStatus.STOPPED, TaskStatus.COMPLETED]:
            return

        task.status = TaskStatus.PENDING
        task.error_msg = None
        task.progress = 0
        task.stage = None
        task.stage_progress = 0
        self._queue_task_for_processing(task)
        self._update_task_ui(task)
        logger.info(f"Retrying single task: {task.video_info.title}")

    def clear_completed(self):
        to_remove = [tid for tid, t in self.tasks.items() if t.status == TaskStatus.COMPLETED]
        for tid in to_remove:
            del self.tasks[tid]
            if self.app:
                self.app.after(0, lambda: self.app.remove_task(tid))
