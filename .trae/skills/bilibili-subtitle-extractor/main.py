"""
Bilibili 字幕提取工具 - 简化版主入口
"""
import os
import sys
import threading
import time
from pathlib import Path

# 修复 OpenMP 库冲突
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

sys.path.insert(0, str(Path(__file__).parent))

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Callable, Optional
from models import Task, TaskStatus, TranscribeStage


class CookieDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback: Callable):
        super().__init__(parent)
        self.on_save_callback = on_save_callback
        self.title("更新 Cookie")
        self.geometry("500x300")
        self.resizable(False, False)
        self.grab_set()
        
        ctk.CTkLabel(self, text="请粘贴浏览器中的 B站 Cookie 字符串:", font=("", 14)).pack(pady=(20, 10), padx=20)
        
        self.textbox = ctk.CTkTextbox(self, height=120)
        self.textbox.pack(pady=10, padx=20, fill="both", expand=True)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=15, padx=20, fill="x")
        
        self.save_btn = ctk.CTkButton(btn_frame, text="保存并验证", command=self._on_save, fg_color="#4CAF50", width=120)
        self.save_btn.pack(side="left", padx=10, expand=True)
        
        ctk.CTkButton(btn_frame, text="取消", command=self.destroy, fg_color="gray", width=80).pack(side="left", padx=10, expand=True)
        
        self.status_label = ctk.CTkLabel(self, text="", font=("", 12))
        self.status_label.pack(pady=10)
    
    def _on_save(self):
        cookie_str = self.textbox.get("1.0", "end-1c").strip()
        if not cookie_str:
            self.status_label.configure(text="请输入 Cookie", text_color="red")
            return
        self.save_btn.configure(state="disabled", text="验证中...")
        self.status_label.configure(text="正在验证 Cookie...")
        self.on_save_callback(cookie_str, self)
    
    def show_result(self, success: bool, message: str):
        if success:
            self.status_label.configure(text=f"✅ {message}", text_color="green")
            self.after(1500, self.destroy)
        else:
            self.status_label.configure(text=f"❌ {message}", text_color="red")
            self.save_btn.configure(state="normal", text="保存并验证")


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, settings: dict, on_save_callback: Callable):
        super().__init__(parent)
        self.settings = settings
        self.on_save_callback = on_save_callback
        self.title("设置")
        self.geometry("400x300")
        self.grab_set()
        
        frame = ctk.CTkFrame(self)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # 并发数
        ctk.CTkLabel(frame, text="下载并发数:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.concurrency_var = ctk.StringVar(value=str(settings.get("download_concurrency", 3)))
        ctk.CTkOptionMenu(frame, variable=self.concurrency_var, values=["1", "2", "3", "4", "5"], width=100).grid(row=0, column=1, padx=10, pady=10)
        
        # 模型
        ctk.CTkLabel(frame, text="Whisper 模型:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.model_var = ctk.StringVar(value=settings.get("whisper_model", "base"))
        ctk.CTkOptionMenu(frame, variable=self.model_var, values=["tiny", "base", "small", "medium"], width=100).grid(row=1, column=1, padx=10, pady=10)
        
        # 设备
        ctk.CTkLabel(frame, text="计算设备:").grid(row=2, column=0, sticky="w", padx=10, pady=10)
        self.device_var = ctk.StringVar(value=settings.get("whisper_device", "auto"))
        ctk.CTkOptionMenu(frame, variable=self.device_var, values=["auto", "cpu", "cuda"], width=100).grid(row=2, column=1, padx=10, pady=10)
        
        # 删除音频
        self.delete_audio_var = ctk.BooleanVar(value=settings.get("delete_audio_after_transcribe", True))
        ctk.CTkCheckBox(frame, text="转录后删除临时音频", variable=self.delete_audio_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=10)
        
        ctk.CTkButton(self, text="保存设置", command=self._save, fg_color="#4CAF50", width=150).pack(pady=15)
    
    def _save(self):
        new_settings = {
            "download_concurrency": int(self.concurrency_var.get()),
            "whisper_model": self.model_var.get(),
            "whisper_device": self.device_var.get(),
            "delete_audio_after_transcribe": self.delete_audio_var.get(),
        }
        self.on_save_callback(new_settings)
        self.destroy()


class TaskItemFrame(ctk.CTkFrame):
    def __init__(self, master, task: Task):
        super().__init__(master, fg_color=("gray85", "gray25"))
        self.task = task
        self._create_widgets()
    
    def _create_widgets(self):
        self.grid_columnconfigure(1, weight=1)
        
        # 状态图标
        icon_map = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.DOWNLOADING: "📥",
            TaskStatus.TRANSCRIBING: "🎙️",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.STOPPED: "⏹️"
        }
        icon = icon_map.get(self.task.status, "📺")
        ctk.CTkLabel(self, text=icon, font=("", 18)).grid(row=0, column=0, rowspan=2, padx=10, pady=8)
        
        # 标题
        title = f"{self.task.video_info.title} - {self.task.video_info.up主}"
        ctk.CTkLabel(self, text=title, font=("", 12), anchor="w").grid(row=0, column=1, sticky="w", padx=5, pady=(8, 2))
        
        # 状态
        ctk.CTkLabel(self, text=self.task.status_text, font=("", 11), text_color="gray", anchor="w").grid(row=1, column=1, sticky="w", padx=5, pady=(0, 8))
    
    def update_task(self, task: Task):
        self.task = task
        for widget in self.winfo_children():
            widget.destroy()
        self._create_widgets()


class BilibiliSubtitleApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Bilibili 字幕提取工具")
        self.geometry("850x650")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.tasks = {}
        self.task_frames = {}
        self.controller = None
        self._input_locked = False
        
        self._create_ui()
        self._init_controller()
    
    def _create_ui(self):
        # 主布局
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # === 顶部：标题和状态 ===
        top_frame = ctk.CTkFrame(self, height=50)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(top_frame, text="Bilibili 字幕提取工具", font=("", 16, "bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        self.status_label = ctk.CTkLabel(top_frame, text="检查环境中...", font=("", 11))
        self.status_label.grid(row=0, column=1, padx=10, pady=10)
        
        self.cookie_btn = ctk.CTkButton(top_frame, text="Cookie", width=80, command=self._on_cookie_click)
        self.cookie_btn.grid(row=0, column=2, padx=5, pady=10)
        
        ctk.CTkButton(top_frame, text="设置", width=60, command=self._on_settings_click).grid(row=0, column=3, padx=5, pady=10)
        
        # === 输入区域 ===
        input_frame = ctk.CTkFrame(self, height=50)
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.input_entry = ctk.CTkEntry(input_frame, placeholder_text="输入 BV号 或 视频链接", height=36)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=10)
        self.input_entry.bind("<Return>", lambda e: self._on_add_click())
        
        ctk.CTkButton(input_frame, text="添加", width=70, height=36, command=self._on_add_click).grid(row=0, column=1, padx=5, pady=10)
        ctk.CTkButton(input_frame, text="粘贴", width=60, height=36, command=self._on_paste_click).grid(row=0, column=2, padx=(5, 10), pady=10)
        
        # === 任务列表 ===
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        self.task_container = ctk.CTkScrollableFrame(list_frame)
        self.task_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.task_container.grid_columnconfigure(0, weight=1)
        
        # === 控制按钮 ===
        btn_frame = ctk.CTkFrame(self, height=45)
        btn_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        
        self.start_btn = ctk.CTkButton(btn_frame, text="▶ 开始", width=90, command=self._on_start_click, fg_color="#4CAF50")
        self.start_btn.pack(side="left", padx=8, pady=8)
        
        ctk.CTkButton(btn_frame, text="⏹ 停止", width=80, command=self._on_stop_click, fg_color="#f44336").pack(side="left", padx=8, pady=8)
        ctk.CTkButton(btn_frame, text="🔄 重试", width=80, command=self._on_retry_click).pack(side="left", padx=8, pady=8)
        ctk.CTkButton(btn_frame, text="🗑 清空", width=80, command=self._on_clear_click, fg_color="gray").pack(side="left", padx=8, pady=8)
        
        # === 日志区域 ===
        log_frame = ctk.CTkFrame(self, height=100)
        log_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(log_frame, text="日志:", anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.log_text = ctk.CTkTextbox(log_frame, height=80, font=("Consolas", 10))
        self.log_text.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.log_text.configure(state="disabled")
    
    def _init_controller(self):
        """初始化控制器"""
        from controller import Controller
        from services import config, load_cookies, verify_cookie
        import asyncio
        
        self.controller = Controller()
        self.controller.set_app(self)
        self.controller.load_settings()
        
        # 检查环境
        def check_env():
            # 检查 CUDA
            try:
                import torch
                cuda_ok = torch.cuda.is_available()
            except:
                cuda_ok = False
            
            # 检查 Cookie
            cookies = load_cookies()
            cookie_ok = False
            if cookies:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    cookie_ok, _ = loop.run_until_complete(verify_cookie(cookies))
                    loop.close()
                except:
                    pass
            
            # 更新 UI
            status = []
            status.append("✅ Cookie" if cookie_ok else "❌ Cookie")
            status.append("✅ CUDA" if cuda_ok else "CPU模式")
            self.after(0, lambda: self.status_label.configure(text=" | ".join(status)))
            self.after(0, lambda: self.cookie_btn.configure(fg_color="#4CAF50" if cookie_ok else "#f44336"))
            self.after(0, lambda: self.add_log("环境检查完成"))
        
        threading.Thread(target=check_env, daemon=True).start()
        
        # 启动日志轮询
        self._poll_logs()
    
    def _poll_logs(self):
        """轮询日志"""
        from services import user_log
        if not hasattr(self, '_last_log_idx'):
            self._last_log_idx = 0
        
        logs = user_log.get_all()
        if len(logs) > self._last_log_idx:
            for log in logs[self._last_log_idx:]:
                self.add_log(log['message'])
            self._last_log_idx = len(logs)
        
        self.after(300, self._poll_logs)
    
    def _on_add_click(self):
        """添加视频"""
        if self._input_locked:
            return
        
        value = self.input_entry.get().strip()
        if not value:
            return
        
        self._input_locked = True
        self.input_entry.delete(0, "end")
        
        if self.controller:
            self.controller.add_input(value)
        
        self.after(1000, self._unlock_input)
    
    def _unlock_input(self):
        self._input_locked = False
    
    def _on_paste_click(self):
        try:
            import pyperclip
            text = pyperclip.paste()
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, text)
        except:
            pass
    
    def _on_start_click(self):
        if self.controller:
            self.controller.start()
            self.controller.start_processing()
            self.add_log("开始处理任务...")
    
    def _on_stop_click(self):
        if self.controller:
            self.controller.stop()
            self.add_log("已停止所有任务")
    
    def _on_retry_click(self):
        if self.controller:
            self.controller.retry_failed()
    
    def _on_clear_click(self):
        if self.controller:
            self.controller.clear_completed()
    
    def _on_cookie_click(self):
        def on_save(cookie_str, dialog):
            from services.cookie_manager import parse_cookie_string, save_cookies, verify_cookie
            import asyncio
            
            def verify():
                try:
                    cookies = parse_cookie_string(cookie_str)
                    save_cookies(cookies)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    ok, msg = loop.run_until_complete(verify_cookie(cookies))
                    loop.close()
                    self.after(0, lambda: dialog.show_result(ok, msg if ok else f"验证失败: {msg}"))
                    if ok:
                        self.after(0, lambda: self.cookie_btn.configure(fg_color="#4CAF50"))
                except Exception as e:
                    self.after(0, lambda: dialog.show_result(False, str(e)))
            
            threading.Thread(target=verify, daemon=True).start()
        
        CookieDialog(self, on_save)
    
    def _on_settings_click(self):
        if not self.controller:
            return
        
        def on_save(settings):
            self.controller.settings = settings
            from services import config
            config.save_settings(settings)
            self.add_log("设置已保存")
        
        SettingsDialog(self, self.controller.settings, on_save)
    
    # === 公共接口 ===
    def add_log(self, message: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def add_task(self, task: Task):
        frame = TaskItemFrame(self.task_container, task)
        frame.grid(row=len(self.task_frames), column=0, sticky="ew", padx=5, pady=3)
        self.task_frames[task.id] = frame
        self.tasks[task.id] = task
    
    def update_task(self, task_id: str, task: Task):
        self.tasks[task.id] = task
        if task_id in self.task_frames:
            self.task_frames[task_id].update_task(task)
    
    def remove_task(self, task_id: str):
        if task_id in self.task_frames:
            self.task_frames[task_id].destroy()
            del self.task_frames[task_id]
        if task_id in self.tasks:
            del self.tasks[task_id]
    
    def update_env_status(self, cookie_ok: bool, cuda_ok: bool, dir_ok: bool):
        pass
    
    def update_device(self, device: str):
        pass


def main():
    app = BilibiliSubtitleApp()
    app.mainloop()


if __name__ == "__main__":
    main()
