# Browser Use 试用（Server 可运行）

## 怎么用

Browser Use 有两种用法：

| 方式 | 依赖 | 浏览器在哪跑 | 适合 |
|------|------|--------------|------|
| **Cloud SDK**（`browser-use-sdk`） | `BROWSER_USE_API_KEY` | Browser Use 云端 | 不想管浏览器、快速试 |
| **开源库**（`browser-use`） | Playwright + 任选 LLM（OpenAI/Anthropic/自建） | 本机/Server 用 Playwright 起 Chromium | 自托管、Server 无界面 |

本目录（`~/proj/browser_use`）用**开源库**：Agent + 浏览器（**优先接已有 CDP**，否则自起 headless）。

## 推荐：用已有 CDP（不自起浏览器）

与本机规约一致：**先启动 Chromium（--remote-debugging-port=9222）**，再跑脚本，Agent 直接连该实例。

```bash
# 1. 先起浏览器（VNC/本机 或 start-chromium.sh，见 ~/.cursor/docs/chrome-remote-debugging-port-9222.md）
# 2. 再跑 Agent
cd ~/proj/browser_use
uv sync
OPENAI_API_KEY=sk-jiangyj uv run python run_headless.py
```

默认连 `http://127.0.0.1:9222`；可设 `CDP_URL` 覆盖（如 `CDP_URL=http://127.0.0.1:9223`）。不设 `CDP_URL` 时脚本会尝试自起浏览器（需 Chromium 可启动，server 无界面时易失败）。

## Server 上能跑吗？

- **接已有 CDP**：能。本机或能访问 9222 的机器上先起 Chromium，脚本只连 CDP，不依赖显示器。
- **自起浏览器**：需 Playwright Chromium、且无界面时往往要 `chromium_sandbox=False` 等；优先用上面「已有 CDP」方式。
- LLM：`OPENAI_API_KEY` + `OPENAI_BASE_URL`，默认 model `jyj.cx/flash:or`。

## 环境变量（示例）

```bash
# LLM（OpenAI 兼容）
export OPENAI_API_KEY="sk-jiangyj"
export OPENAI_BASE_URL="https://dj.jyj.cx/v1"

# 已有 CDP（默认 9222）
export CDP_URL="http://127.0.0.1:9222"
```

## 运行

```bash
cd ~/proj/browser_use
uv sync
# 推荐：先起 Chromium 再跑
OPENAI_API_KEY=sk-jiangyj uv run python run_headless.py
```

`run_headless.py` 里任务可改：当前为打开 example.com 并取标题。

## 参考

- [Browser Use 开源文档](https://docs.browser-use.com/)
- [Supported Models](https://docs.browser-use.com/open-source/supported-models)（OpenAI/Anthropic/Google/Ollama/自定义 base_url）
