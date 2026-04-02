from __future__ import annotations

import asyncio
import sys
import threading
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent / ".trae" / "skills" / "bilibili-subtitle-extractor"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def _fail(message: str) -> None:
    print(message)
    raise SystemExit(1)


try:
    import customtkinter as ctk
except ImportError as exc:
    _fail(f"缺少 GUI 依赖 customtkinter: {exc}")

try:
    from controller import Controller
    from models import Task
    from services import (
        config,
        ensure_dirs,
        load_cookies,
        parse_cookie_string,
        save_cookies,
        verify_cookie,
    )
    from ui_v2 import BilibiliSubtitleApp
except ImportError as exc:
    _fail(f"无法导入 GUI 运行所需模块: {exc}")


def detect_cuda() -> bool:
    try:
        import torch

        return torch.cuda.is_available()
    except Exception:
        return False


def verify_cookie_sync(cookie_data: dict) -> tuple[bool, str]:
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(verify_cookie(cookie_data))
    finally:
        loop.close()


def build_runtime(app: BilibiliSubtitleApp) -> Controller:
    controller = Controller()
    controller.set_app(app)
    controller.load_settings()
    ensure_dirs()

    def refresh_environment() -> None:
        def worker() -> None:
            cookie_ok = False
            cookie_data = load_cookies()
            if cookie_data:
                try:
                    cookie_ok, _ = verify_cookie_sync(cookie_data)
                except Exception as exc:
                    cookie_ok = False
                    app.after(0, lambda: app.add_log(f"❌ Cookie 验证失败: {exc}"))

            cuda_ok = detect_cuda()
            dir_ok = config.output_dir.exists()
            device = "cuda" if cuda_ok else "cpu"

            def update_ui() -> None:
                app.update_env_status(cookie_ok, cuda_ok, dir_ok)
                app.update_device(device)
                app.add_log("环境检查完成")

            app.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def on_add_input(value: str) -> None:
        controller.add_input(value)

    def on_save_settings(settings: dict) -> None:
        controller.save_settings(settings)
        ensure_dirs()
        app.update_device(settings.get("whisper_device", "auto"))
        app.add_log("设置已保存")
        refresh_environment()

    def on_cookie_click() -> None:
        def on_save(cookie_str: str, dialog) -> None:
            def worker() -> None:
                try:
                    cookie_data = parse_cookie_string(cookie_str)
                    if not cookie_data:
                        raise ValueError("未解析到有效 Cookie")
                    save_cookies(cookie_data)
                    ok, message = verify_cookie_sync(cookie_data)

                    def finish() -> None:
                        dialog.show_result(ok, message if ok else f"验证失败: {message}")
                        refresh_environment()

                    app.after(0, finish)
                except Exception as exc:
                    app.after(0, lambda: dialog.show_result(False, str(exc)))

            threading.Thread(target=worker, daemon=True).start()

        app.show_cookie_dialog(on_save)

    def on_start() -> None:
        controller.start()
        controller.start_processing()
        app.add_log("开始处理任务...")

    def on_stop() -> None:
        controller.stop()
        app.add_log("已停止所有任务")

    def on_retry(task_id: str | None = None) -> None:
        if task_id:
            controller.retry_task(task_id)
            app.add_log(f"已重试任务: {task_id}")
            return

        controller.retry_failed()
        app.add_log("已重试失败任务")

    def on_clear() -> None:
        controller.clear_completed()
        app.add_log("已清空完成任务")

    app.set_input_callback(on_add_input)
    app.set_settings_callback(lambda: app.show_settings_dialog(controller.settings, on_save_settings))
    app.set_cookie_callback(on_cookie_click)
    app.set_start_callback(on_start)
    app.set_stop_callback(on_stop)
    app.set_retry_callback(on_retry)
    app.set_clear_callback(on_clear)
    app.protocol("WM_DELETE_WINDOW", lambda: on_close(app, controller))

    refresh_environment()
    return controller


def on_close(app: BilibiliSubtitleApp, controller: Controller) -> None:
    try:
        controller.stop()
    except Exception:
        pass
    app.destroy()


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = BilibiliSubtitleApp()
    build_runtime(app)
    app.mainloop()


if __name__ == "__main__":
    main()