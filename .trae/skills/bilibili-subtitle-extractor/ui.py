import customtkinter as ctk
from tkinter import filedialog
import threading
import queue
from typing import Callable, Optional
from models import Task, TaskStatus, TranscribeStage

class CookieDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback: Callable):
        super().__init__(parent)
        self.on_save_callback = on_save_callback
        self.title("🔑 更新 Cookie")
        self.geometry("500x350")
        self.resizable(False, False)
        self.grab_set()
        self.setup_ui()

    def setup_ui(self):
        label = ctk.CTkLabel(self, text="请粘贴浏览器中的 B站 Cookie 字符串:", font=("", 14))
        label.pack(pady=(20, 10), padx=20)

        self.textbox = ctk.CTkTextbox(self, height=150)
        self.textbox.pack(pady=10, padx=20, fill="both", expand=True)

        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=15, padx=20, fill="x")

        self.save_btn = ctk.CTkButton(
            button_frame, text="💾 保存并验证",
            command=self.on_save,
            fg_color="#4CAF50"
        )
        self.save_btn.pack(side="left", padx=5, expand=True, fill="x")

        cancel_btn = ctk.CTkButton(
            button_frame, text="❌ 取消",
            command=self.destroy,
            fg_color="gray"
        )
        cancel_btn.pack(side="left", padx=5, expand=True, fill="x")

        self.status_label = ctk.CTkLabel(self, text="", font=("", 12))
        self.status_label.pack(pady=10)

    def on_save(self):
        cookie_str = self.textbox.get("1.0", "end-1c")
        self.save_btn.configure(state="disabled", text="⏳ 验证中...")
        self.status_label.configure(text="正在验证 Cookie...")
        self.on_save_callback(cookie_str, self)

    def show_result(self, success: bool, message: str):
        if success:
            self.status_label.configure(text=f"✅ {message}", text_color="green")
            self.after(1500, self.destroy)
        else:
            self.status_label.configure(text=f"❌ {message}", text_color="red")
            self.save_btn.configure(state="normal", text="💾 保存并验证")

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, settings: dict, on_save_callback: Callable):
        super().__init__(parent)
        self.settings = settings
        self.on_save_callback = on_save_callback
        self.title("⚙️ 设置")
        self.geometry("450x400")
        self.grab_set()
        self.setup_ui()

    def setup_ui(self):
        tabview = ctk.CTkTabview(self)
        tabview.pack(pady=20, padx=20, fill="both", expand=True)

        tab_download = tabview.add("下载设置")
        tab_transcribe = tabview.add("转录设置")
        tab_ui = tabview.add("界面设置")

        ctk.CTkLabel(tab_download, text="并发数:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.concurrency_var = ctk.StringVar(value=str(self.settings.get("download_concurrency", 3)))
        concurrency_menu = ctk.CTkOptionMenu(tab_download, variable=self.concurrency_var, values=["1", "2", "3", "4", "5"])
        concurrency_menu.grid(row=0, column=1, sticky="w", padx=10, pady=10)

        ctk.CTkLabel(tab_download, text="输出目录:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.output_dir_var = ctk.StringVar(value=self.settings.get("output_dir", ""))
        ctk.CTkEntry(tab_download, textvariable=self.output_dir_var, width=200).grid(row=1, column=1, padx=10, pady=10)
        ctk.CTkButton(tab_download, text="浏览...", command=self.browse_dir, width=60).grid(row=1, column=2, padx=5, pady=10)

        self.delete_audio_var = ctk.BooleanVar(value=self.settings.get("delete_audio_after_transcribe", True))
        ctk.CTkCheckBox(tab_download, text="下载完成后删除临时音频", variable=self.delete_audio_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        ctk.CTkLabel(tab_transcribe, text="模型:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.model_var = ctk.StringVar(value=self.settings.get("whisper_model", "base"))
        model_menu = ctk.CTkOptionMenu(tab_transcribe, variable=self.model_var, values=["tiny", "base", "small", "medium", "large"])
        model_menu.grid(row=0, column=1, sticky="w", padx=10, pady=10)

        ctk.CTkLabel(tab_transcribe, text="设备:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.device_var = ctk.StringVar(value=self.settings.get("whisper_device", "auto"))
        device_menu = ctk.CTkOptionMenu(tab_transcribe, variable=self.device_var, values=["auto", "cpu", "cuda"])
        device_menu.grid(row=1, column=1, sticky="w", padx=10, pady=10)

        ctk.CTkLabel(tab_transcribe, text="输出格式:").grid(row=2, column=0, sticky="w", padx=10, pady=10)
        self.format_var = ctk.StringVar(value=self.settings.get("output_format", "txt"))
        format_menu = ctk.CTkOptionMenu(tab_transcribe, variable=self.format_var, values=["txt", "srt", "json"])
        format_menu.grid(row=2, column=1, sticky="w", padx=10, pady=10)

        self.auto_open_var = ctk.BooleanVar(value=self.settings.get("auto_open_dir", True))
        ctk.CTkCheckBox(tab_ui, text="完成后自动打开输出目录", variable=self.auto_open_var).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        ctk.CTkLabel(tab_ui, text="日志级别:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.log_level_var = ctk.StringVar(value=self.settings.get("log_level", "info"))
        log_menu = ctk.CTkOptionMenu(tab_ui, variable=self.log_level_var, values=["debug", "info", "warning"])
        log_menu.grid(row=1, column=1, sticky="w", padx=10, pady=10)

        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=15, padx=20, fill="x")

        ctk.CTkButton(
            button_frame, text="💾 保存设置",
            command=self.on_save,
            fg_color="#4CAF50"
        ).pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkButton(
            button_frame, text="❌ 取消",
            command=self.destroy,
            fg_color="gray"
        ).pack(side="left", padx=5, expand=True, fill="x")

    def browse_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir_var.set(dir_path)

    def on_save(self):
        new_settings = {
            "download_concurrency": int(self.concurrency_var.get()),
            "output_dir": self.output_dir_var.get(),
            "delete_audio_after_transcribe": self.delete_audio_var.get(),
            "whisper_model": self.model_var.get(),
            "whisper_device": self.device_var.get(),
            "output_format": self.format_var.get(),
            "auto_open_dir": self.auto_open_var.get(),
            "log_level": self.log_level_var.get()
        }
        self.on_save_callback(new_settings)
        self.destroy()

class TaskItem(ctk.CTkFrame):
    def __init__(self, parent, task: Task, on_retry_callback: Callable = None, on_delete_callback: Callable = None, on_open_callback: Callable = None):
        super().__init__(parent, fg_color=["#2a2a2a", "#3a3a3a"])
        self.task = task
        self.on_retry_callback = on_retry_callback
        self.on_delete_callback = on_delete_callback
        self.on_open_callback = on_open_callback
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)

        icon_map = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.DOWNLOADING: "📥",
            TaskStatus.TRANSCRIBING: "🎙️",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.STOPPED: "⏹️"
        }
        icon = ctk.CTkLabel(self, text=icon_map.get(self.task.status, "📺"), font=("", 16))
        icon.grid(row=0, column=0, rowspan=2, padx=(10, 5), pady=10)

        title_text = f"{self.task.video_info.title} ({self.task.duration_str}) - {self.task.video_info.up主}"
        self.title_label = ctk.CTkLabel(self, text=title_text, font=("", 12), anchor="w")
        self.title_label.grid(row=0, column=1, columnspan=2, sticky="w", padx=5, pady=(10, 5))

        self.status_label = ctk.CTkLabel(self, text=self.task.status_text, font=("", 11), anchor="w", text_color="gray")
        self.status_label.grid(row=1, column=1, sticky="w", padx=5, pady=(0, 10))

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=0, column=3, rowspan=2, padx=5, pady=10)

        if self.task.status == TaskStatus.COMPLETED:
            if self.on_open_callback:
                open_btn = ctk.CTkButton(button_frame, text="📂", width=35, height=28, command=self.on_open)
                open_btn.pack(side="left", padx=2)
            if self.on_retry_callback:
                retry_btn = ctk.CTkButton(button_frame, text="🔄", width=35, height=28, command=self.on_retry)
                retry_btn.pack(side="left", padx=2)

        elif self.task.status == TaskStatus.FAILED:
            if self.on_retry_callback:
                retry_btn = ctk.CTkButton(button_frame, text="🔄", width=35, height=28, command=self.on_retry)
                retry_btn.pack(side="left", padx=2)
            if self.on_delete_callback:
                delete_btn = ctk.CTkButton(button_frame, text="🗑️", width=35, height=28, command=self.on_delete)
                delete_btn.pack(side="left", padx=2)

    def update_task(self, task: Task):
        self.task = task
        self.status_label.configure(text=self.task.status_text)
        for widget in self.winfo_children():
            widget.destroy()
        self.setup_ui()

    def on_retry(self):
        if self.on_retry_callback:
            self.on_retry_callback(self.task.id)

    def on_delete(self):
        if self.on_delete_callback:
            self.on_delete_callback(self.task.id)

    def on_open(self):
        if self.on_open_callback:
            self.on_open_callback(self.task.id)

class BilibiliSubtitleApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Bilibili 字幕提取工具")
        self.geometry("900x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.tasks = {}
        self.task_frames = {}
        self.input_callback = None
        self.settings_callback = None
        self.cookie_callback = None
        self.start_callback = None
        self.stop_callback = None
        self.retry_callback = None
        self.clear_callback = None
        self.settings = {}
        self._input_lock = False

        self.setup_ui()

    def setup_ui(self):
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self, height=60)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(header_frame, text="Bilibili 字幕提取工具", font=("", 18, "bold"))
        title_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        settings_btn = ctk.CTkButton(header_frame, text="⚙️ 设置", width=80, command=self.on_settings_click)
        settings_btn.grid(row=0, column=1, padx=10, pady=10)

        status_frame = ctk.CTkFrame(self, height=50)
        status_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        status_frame.grid_columnconfigure(0, weight=1)

        self.env_status_label = ctk.CTkLabel(status_frame, text="⏳ 环境检查中...", font=("", 12))
        self.env_status_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.cookie_btn = ctk.CTkButton(status_frame, text="🔑 更新Cookie", width=100, command=self.on_cookie_click)
        self.cookie_btn.grid(row=0, column=1, padx=10, pady=10)

        self.device_label = ctk.CTkLabel(status_frame, text="设备: 检测中", font=("", 12))
        self.device_label.grid(row=0, column=2, padx=15, pady=10)

        input_frame = ctk.CTkFrame(self, height=60)
        input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(input_frame, placeholder_text="输入 BV号 / 视频链接", height=36)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=10)
        # 绑定回车键，但检查输入框是否有焦点且不为空
        self.input_entry.bind("<Return>", self._on_enter_key)

        add_btn = ctk.CTkButton(input_frame, text="➕ 添加", width=80, height=36, command=self.on_add_click)
        add_btn.grid(row=0, column=1, padx=(5, 5), pady=10)

        paste_btn = ctk.CTkButton(input_frame, text="📋 粘贴", width=80, height=36, command=self.on_paste_click)
        paste_btn.grid(row=0, column=2, padx=(5, 10), pady=10)

        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        scroll_frame = ctk.CTkScrollableFrame(list_frame)
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll_frame.grid_columnconfigure(0, weight=1)

        self.task_container = scroll_frame

        control_frame = ctk.CTkFrame(self, height=50)
        control_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)

        self.start_btn = ctk.CTkButton(control_frame, text="▶ 开始", width=100, command=self.on_start_click, fg_color="#4CAF50")
        self.start_btn.pack(side="left", padx=5)

        stop_btn = ctk.CTkButton(control_frame, text="⏹ 停止全部", width=100, command=self.on_stop_click, fg_color="#f44336")
        stop_btn.pack(side="left", padx=5)

        retry_failed_btn = ctk.CTkButton(control_frame, text="🔄 重试失败", width=100, command=self.on_retry_failed_click)
        retry_failed_btn.pack(side="left", padx=5)

        clear_btn = ctk.CTkButton(control_frame, text="🗑️ 清空", width=100, command=self.on_clear_click, fg_color="gray")
        clear_btn.pack(side="left", padx=5)

        # 日志区域
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=5)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        log_label = ctk.CTkLabel(log_frame, text="运行日志:", font=("", 12, "bold"))
        log_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.log_textbox = ctk.CTkTextbox(log_frame, height=150)
        self.log_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.log_textbox.configure(state="disabled")

    def _on_enter_key(self, event):
        """处理回车键按下事件"""
        # 只有当输入框有焦点时才处理
        if self.focus_get() == self.input_entry:
            self.on_add_click()

    def update_env_status(self, cookie_ok: bool, cuda_ok: bool, dir_ok: bool):
        parts = []
        if cookie_ok:
            parts.append("✅ Cookie有效")
            self.cookie_btn.configure(fg_color="#4CAF50")
        else:
            parts.append("❌ Cookie无效")
            self.cookie_btn.configure(fg_color="#f44336")

        if cuda_ok:
            parts.append("✅ CUDA可用")
        else:
            parts.append("✅ CPU模式")

        if dir_ok:
            parts.append("✅ 输出目录正常")

        self.env_status_label.configure(text=" | ".join(parts))

    def update_device(self, device: str):
        self.device_label.configure(text=f"设备: {device}")

    def on_add_click(self):
        # 如果已加锁，直接返回
        if self._input_lock:
            return
        
        # 先加锁，防止并发
        self._input_lock = True
        
        # 获取并立即清空输入框
        value = self.input_entry.get().strip()
        self.input_entry.delete(0, "end")
        
        # 如果值为空，解锁并返回
        if not value:
            self._input_lock = False
            return
        
        # 执行回调
        if self.input_callback:
            try:
                self.input_callback(value)
            except Exception as e:
                print(f"Error in input callback: {e}")
        
        # 延迟解锁（延长到 1.5 秒，确保网络请求已经开始）
        self.after(1500, lambda: setattr(self, '_input_lock', False))

    def on_paste_click(self):
        try:
            import pyperclip
            text = pyperclip.paste()
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, text)
        except ImportError:
            pass

    def on_settings_click(self):
        if self.settings_callback:
            self.settings_callback()

    def on_cookie_click(self):
        if self.cookie_callback:
            self.cookie_callback()

    def on_start_click(self):
        if self.start_callback:
            self.start_callback()

    def on_stop_click(self):
        if self.stop_callback:
            self.stop_callback()

    def on_retry_failed_click(self):
        if self.retry_callback:
            self.retry_callback()

    def on_clear_click(self):
        if self.clear_callback:
            self.clear_callback()

    def set_input_callback(self, callback: Callable):
        self.input_callback = callback

    def set_settings_callback(self, callback: Callable):
        self.settings_callback = callback

    def set_cookie_callback(self, callback: Callable):
        self.cookie_callback = callback

    def set_start_callback(self, callback: Callable):
        self.start_callback = callback

    def set_stop_callback(self, callback: Callable):
        self.stop_callback = callback

    def set_retry_callback(self, callback: Callable):
        self.retry_callback = callback

    def set_clear_callback(self, callback: Callable):
        self.clear_callback = callback

    def add_task(self, task: Task):
        self.tasks[task.id] = task
        self._refresh_tasks()

    def update_task(self, task_id: str, task: Task):
        self.tasks[task_id] = task
        self._refresh_tasks()

    def remove_task(self, task_id: str):
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._refresh_tasks()

    def clear_all_tasks(self):
        self.tasks.clear()
        self._refresh_tasks()

    def _refresh_tasks(self):
        for widget in self.task_container.winfo_children():
            widget.destroy()

        for task_id, task in self.tasks.items():
            item = TaskItem(
                self.task_container,
                task,
                on_retry_callback=self._on_task_retry if self.retry_callback else None,
                on_delete_callback=self._on_task_delete if self.clear_callback else None,
                on_open_callback=self._on_task_open
            )
            item.pack(fill="x", pady=2)

    def _on_task_retry(self, task_id: str):
        if self.retry_callback:
            self.retry_callback(task_id)

    def _on_task_delete(self, task_id: str):
        self.remove_task(task_id)

    def _on_task_open(self, task_id: str):
        task = self.tasks.get(task_id)
        if task and task.subtitle_path:
            import os
            os.startfile(os.path.dirname(task.subtitle_path))

    def add_log(self, message: str):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def show_cookie_dialog(self, on_save: Callable):
        dialog = CookieDialog(self, on_save)

    def show_settings_dialog(self, settings: dict, on_save: Callable):
        dialog = SettingsDialog(self, settings, on_save)
