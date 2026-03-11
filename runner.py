"""单 case 与 main 入口逻辑。"""
import asyncio
import os
import sys
import time

from browser_use import Agent, BrowserSession, ChatOpenAI

from config import CDP_POST_START_DELAY, TASKS
from cdp import ensure_cdp_ready


async def run_one_case(case_idx: int, llm, cdp_url: str) -> bool:
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
    just_started = ensure_cdp_ready(cdp_url)
    if just_started and CDP_POST_START_DELAY > 0:
        print(f"等待 {CDP_POST_START_DELAY}s 让浏览器稳定后再跑 Agent ...", file=sys.stderr)
        time.sleep(CDP_POST_START_DELAY)

    case_env = os.getenv("BROWSER_USE_CASE", "0").strip().lower()
    if case_env == "all":
        results = [(i, await run_one_case(i, llm, cdp_url)) for i in range(len(TASKS))]
        passed = sum(1 for _, ok in results if ok)
        print(f"\n{'='*60}\nTotal: {passed}/{len(TASKS)} passed")
        for i, ok in results:
            print(f"  Case {i}: {'PASS' if ok else 'FAIL'}")
        if passed < len(TASKS):
            raise SystemExit(1)
        return
    case_idx = int(case_env) if case_env.isdigit() else 0
    await run_one_case(case_idx, llm, cdp_url)
