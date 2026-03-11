#!/usr/bin/env python3
"""
自定义 Tools：在默认 browser-use actions 基础上增加 get_region_html。

用法：创建 Agent 时传入 tools=ToolsWithRegionHtml()，则 agent 可调用
  get_region_html(selector="...")
得到该元素的 outerHTML（在 extracted_content 中），再用 write_file 保存。

示例：
  from tools_with_region_html import ToolsWithRegionHtml
  agent = Agent(task=task, llm=llm, browser_session=session, tools=ToolsWithRegionHtml())
"""
import json
import logging
from typing import Optional

from pydantic import BaseModel, Field

from browser_use.agent.views import ActionResult
from browser_use.browser import BrowserSession
from browser_use.tools.service import Tools

logger = logging.getLogger(__name__)


class GetRegionHtmlAction(BaseModel):
	selector: str = Field(description='CSS selector for the element to get outerHTML (e.g. "table", "div.main")')
	max_length: Optional[int] = Field(
		default=None,
		description='Optional. If set, truncate to this many characters; if not set, return full HTML (no truncation) so the full DOM structure is preserved for parsing or inspection.',
	)


class ToolsWithRegionHtml(Tools):
	"""在默认 Tools 上增加 get_region_html：用 CDP Runtime.evaluate 取元素 outerHTML。"""

	def __init__(self, exclude_actions=None, output_model=None, display_files_in_done_text=True):
		super().__init__(
			exclude_actions=exclude_actions,
			output_model=output_model,
			display_files_in_done_text=display_files_in_done_text,
		)

		@self.registry.action(
			'Get the outerHTML of the first element matching the CSS selector. Use to save a region\'s raw HTML for later parsing (e.g. table container). Returns the HTML string in extracted_content; then use write_file to save it.',
			param_model=GetRegionHtmlAction,
		)
		async def get_region_html(params: GetRegionHtmlAction, browser_session: BrowserSession):
			# 安全注入 selector，避免 XSS；仅传字符串
			sel = params.selector
			if not sel or not isinstance(sel, str):
				return ActionResult(error='selector must be a non-empty string')
			expr = (
				'(function(){ var el = document.querySelector('
				+ json.dumps(sel)
				+ '); return el ? el.outerHTML : null; })()'
			)
			try:
				cdp_session = await browser_session.get_or_create_cdp_session()
				result = await cdp_session.cdp_client.send.Runtime.evaluate(
					params={'expression': expr, 'returnByValue': True, 'awaitPromise': True},
					session_id=cdp_session.session_id,
				)
			except Exception as e:
				logger.exception('get_region_html CDP failed')
				return ActionResult(error=f'get_region_html failed: {e}')

			if result.get('exceptionDetails'):
				msg = result['exceptionDetails'].get('text', 'Unknown JS error')
				return ActionResult(error=f'get_region_html JS error: {msg}')

			value = result.get('result', {}).get('value')
			if value is None:
				return ActionResult(
					extracted_content='',
					long_term_memory=f'No element found for selector: {sel!r}',
				)
			if not isinstance(value, str):
				return ActionResult(error=f'get_region_html returned non-string: {type(value)}')

			# 仅当显式传入 max_length 时才截断，默认不截断，保留完整结构供解析或人工查看
			if params.max_length is not None and len(value) > params.max_length:
				value = value[: params.max_length] + '\n... [truncated]'
			memory = f'Got outerHTML for selector {sel!r} ({len(value)} chars).'
			logger.info('📄 %s', memory)
			return ActionResult(extracted_content=value, long_term_memory=memory)
