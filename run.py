#!/usr/bin/env python3
"""
Browser Use 最小示例。
- CDP：设 CDP_URL（默认 http://127.0.0.1:9222）则连接本机 Chromium；未设则 headless 自起。9222 未开可执行 ~/.vnc/start-chromium.sh；AUTO_START_CHROMIUM=1 可自动执行该脚本，CDP_POST_START_DELAY 秒后再跑 Agent。
- LLM：OPENAI_BASE_URL + OPENAI_API_KEY，默认 model=jyj.cx/flash:or。
- 任务：BROWSER_USE_CASE=0|1|2|3|4 选单 case，all 跑 0–4 并汇总。
- 兼容：compat 层统一处理非流式与 action JSON 规范化（click 整数→对象、wait.time→seconds）。
"""
import asyncio

from dotenv import load_dotenv

load_dotenv()

import compat  # noqa: E402 — 先应用补丁再使用 LLM/Agent
from runner import main

if __name__ == "__main__":
    asyncio.run(main())
