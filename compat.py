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
    # ExtractAction 要求 query，部分模型返回 goal → 映射为 query
    if "extract" in item and isinstance(item.get("extract"), dict):
        ex = item["extract"]
        if "goal" in ex and "query" not in ex:
            ex["query"] = ex.pop("goal")
    # EvaluateAction 要求 code，部分模型（如 jyj.cx/flash:or）返回 javascript → 映射为 code
    if "evaluate" in item and isinstance(item.get("evaluate"), dict):
        ev = item["evaluate"]
        if "javascript" in ev and "code" not in ev:
            ev["code"] = ev.pop("javascript")


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
