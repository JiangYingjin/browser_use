"""通用工具：run_id 与分层日志目录（对齐 agent headless 的 YYYY/MM/DD/time_part 结构）。"""
import os
from datetime import datetime


def make_runid(base: str = "outputs/runs") -> tuple[str, str]:
    """生成当前时刻的 run_id 及对应分层目录路径。

    Returns:
        (run_id, run_dir)，例如 ("20260311_172224", "outputs/runs/2026/03/11/172224")。
    """
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    year, month, day = run_id[:4], run_id[4:6], run_id[6:8]
    time_part = run_id.split("_", 1)[1]
    run_dir = os.path.join(base, year, month, day, time_part)
    return run_id, run_dir
