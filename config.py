"""配置与任务列表。"""
import os

DEFAULT_START_CHROMIUM_SCRIPT = os.path.expanduser("~/.vnc/start-chromium.sh")
CDP_READY_TIMEOUT = 45
CDP_POST_START_DELAY = int(os.getenv("CDP_POST_START_DELAY", "5"))

TASKS = [
    "Open https://example.com and return the page title.",
    "Open https://example.com, click the 'More information' link, then return the first heading (h1 or main title) on the new page.",
    "Open https://duckduckgo.com, type 'Browser automation' in the search box and submit, then return the title of the first search result.",
    "Open https://httpbin.org/forms/post, fill in the 'Customer name' field with 'TestUser', and tell me the exact text on the submit button.",
    "Open https://en.wikipedia.org, use the search box to search for 'Python (programming language)', open the article, and return the first sentence of the first paragraph.",
]
