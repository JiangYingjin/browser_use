#!/usr/bin/env python3
"""Browser Use 最小示例：CDP 连本机 Chromium（可自动起）、LLM 调 jyj.cx/flash:or，跑单 case 或全量。"""
import asyncio
import sys
import time
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import compat  # noqa: E402
from browser_use import Agent, BrowserSession, ChatOpenAI
from config import (
    CDP_URL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    BROWSER_USE_LLM_MODEL,
)
from cdp import ensure_cdp_ready


async def run_one(task: str) -> bool:
    if ensure_cdp_ready():
        print(f"等待 5s 让浏览器稳定 ...", file=sys.stderr)
        time.sleep(5)

    browser_session = BrowserSession(cdp_url=CDP_URL)
    llm = ChatOpenAI(
        model=BROWSER_USE_LLM_MODEL,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
    )
    agent = Agent(task=task, llm=llm, browser_session=browser_session)
    history = await agent.run()

    # 创建输出目录
    os.makedirs("outputs/history", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"outputs/history/{timestamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(history.model_dump(), f, ensure_ascii=False, indent=2)
    print(f"History saved to {out_path}")

    last = history.history[-1] if history.history else None
    ok = bool(last and last.result and getattr(last.result[0], "success", False))
    if last and last.result:
        extracted_content = getattr(last.result[0], "extracted_content", None) or str(
            last
        )
        # print("Result:", extracted_content)
        os.makedirs("outputs/results", exist_ok=True)
        with open(f"outputs/results/{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write(extracted_content)
    return extracted_content


async def main():
    if len(sys.argv) > 1:
        task = sys.argv[1]
        await run_one(task)


if __name__ == "__main__":
    asyncio.run(main())
