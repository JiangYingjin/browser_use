#!/usr/bin/env python3
"""Browser Use 最小示例：CDP 连本机 Chromium（可自动起）、LLM 调 jyj.cx/flash:or，跑单 case 或全量。"""
import asyncio
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import compat  # noqa: E402
from utils import make_runid
from browser_use import Agent, BrowserSession, ChatOpenAI
from tools_with_region_html import ToolsWithRegionHtml
from config import (
    CDP_URL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    BROWSER_USE_LLM_MODEL,
)
from cdp import ensure_cdp_ready


async def run_one(task: str) -> str | None:
    if ensure_cdp_ready():
        print(f"等待 5s 让浏览器稳定 ...", file=sys.stderr)
        time.sleep(5)

    browser_session = BrowserSession(cdp_url=CDP_URL)
    llm = ChatOpenAI(
        model=BROWSER_USE_LLM_MODEL,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
    )
    agent = Agent(
        task=task,
        llm=llm,
        browser_session=browser_session,
        tools=ToolsWithRegionHtml(),
    )

    history = await agent.run()

    _, run_dir = make_runid()
    d = Path(run_dir)
    d.mkdir(parents=True, exist_ok=True)

    history_path = d / "history.json"
    history_path.write_text(
        json.dumps(history.model_dump(), ensure_ascii=False, indent=2),
    )

    last = history.history[-1] if history.history else None
    result = (
        getattr(last.result[0], "extracted_content", None)
        if last and last.result
        else None
    )
    if result:
        result_path = d / "result.txt"
        result_path.write_text(result)
        print(f"Result saved to {result_path}")
    return result


async def main():
    if len(sys.argv) > 1:
        task = sys.argv[1]
        await run_one(task)


if __name__ == "__main__":
    asyncio.run(main())
