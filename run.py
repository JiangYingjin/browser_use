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
    CASE_INDEX,
    CDP_POST_START_DELAY,
    CDP_URL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    BROWSER_USE_LLM_MODEL,
    RUN_ALL,
    TASKS,
)
from cdp import ensure_cdp_ready


async def run_one(case_idx: int, llm, cdp_url: str) -> bool:
    task = TASKS[case_idx % len(TASKS)]
    print(
        f"\n{'='*60}\nCase {case_idx}: {task[:70]}{'...' if len(task) > 70 else ''}\n{'='*60}"
    )
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
        print(f"Case {case_idx}: {'PASS' if ok else 'FAIL'}")
        return ok
    except Exception as e:
        print(f"Case {case_idx}: FAIL - {e}")
        return False


async def main():
    llm = ChatOpenAI(
        model=BROWSER_USE_LLM_MODEL, api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL
    )
    just_started = ensure_cdp_ready()
    if just_started and CDP_POST_START_DELAY > 0:
        print(f"等待 {CDP_POST_START_DELAY}s 让浏览器稳定 ...", file=sys.stderr)
        time.sleep(CDP_POST_START_DELAY)
    if RUN_ALL:
        results = [(i, await run_one(i, llm, CDP_URL)) for i in range(len(TASKS))]
        passed = sum(1 for _, ok in results if ok)
        print(f"\n{'='*60}\nTotal: {passed}/{len(TASKS)} passed")
        for i, ok in results:
            print(f"  Case {i}: {'PASS' if ok else 'FAIL'}")
        raise SystemExit(1 if passed < len(TASKS) else 0)
    await run_one(CASE_INDEX, llm, CDP_URL)


if __name__ == "__main__":
    asyncio.run(main())
