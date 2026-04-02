from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
SERVER_SCRIPT = ROOT_DIR / "stitch" / "biliglass_pro" / "server.py"
CONSOLE_PATH = "/_2/code.html"


def stream_output(process: subprocess.Popen, port_holder: dict[str, int | None]):
    port_pattern = re.compile(r"http://127\.0\.0\.1:(\d+)")

    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="")
        match = port_pattern.search(line)
        if match and port_holder.get("port") is None:
            port_holder["port"] = int(match.group(1))


def main() -> int:
    if not SERVER_SCRIPT.exists():
        print(f"找不到后端脚本: {SERVER_SCRIPT}")
        return 1

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    process = subprocess.Popen(
        [sys.executable, str(SERVER_SCRIPT)],
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )

    port_holder: dict[str, int | None] = {"port": None}
    output_thread = threading.Thread(target=stream_output, args=(process, port_holder), daemon=True)
    output_thread.start()

    browser_opened = False
    waited = 0.0
    while process.poll() is None:
        port = port_holder.get("port")
        if port and not browser_opened:
            url = f"http://127.0.0.1:{port}{CONSOLE_PATH}"
            webbrowser.open(url)
            print(f"已打开浏览器: {url}")
            browser_opened = True
        if not browser_opened:
            time.sleep(0.2)
            waited += 0.2
            if waited > 10:
                print("后端已启动，但未及时拿到端口信息。请查看控制台输出。")
                browser_opened = True
        else:
            time.sleep(0.5)

    output_thread.join(timeout=2)
    return process.returncode or 0


if __name__ == "__main__":
    raise SystemExit(main())
