#!/usr/bin/env python3
"""Browser Use 最小示例：CDP 连本机 Chromium（可自动起）、LLM 调 jyj.cx/flash:or，跑单 case 或全量。"""
import asyncio
import sys
import time

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

TASKS = [
    "打开 https://example.com 并返回页面标题。",
    "打开 https://example.com，点击“More information”链接，然后返回新页面的第一个标题（h1 或主标题）。",
    "打开 https://duckduckgo.com，在搜索框输入“Browser automation”并提交，然后返回第一个搜索结果的标题。",
    "打开 https://httpbin.org/forms/post，在“Customer name”字段填写“TestUser”，告诉我提交按钮上准确的文字内容。",
    "打开 https://en.wikipedia.org，使用搜索框搜索“Python (programming language)”，打开文章，并返回第一段第一句。",
]


async def run_one(task: str, llm, cdp_url: str = CDP_URL) -> bool:
    """传入提示词文本，跑一次 Agent，返回是否成功。"""
    print(f"\n{'='*60}\nTask: {task[:70]}{'...' if len(task) > 70 else ''}\n{'='*60}")
    session = BrowserSession(cdp_url=cdp_url)
    agent = Agent(task=task, llm=llm, browser_session=session)
    try:
        history = await agent.run(max_steps=15)
        last = history.history[-1] if history.history else None
        ok = bool(last and last.result and getattr(last.result[0], "success", False))
        if last and last.result:
            print(
                "Result:",
                getattr(last.result[0], "extracted_content", None) or str(last)[:200],
            )
        print("PASS" if ok else "FAIL")
        return ok
    except Exception as e:
        print(f"FAIL - {e}")
        return False


async def main():
    llm = ChatOpenAI(
        model=BROWSER_USE_LLM_MODEL, api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL
    )
    if ensure_cdp_ready():
        print(f"等待 5s 让浏览器稳定 ...", file=sys.stderr)
        time.sleep(5)

    results = [(i, await run_one(TASKS[i], llm)) for i in range(len(TASKS))]

    passed = sum(1 for _, ok in results if ok)
    print(f"\n{'='*60}\nTotal: {passed}/{len(TASKS)} passed")
    for i, ok in results:
        print(f"  Case {i}: {'PASS' if ok else 'FAIL'}")
    raise SystemExit(1 if passed < len(TASKS) else 0)


if __name__ == "__main__":
    asyncio.run(main())
