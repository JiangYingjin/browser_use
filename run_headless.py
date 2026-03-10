#!/usr/bin/env python3
"""
Browser Use 最小示例。
- 优先使用已有 CDP：设 CDP_URL（默认 http://127.0.0.1:9222）则连接本机已启动的 Chromium，不自行起浏览器。
- 未设 CDP_URL 时用 Browser(headless=True) 自起浏览器（需 Chromium 可启动，如 chromium_sandbox=False）。
LLM：OPENAI_API_KEY + OPENAI_BASE_URL，默认 model=jyj.cx/flash:or。
"""
# 强制非流式：避免网关/代理返回流式或非标准体导致 response 变成 str，从而报 'str' object has no attribute 'choices'
from openai.resources.chat.completions import AsyncCompletions

_orig_async_create = AsyncCompletions.create


async def _create_no_stream(self, *args, **kwargs):
    kwargs["stream"] = False
    return await _orig_async_create(self, *args, **kwargs)


AsyncCompletions.create = _create_no_stream

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    from browser_use import Agent, Browser, BrowserSession, ChatOpenAI

    # LLM：OpenAI 兼容端点，默认 dj.jyj.cx/v1 + jyj.cx/flash:or
    base_url = os.getenv("OPENAI_BASE_URL", "https://dj.jyj.cx/v1")
    api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(
        model=os.getenv("BROWSER_USE_LLM_MODEL", "jyj.cx/flash:or"),
        api_key=api_key,
        base_url=base_url or None,
    )
    if base_url and not api_key:
        print("Warning: OPENAI_BASE_URL set but OPENAI_API_KEY empty, may fail.")

    # 使用已有 CDP：本机先起 Chromium（如 --remote-debugging-port=9222），再跑本脚本
    cdp_url = os.getenv("CDP_URL", "http://127.0.0.1:9222").strip()
    session = BrowserSession(cdp_url=cdp_url)
    agent = Agent(
        task="Open https://example.com and return the page title.",
        llm=llm,
        browser_session=session,
    )

    history = await agent.run(max_steps=10)
    print("History length:", len(history))
    if history.history:
        last = history.history[-1]
        print(
            "Last step result (excerpt):",
            str(last) if hasattr(last, "__str__") else last,
        )


if __name__ == "__main__":
    asyncio.run(main())
