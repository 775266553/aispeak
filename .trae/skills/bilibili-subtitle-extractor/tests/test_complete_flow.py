"""
完整流程测试 - 包括模型下载和转录
"""
import sys
import threading
import time
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from controller import Controller
from models import Task, TaskStatus
from services import config, load_cookies


class MockApp:
    def __init__(self):
        self.logs = []
        self.tasks = {}

    def add_log(self, msg):
        self.logs.append(msg)
        print(f"[LOG] {msg}")

    def add_task(self, task):
        self.tasks[task.id] = task
        print(f"[UI] 添加任务: {task.video_info.title}")

    def update_task(self, task_id, task):
        self.tasks[task_id] = task
        status_map = {
            TaskStatus.PENDING: "⏳ 等待中",
            TaskStatus.DOWNLOADING: "📥 下载中",
            TaskStatus.TRANSCRIBING: "🎙️ 转录中",
            TaskStatus.COMPLETED: "✅ 已完成",
            TaskStatus.FAILED: "❌ 失败",
            TaskStatus.STOPPED: "⏹️ 已停止"
        }
        status_str = status_map.get(task.status, str(task.status))
        progress = f" {task.progress:.0f}%" if task.progress > 0 else ""
        print(f"[UI] {status_str}{progress} - {task.video_info.title}")

    def remove_task(self, task_id):
        if task_id in self.tasks:
            del self.tasks[task_id]

    def after(self, ms, callback):
        def run():
            time.sleep(ms/1000)
            callback()
        threading.Thread(target=run, daemon=True).start()


def test_complete():
    print("="*70)
    print(" Bilibili 字幕提取工具 - 完整流程测试")
    print(" (包括模型下载，预计需要 3-10 分钟)")
    print("="*70)

    # 初始化
    print("\n[1/5] 初始化...")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.temp_audio_dir.mkdir(parents=True, exist_ok=True)
    config.subtitles_dir.mkdir(parents=True, exist_ok=True)
    
    cookies = load_cookies()
    print(f"  Cookie: {'✅ 已加载' if cookies else '❌ 未找到'}")

    # 创建 Controller
    controller = Controller()
    app = MockApp()
    controller.set_app(app)
    controller.load_settings()
    print("  Controller: ✅ 已创建")

    # 添加视频
    print("\n[2/5] 添加视频...")
    controller.add_input("BV1Pho9YrEre")
    time.sleep(3)
    print(f"  任务数: {len(controller.tasks)}")

    # 启动处理
    print("\n[3/5] 启动处理...")
    controller.start()
    controller.start_processing()
    print("  Controller: ✅ 已启动")

    # 监控进度
    print("\n[4/5] 监控进度 (按 Ctrl+C 可中断)...")
    print("-"*70)
    
    start_time = time.time()
    last_status = None
    
    try:
        while True:
            for task in controller.tasks.values():
                current = (task.status, task.progress)
                if current != last_status:
                    last_status = current
                    elapsed = time.time() - start_time
                    print(f"[{elapsed:5.1f}s] {task.status.value:6s} {task.progress:5.1f}% | {task.video_info.title[:40]}")

                if task.status == TaskStatus.COMPLETED:
                    print("-"*70)
                    print(f"\n✅ 任务完成!")
                    print(f"   音频: {task.audio_path}")
                    print(f"   字幕: {task.subtitle_path}")
                    if task.subtitle_path and Path(task.subtitle_path).exists():
                        content = Path(task.subtitle_path).read_text(encoding='utf-8')
                        print(f"   字幕长度: {len(content)} 字符")
                        print(f"   前200字:\n   {content[:200]}...")
                    return True

                if task.status == TaskStatus.FAILED:
                    print("-"*70)
                    print(f"\n❌ 任务失败: {task.error_msg}")
                    return False

            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n用户中断")
        return False
    finally:
        # 停止
        print("\n[5/5] 停止 Controller...")
        controller.stop()
        print("  Controller: ✅ 已停止")

    return False


if __name__ == "__main__":
    try:
        success = test_complete()
        print("\n" + "="*70)
        if success:
            print(" 测试结果: ✅ 通过")
        else:
            print(" 测试结果: ❌ 未通过")
        print("="*70)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
