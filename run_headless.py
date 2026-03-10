#!/usr/bin/env python3
"""
Browser Use 最小示例。
- 优先使用已有 CDP：设 CDP_URL（默认 http://127.0.0.1:9222）则连接本机已启动的 Chromium，不自行起浏览器。
- 未设 CDP_URL 时用 Browser(headless=True) 自起浏览器（需 Chromium 可启动，如 chromium_sandbox=False）。
LLM：OPENAI_BASE_URL + OPENAI_API_KEY，默认 model=jyj.cx/flash:or。
多 case：BROWSER_USE_CASE=0|1|2|3|4 选择任务（0 最简单，4 最难），默认 0。
全量测试：BROWSER_USE_CASE=all 依次跑 0–4 并汇总通过/失败。

兼容 jyj.cx/flash:or 等模型：解析前规范化 action JSON——
  - "click": <int> → "click": {"index": <int>}；
  - "wait": {"time": N} → "wait": {"seconds": N}（库要求 seconds 而非 time）。
"""
# 强制非流式：避免网关/代理返回流式或非标准体导致 response 变成 str，从而报 'str' object has no attribute 'choices'
from openai.resources.chat.completions import AsyncCompletions

_orig_async_create = AsyncCompletions.create


async def _create_no_stream(self, *args, **kwargs):
    kwargs["stream"] = False
    return await _orig_async_create(self, *args, **kwargs)


AsyncCompletions.create = _create_no_stream

# 规范化 Agent 输出 JSON：click 整数→对象、wait.time→wait.seconds
import json
from pydantic import BaseModel

_orig_model_validate_json = BaseModel.model_validate_json


def _normalize_agent_action_item(item: dict) -> None:
    if not isinstance(item, dict):
        return
    if "click" in item and isinstance(item["click"], int):
        item["click"] = {"index": item["click"]}
    if "wait" in item and isinstance(item["wait"], dict) and "time" in item["wait"]:
        item["wait"]["seconds"] = item["wait"].pop("time")


def _model_validate_json_with_click_fix(cls, s: str):
    if isinstance(s, str):
        try:
            data = json.loads(s)
            if isinstance(data.get("action"), list):
                for item in data["action"]:
                    _normalize_agent_action_item(item)
                s = json.dumps(data)
        except Exception:
            pass
    return _orig_model_validate_json.__func__(cls, s)


BaseModel.model_validate_json = classmethod(_model_validate_json_with_click_fix)

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

# Case 0=简单，1–4=逐步复杂；通过 BROWSER_USE_CASE=1 等选择
TASKS = [
    "Open https://example.com and return the page title.",
    "Open https://example.com, click the 'More information' link, then return the first heading (h1 or main title) on the new page.",
    "Open https://duckduckgo.com, type 'Browser automation' in the search box and submit, then return the title of the first search result.",
    "Open https://httpbin.org/forms/post, fill in the 'Customer name' field with 'TestUser', and tell me the exact text on the submit button.",
    "Open https://en.wikipedia.org, use the search box to search for 'Python (programming language)', open the article, and return the first sentence of the first paragraph.",
]

async def run_one_case(
    case_idx: int,
    llm,
    cdp_url: str,
) -> bool:
    """跑单个 case，返回是否成功。"""
    from browser_use import Agent, BrowserSession

    task = TASKS[case_idx % len(TASKS)]
    print(f"\n{'='*60}\nCase {case_idx}: {task[:70]}{'...' if len(task) > 70 else ''}\n{'='*60}")
    session = BrowserSession(cdp_url=cdp_url)
    agent = Agent(task=task, llm=llm, browser_session=session)
    try:
        history = await agent.run(max_steps=15)
        last_result = history.history[-1].result if history.history else []
        ok = bool(last_result) and getattr(last_result[0], "success", False)
        if history.history:
            last = history.history[-1]
            content = getattr(last.result[0], "extracted_content", None) or str(last)[:200]
            print(f"Result: {content}")
        print(f"Case {case_idx}: {'PASS' if ok else 'FAIL'}")
        return ok
    except Exception as e:
        print(f"Case {case_idx}: FAIL - {e}")
        return False


async def main() -> None:
    from browser_use import BrowserSession, ChatOpenAI

    base_url = os.getenv("OPENAI_BASE_URL", "https://dj.jyj.cx/v1")
    api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(
        model=os.getenv("BROWSER_USE_LLM_MODEL", "jyj.cx/flash:or"),
        api_key=api_key,
        base_url=base_url or None,
    )
    if base_url and not api_key:
        print("Warning: OPENAI_BASE_URL set but OPENAI_API_KEY empty, may fail.")

    cdp_url = os.getenv("CDP_URL", "http://127.0.0.1:9222").strip()
    case_env = os.getenv("BROWSER_USE_CASE", "0").strip().lower()

    if case_env == "all":
        # 全量测试：依次跑 0–4，最后汇总
        results = []
        for i in range(len(TASKS)):
            ok = await run_one_case(i, llm, cdp_url)
            results.append((i, ok))
        passed = sum(1 for _, ok in results if ok)
        print(f"\n{'='*60}\nTotal: {passed}/{len(TASKS)} passed")
        for i, ok in results:
            print(f"  Case {i}: {'PASS' if ok else 'FAIL'}")
        if passed < len(TASKS):
            raise SystemExit(1)
        return

    case_idx = int(case_env) if case_env.isdigit() else 0
    await run_one_case(case_idx, llm, cdp_url)


if __name__ == "__main__":
    asyncio.run(main())
