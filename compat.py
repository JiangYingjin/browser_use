"""兼容：强制非流式 LLM、规范化 action JSON（click 整数→对象、wait.time→seconds）。"""

import json
from openai.resources.chat.completions import AsyncCompletions
from pydantic import BaseModel

_orig_create = AsyncCompletions.create


async def _no_stream(self, *args, **kwargs):
    kwargs["stream"] = False
    return await _orig_create(self, *args, **kwargs)


AsyncCompletions.create = _no_stream

_orig_validate = BaseModel.model_validate_json


def _norm(item: dict):
    if not isinstance(item, dict):
        return
    if "click" in item and isinstance(item["click"], int):
        item["click"] = {"index": item["click"]}
    if "wait" in item and isinstance(item.get("wait"), dict) and "time" in item["wait"]:
        item["wait"]["seconds"] = item["wait"].pop("time")
    # ExtractAction 要求 query，部分模型返回 goal 或 instruction → 映射为 query
    if "extract" in item and isinstance(item.get("extract"), dict):
        ex = item["extract"]
        if "query" not in ex:
            if "goal" in ex:
                ex["query"] = ex.pop("goal")
            elif "instruction" in ex:
                ex["query"] = ex.pop("instruction")
    # EvaluateAction 要求 code，部分模型返回 script 或 javascript → 映射为 code
    if "evaluate" in item and isinstance(item.get("evaluate"), dict):
        ev = item["evaluate"]
        if "code" not in ev:
            if "script" in ev:
                ev["code"] = ev.pop("script")
            elif "javascript" in ev:
                ev["code"] = ev.pop("javascript")
    # SearchPageAction 要求 pattern，部分模型返回 query → 映射为 pattern
    if "search_page" in item and isinstance(item.get("search_page"), dict):
        sp = item["search_page"]
        if "pattern" not in sp and "query" in sp:
            sp["pattern"] = sp.pop("query")


def _validate(cls, s: str):
    if isinstance(s, str):
        try:
            d = json.loads(s)
            if isinstance(d.get("action"), list):
                for x in d["action"]:
                    _norm(x)
                s = json.dumps(d)
        except Exception:
            pass
    return _orig_validate.__func__(cls, s)


BaseModel.model_validate_json = classmethod(_validate)
