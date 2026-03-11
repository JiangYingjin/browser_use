"""CDP 就绪检测与可选自动启动 Chromium。"""
import os
import subprocess
import sys
import time
from urllib.parse import urlparse

from config import CDP_READY_TIMEOUT, DEFAULT_START_CHROMIUM_SCRIPT


def _cdp_port_ready(host: str, port: int) -> bool:
    try:
        import urllib.request
        req = urllib.request.Request(f"http://{host}:{port}/json/version", method="GET")
        with urllib.request.urlopen(req, timeout=3):
            return True
    except Exception:
        return False


def ensure_cdp_ready(cdp_url: str) -> bool:
    """
    若 CDP 不可达且 AUTO_START_CHROMIUM=1，则执行 START_CHROMIUM_SCRIPT 并等待就绪；
    否则不可达时打印提示并 exit(1)。返回 True 表示本次由脚本启动了浏览器。
    """
    parsed = urlparse(cdp_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 9222
    if _cdp_port_ready(host, port):
        return False
    script = os.getenv("START_CHROMIUM_SCRIPT", DEFAULT_START_CHROMIUM_SCRIPT).strip()
    auto = os.getenv("AUTO_START_CHROMIUM", "1").strip().lower() in ("1", "true", "yes")
    if auto and script and os.path.isfile(script):
        print(f"CDP {host}:{port} 未就绪，正在执行 {script} ...", file=sys.stderr)
        subprocess.Popen(
            [script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
        )
        for _ in range(CDP_READY_TIMEOUT):
            if _cdp_port_ready(host, port):
                print("CDP 已就绪。", file=sys.stderr)
                return True
            time.sleep(1)
        print(f"等待 CDP 超时（{CDP_READY_TIMEOUT}s）。", file=sys.stderr)
    print(f"无法连接 CDP {cdp_url}，可执行: {DEFAULT_START_CHROMIUM_SCRIPT}", file=sys.stderr)
    sys.exit(1)
