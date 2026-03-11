"""CDP 不可达时执行启动脚本并等待。"""

import os
import subprocess
import sys
import time
from urllib.parse import urlparse

from config import CDP_READY_TIMEOUT, CDP_URL, START_CHROMIUM_SCRIPT


def _ready(host: str, port: int) -> bool:
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://{host}:{port}/json/version", timeout=3):
            return True
    except Exception:
        return False


def ensure_cdp_ready(cdp_url: str = CDP_URL) -> bool:
    parsed = urlparse(cdp_url)
    host, port = parsed.hostname, parsed.port
    if _ready(host, port):
        return False
    if os.path.isfile(START_CHROMIUM_SCRIPT):
        print(
            f"CDP {host}:{port} 未就绪，执行 {START_CHROMIUM_SCRIPT} ...",
            file=sys.stderr,
        )
        subprocess.Popen(
            [START_CHROMIUM_SCRIPT],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(CDP_READY_TIMEOUT):
            if _ready(host, port):
                print("CDP 已就绪。", file=sys.stderr)
                return True
            time.sleep(1)
        print(f"等待 CDP 超时（{CDP_READY_TIMEOUT}s）。", file=sys.stderr)
    print(f"无法连接 CDP {cdp_url}，可执行: {START_CHROMIUM_SCRIPT}", file=sys.stderr)
    sys.exit(1)
