"""
兼容层：强制非流式 LLM 调用、规范化 Agent 输出 JSON。
导入此模块即生效（monkey-patch）。
"""
import json

from openai.resources.chat.completions import AsyncCompletions
from pydantic import BaseModel

# 强制非流式，避免网关返回流式/非标准体导致 'str' object has no attribute 'choices'
_orig_create = AsyncCompletions.create


async def _create_no_stream(self, *args, **kwargs):
    kwargs["stream"] = False
    return await _orig_create(self, *args, **kwargs)


AsyncCompletions.create = _create_no_stream

# 规范化 action：click 整数→对象、wait.time→wait.seconds（兼容 jyj.cx/flash:or 等）
_orig_validate = BaseModel.model_validate_json


def _normalize_action_item(item: dict) -> None:
    if not isinstance(item, dict):
        return
    if "click" in item and isinstance(item["click"], int):
        item["click"] = {"index": item["click"]}
    if "wait" in item and isinstance(item["wait"], dict) and "time" in item["wait"]:
        item["wait"]["seconds"] = item["wait"].pop("time")


def _model_validate_json(cls, s: str):
    if isinstance(s, str):
        try:
            data = json.loads(s)
            if isinstance(data.get("action"), list):
                for item in data["action"]:
                    _normalize_action_item(item)
                s = json.dumps(data)
        except Exception:
            pass
    return _orig_validate.__func__(cls, s)


BaseModel.model_validate_json = classmethod(_model_validate_json)
