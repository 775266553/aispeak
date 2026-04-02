from __future__ import annotations

import asyncio
import atexit
import json
import mimetypes
import os
import socket
import subprocess
import sys
import threading
import time
import shutil
from email.parser import BytesParser
from email.policy import default as email_default_policy
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import unquote, urlparse


STITCH_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = STITCH_ROOT.parent / ".trae" / "skills" / "bilibili-subtitle-extractor"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from controller import Controller
from models import TaskStatus
from services import config, ensure_dirs, load_cookies, parse_cookie_string, save_cookies, verify_cookie


def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: Dict[str, Any] = {}
    error: Dict[str, BaseException] = {}

    def _worker():
        try:
            result["value"] = asyncio.run(coro)
        except BaseException as exc:  # pragma: no cover - propagated below
            error["value"] = exc

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    thread.join()
    if error:
        raise error["value"]
    return result.get("value")


def _safe_filename(value: str) -> str:
    return "".join(ch for ch in value if ch not in '<>:"/\\|?*')


class WebAdapter:
    def __init__(self, runtime: "BiliGlassRuntime"):
        self.runtime = runtime

    def after(self, delay_ms, callback):
        if delay_ms <= 0:
            callback()
            return

        timer = threading.Timer(delay_ms / 1000.0, callback)
        timer.daemon = True
        timer.start()

    def add_log(self, message: str):
        self.runtime.append_log(message)

    def add_task(self, task):
        self.runtime.append_log(f"已加入任务: {task.video_info.title}")

    def update_task(self, task_id, task):
        self.runtime.last_task_update = task_id

    def remove_task(self, task_id):
        self.runtime.last_removed_task = task_id


class BiliGlassRuntime:
    def __init__(self):
        ensure_dirs()
        self.controller = Controller()
        self.logs = deque(maxlen=200)
        self.log_lock = threading.Lock()
        self.state_lock = threading.RLock()
        self.last_task_update: Optional[str] = None
        self.last_removed_task: Optional[str] = None
        self.started_at = time.time()
        self.cookie_state = {
            "saved": False,
            "verified": False,
            "user": "未配置",
            "message": "未配置 Cookie",
        }

        self.adapter = WebAdapter(self)
        self.controller.set_app(self.adapter)
        self.settings = self.controller.load_settings()
        self.settings["delete_audio_after_transcribe"] = False
        self.controller.settings = self.settings
        self.refresh_cookie_state()
        self.controller.start()

    def append_log(self, message: str):
        with self.log_lock:
            self.logs.append({
                "ts": time.time(),
                "message": message,
            })

    def refresh_cookie_state(self, cookie_text: Optional[str] = None):
        if cookie_text is not None:
            cookies = parse_cookie_string(cookie_text)
            if cookies:
                save_cookies(cookies)

        cookies = load_cookies()
        if not cookies:
            self.cookie_state = {
                "saved": False,
                "verified": False,
                "user": "未配置",
                "message": "Cookie 未配置",
            }
            return self.cookie_state

        try:
            verified, user = _run_async(verify_cookie(cookies))
        except Exception as exc:
            verified = False
            user = str(exc)

        self.cookie_state = {
            "saved": True,
            "verified": bool(verified),
            "user": user if verified else "验证失败",
            "message": f"{'已登录' if verified else '验证失败'}: {user}",
        }
        return self.cookie_state

    def save_cookie_text(self, cookie_text: str):
        cookies = parse_cookie_string(cookie_text)
        if not cookies:
            raise ValueError("未找到有效 Cookie 字段，请检查是否包含 SESSDATA")

        if not save_cookies(cookies):
            raise RuntimeError("Cookie 保存失败")

        return self.refresh_cookie_state()

    def serialize_task(self, task) -> Dict[str, Any]:
        cover = getattr(task.video_info, "cover", None)
        status_key = task.status.name
        return {
            "id": task.id,
            "bvid": task.video_info.bvid,
            "title": task.video_info.title,
            "up主": task.video_info.up主,
            "duration": task.video_info.duration,
            "duration_str": task.duration_str,
            "cover": cover,
            "is_member_only": task.video_info.is会员专属,
            "page_count": task.video_info.page_count,
            "source_type": getattr(task.video_info, "source_type", "bilibili"),
            "source_name": getattr(task.video_info, "source_name", None),
            "source_path": getattr(task.video_info, "source_path", None),
            "display_title": task.display_title,
            "source_label": task.source_label,
            "status_key": status_key,
            "status": task.status.value,
            "status_text": task.status_text,
            "progress": task.progress,
            "stage": task.stage.value if task.stage else None,
            "stage_progress": task.stage_progress,
            "error_msg": task.error_msg,
            "audio_path": task.audio_path,
            "subtitle_path": task.subtitle_path,
            "download_speed": task.download_speed,
            "created_at": task.created_at,
        }

    def serialize_settings(self) -> Dict[str, Any]:
        current = dict(self.controller.settings or {})
        current.setdefault("download_concurrency", 3)
        current.setdefault("delete_audio_after_transcribe", True)
        current.setdefault("whisper_model", "base")
        current.setdefault("whisper_device", "auto")
        current.setdefault("output_format", "txt")
        current.setdefault("auto_open_dir", True)
        current.setdefault("log_level", "info")
        current["output_dir"] = str(config.output_dir)
        current["temp_audio_dir"] = str(config.temp_audio_dir)
        current["subtitles_dir"] = str(config.subtitles_dir)
        return current

    def system_stats(self) -> Dict[str, Any]:
        tasks = list(self.controller.tasks.values())
        counts = {
            "total": len(tasks),
            "running": sum(1 for task in tasks if task.status in (TaskStatus.DOWNLOADING, TaskStatus.TRANSCRIBING)),
            "waiting": sum(1 for task in tasks if task.status == TaskStatus.PENDING),
            "completed": sum(1 for task in tasks if task.status == TaskStatus.COMPLETED),
            "failed": sum(1 for task in tasks if task.status == TaskStatus.FAILED),
            "stopped": sum(1 for task in tasks if task.status == TaskStatus.STOPPED),
        }
        return counts

    def hardware_state(self) -> Dict[str, Any]:
        try:
            import torch

            cuda_available = bool(torch.cuda.is_available())
        except Exception:
            cuda_available = False

        return {
            "cuda_available": cuda_available,
            "device": self.controller.settings.get("whisper_device", "auto") if self.controller.settings else "auto",
            "model": self.controller.settings.get("whisper_model", "base") if self.controller.settings else "base",
        }

    def storage_state(self) -> Dict[str, Any]:
        output_dir = config.output_dir
        total_bytes = 0
        if output_dir.exists():
            for root, _, files in os.walk(output_dir):
                for filename in files:
                    try:
                        total_bytes += (Path(root) / filename).stat().st_size
                    except OSError:
                        continue
        used_gb = total_bytes / (1024 ** 3)
        return {
            "output_dir": str(output_dir),
            "used_gb": round(used_gb, 1),
        }

    def bootstrap(self) -> Dict[str, Any]:
        with self.state_lock:
            tasks = [self.serialize_task(task) for task in self.controller.tasks.values()]
            return {
                "settings": self.serialize_settings(),
                "cookie": dict(self.cookie_state),
                "stats": self.system_stats(),
                "hardware": self.hardware_state(),
                "storage": self.storage_state(),
                "tasks": tasks,
                "logs": list(self.logs)[-50:],
                "running": self.controller.is_running,
                "started_at": self.started_at,
            }

    def open_output_dir(self):
        target = str(config.output_dir)
        os.makedirs(target, exist_ok=True)
        os.startfile(target)
        return target

    def open_task_location(self, task_id: str):
        task = self.controller.tasks.get(task_id)
        if not task:
            raise KeyError("任务不存在")

        if task.subtitle_path:
            target = Path(task.subtitle_path).parent
        elif task.audio_path:
            target = Path(task.audio_path).parent
        else:
            target = config.subtitles_dir

        target.mkdir(parents=True, exist_ok=True)
        os.startfile(str(target))
        return str(target)

    def open_task_audio(self, task_id: str):
        task = self.controller.tasks.get(task_id)
        if not task:
            raise KeyError("任务不存在")

        if task.audio_path and Path(task.audio_path).exists():
            os.startfile(task.audio_path)
            return task.audio_path

        return self.open_task_location(task_id)

    def delete_task(self, task_id: str):
        task = self.controller.tasks.get(task_id)
        if not task:
            raise KeyError("任务不存在")
        task.status = TaskStatus.STOPPED
        task.progress = 0
        self.controller.tasks.pop(task_id, None)


RUNTIME = BiliGlassRuntime()


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "BiliGlassHTTP/1.0"

    def _send_json(self, payload: Dict[str, Any], status: int = 200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, text: str, status: int = 200, content_type: str = "text/plain; charset=utf-8"):
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def _read_multipart(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            raise ValueError("上传内容为空")

        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("multipart/form-data"):
            raise ValueError("上传请求必须使用 multipart/form-data")

        body = self.rfile.read(length)
        mime_bytes = (
            f"Content-Type: {content_type}\r\n"
            f"MIME-Version: 1.0\r\n\r\n"
        ).encode("utf-8") + body

        message = BytesParser(policy=email_default_policy).parsebytes(mime_bytes)
        if not message.is_multipart():
            raise ValueError("上传内容解析失败")
        return message

    def _store_local_uploads(self, form) -> list[Dict[str, Any]]:
        upload_root = config.temp_audio_dir / "local_uploads" / time.strftime("%Y%m%d_%H%M%S")
        upload_root.mkdir(parents=True, exist_ok=True)

        parts = []
        for part in form.iter_parts():
            filename = part.get_filename()
            if not filename:
                continue
            parts.append(part)

        if not parts:
            raise ValueError("请选择要转写的文件")

        uploaded: list[Dict[str, Any]] = []

        for part in parts:
            filename = Path(part.get_filename() or "upload.bin").name
            if not Controller.is_supported_local_media(filename):
                raise ValueError(f"不支持的媒体格式: {Path(filename).suffix or '未知'}")

            safe_stem = _safe_filename(Path(filename).stem) or "upload"
            suffix = Path(filename).suffix
            target_path = upload_root / f"{safe_stem}{suffix}"
            counter = 1
            while target_path.exists():
                target_path = upload_root / f"{safe_stem}_{counter}{suffix}"
                counter += 1

            with open(target_path, "wb") as target_file:
                target_file.write(part.get_payload(decode=True) or b"")

            task = RUNTIME.controller.add_local_file(str(target_path), source_name=filename)
            uploaded.append(RUNTIME.serialize_task(task))

        return uploaded

    def _resolve_static_path(self, request_path: str) -> Path:
        clean = unquote(urlparse(request_path).path)
        if clean in ("/", ""):
            return STITCH_ROOT / "_2" / "code.html"
        if clean == "/settings":
            return STITCH_ROOT / "_1" / "code.html"
        if clean == "/console":
            return STITCH_ROOT / "_2" / "code.html"

        if clean.startswith("/api/"):
            return Path("")

        relative = clean.lstrip("/")
        candidate = (STITCH_ROOT / relative).resolve()
        if not str(candidate).startswith(str(STITCH_ROOT.resolve())):
            raise FileNotFoundError("Forbidden")
        return candidate

    def _serve_static(self):
        path = self._resolve_static_path(self.path)
        if not path or not path.exists() or path.is_dir():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        content_type, _ = mimetypes.guess_type(str(path))
        content_type = content_type or "application/octet-stream"
        data = path.read_bytes()

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        clean = unquote(urlparse(self.path).path)
        if clean == "/api/bootstrap":
            self._send_json(RUNTIME.bootstrap())
            return
        if clean == "/api/settings":
            self._send_json({"settings": RUNTIME.serialize_settings(), "cookie": dict(RUNTIME.cookie_state)})
            return
        if clean == "/api/tasks":
            self._send_json({"tasks": [RUNTIME.serialize_task(task) for task in RUNTIME.controller.tasks.values()]})
            return
        if clean == "/api/logs":
            self._send_json({"logs": list(RUNTIME.logs)})
            return
        self._serve_static()

    def do_POST(self):
        clean = unquote(urlparse(self.path).path)
        payload = {}
        content_type = self.headers.get("Content-Type", "")
        if content_type.startswith("application/json"):
            payload = self._read_json()

        try:
            if clean == "/api/local/upload":
                form = self._read_multipart()
                tasks = self._store_local_uploads(form)
                self._send_json({"ok": True, "message": "本地文件已加入任务", "count": len(tasks), "tasks": tasks}, 201)
                return

            if clean == "/api/tasks/add":
                value = (payload.get("input") or "").strip()
                if not value:
                    raise ValueError("请输入 BV 号或视频链接")
                RUNTIME.controller.add_input(value)
                self._send_json({"ok": True, "message": "任务已加入"}, 201)
                return

            if clean == "/api/tasks/start":
                RUNTIME.controller.start()
                RUNTIME.controller.start_processing()
                self._send_json({"ok": True, "message": "开始处理"})
                return

            if clean == "/api/tasks/stop":
                RUNTIME.controller.stop()
                self._send_json({"ok": True, "message": "已停止"})
                return

            if clean == "/api/tasks/retry-failed":
                RUNTIME.controller.retry_failed()
                self._send_json({"ok": True, "message": "失败任务已重试"})
                return

            if clean == "/api/tasks/clear-completed":
                RUNTIME.controller.clear_completed()
                self._send_json({"ok": True, "message": "已清空完成任务"})
                return

            if clean.startswith("/api/tasks/") and clean.endswith("/retry"):
                task_id = clean.split("/")[3]
                RUNTIME.controller.retry_task(task_id)
                self._send_json({"ok": True, "message": "任务已重试"})
                return

            if clean.startswith("/api/tasks/") and clean.endswith("/stop"):
                task_id = clean.split("/")[3]
                task = RUNTIME.controller.tasks.get(task_id)
                if task:
                    task.status = TaskStatus.STOPPED
                    task.progress = 0
                self._send_json({"ok": True, "message": "任务已停止"})
                return

            if clean.startswith("/api/tasks/") and clean.endswith("/open"):
                task_id = clean.split("/")[3]
                target = RUNTIME.open_task_location(task_id)
                self._send_json({"ok": True, "target": target})
                return

            if clean.startswith("/api/tasks/") and clean.endswith("/open-audio"):
                task_id = clean.split("/")[3]
                target = RUNTIME.open_task_audio(task_id)
                self._send_json({"ok": True, "target": target})
                return

            if clean.startswith("/api/tasks/") and clean.endswith("/delete"):
                task_id = clean.split("/")[3]
                RUNTIME.delete_task(task_id)
                self._send_json({"ok": True, "message": "任务已移除"})
                return

            if clean == "/api/settings/save":
                new_settings = payload.get("settings") or {}
                merged = RUNTIME.serialize_settings()
                merged.update(new_settings)
                merged["download_concurrency"] = int(merged.get("download_concurrency", 3))
                RUNTIME.controller.save_settings(merged)
                RUNTIME.settings = merged
                self._send_json({"ok": True, "settings": RUNTIME.serialize_settings()})
                return

            if clean == "/api/cookie/save":
                cookie_text = payload.get("cookie_text") or ""
                cookie_state = RUNTIME.save_cookie_text(cookie_text)
                self._send_json({"ok": True, "cookie": cookie_state})
                return

            if clean == "/api/cookie/verify":
                cookie_text = payload.get("cookie_text") or None
                if cookie_text:
                    cookie_state = RUNTIME.refresh_cookie_state(cookie_text)
                else:
                    cookie_state = RUNTIME.refresh_cookie_state()
                self._send_json({"ok": True, "cookie": cookie_state})
                return

            if clean == "/api/output/open":
                target = RUNTIME.open_output_dir()
                self._send_json({"ok": True, "target": target})
                return

            if clean == "/api/cookie/load":
                self._send_json({"ok": True, "cookies": load_cookies()})
                return

            self._send_json({"ok": False, "error": "Unknown endpoint"}, 404)
        except Exception as exc:
            self._send_json({"ok": False, "error": str(exc)}, 400)

    def log_message(self, format: str, *args):
        return


def find_free_port(start: int = 8765, limit: int = 100) -> int:
    for port in range(start, start + limit):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("无法找到可用端口")


def run_server(host: str = "127.0.0.1", port: Optional[int] = None):
    actual_port = port or find_free_port()
    server = ThreadingHTTPServer((host, actual_port), RequestHandler)

    def _shutdown():
        try:
            RUNTIME.controller.stop()
        except Exception:
            pass
        try:
            server.server_close()
        except Exception:
            pass

    atexit.register(_shutdown)

    print(f"BiliGlass web server running at http://{host}:{actual_port}")
    print(f"Console: http://{host}:{actual_port}/_2/code.html")
    print(f"Settings: http://{host}:{actual_port}/_1/code.html")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _shutdown()


if __name__ == "__main__":
    run_server()
