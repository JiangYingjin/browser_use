"""配置"""

import os

START_CHROMIUM_SCRIPT = os.path.expanduser("~/.vnc/start-chromium.sh")
CDP_URL = "http://127.0.0.1:9222"
CDP_READY_TIMEOUT = 45

OPENAI_BASE_URL = "https://dj.jyj.cx/v1"
OPENAI_API_KEY = "sk-jiangyj"
BROWSER_USE_LLM_MODEL = "jyj.cx/flash:or"
