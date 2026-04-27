"""
ailab MCP Server — 将 ailab AI 能力暴露为 MCP 工具，供 Hermes Agent 调用。

启动方式（需在 backend/ 目录下运行）:
    cd backend
    DJANGO_SETTINGS_MODULE=config.settings python -m mcp_server.server

或者:
    fastmcp run mcp_server/server.py:mcp --transport http --port 8100
"""

import os
import sys
import json
import logging

# 确保 backend 在 Python path 中
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# 设置 Django 环境（复用现有配置和工具）
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from mcp.server.fastmcp import FastMCP
from django.conf import settings

logger = logging.getLogger(__name__)

mcp = FastMCP("ailab", description="AI Lab 智能工具集 — DeepSeek 对话、OCR、语音转录、表情包生成、菜谱搜索")

# ==================== 模型配置（与 views.py 保持一致） ====================

MODEL_CONFIGS = {
    "deepseek-v4-flash": {
        "label": "DeepSeek V4 Flash",
        "api_key_attr": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
    },
    "deepseek-v4-pro": {
        "label": "DeepSeek V4 Pro",
        "api_key_attr": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-pro",
    },
}

VALID_THINKING_LEVELS = {"none", "low", "medium", "high", "max"}


def _build_system_prompt():
    """构建系统提示词"""
    from datetime import datetime
    now = datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    time_str = f"{now.strftime('%Y年%m月%d日 %H:%M')} {weekdays[now.weekday()]}"
    return (
        f"当前时间：{time_str}。\n"
        "你是一个乐于助人的 AI 助手。你可以使用工具来获取实时信息或执行计算。\n\n"
        "【重要规则】\n"
        "1. 需要实时信息、最新数据或你不确定的事实时，必须调用 web_search 工具，禁止凭记忆编造。\n"
        "2. [REF:n] 标记只能来自工具返回的结果，禁止自己编造引用标记。\n"
        "3. 引用时将 [REF:n] 放在具体数据或论述旁边，不要把多个引用堆在一起。\n"
        "4. 使用工具后直接给出答案，不要说「让我帮你查找」「稍等」之类的过渡语。\n"
        "5. 如果用户的问题不需要工具（常识、闲聊），直接回答即可。\n"
        "6. 多次搜索时，每次工具返回的 [REF:n] 编号全局唯一递增，请直接使用工具给出的编号，不要重新编号。\n"
        "7. 调用 web_search 时，务必使用 focus 参数传递检索重点，告诉摘要 AI 应该关注提取什么信息。\n"
    )


# ==================== MCP 工具 ====================

@mcp.tool()
def ailab_chat(
    message: str,
    model: str = "deepseek-v4-flash",
    thinking: str = "low",
    max_rounds: int = 10,
) -> str:
    """
    AI 对话工具——调用 DeepSeek 大模型进行智能问答。

    支持多模型、thinking effort 控制、自动 web_search 工具调用。
    适用于：知识问答、代码编写、文本创作、逻辑推理、实时信息搜索等。

    Args:
        message: 用户消息内容
        model: 模型选择，可选 "deepseek-v4-flash"（快速）或 "deepseek-v4-pro"（深度推理）
        thinking: 思考强度，可选 "none"（关闭）、"low"、"medium"、"high"、"max"
        max_rounds: 最大工具调用轮数，默认 10
    """
    from openai import OpenAI
    from api.tools import TOOL_DEFINITIONS, execute_tool, reset_ref_counter, get_collected_references

    if thinking not in VALID_THINKING_LEVELS:
        thinking = "low"

    cfg = MODEL_CONFIGS.get(model)
    if not cfg:
        return f"错误：不支持的模型 {model}。可选：{', '.join(MODEL_CONFIGS.keys())}"

    api_key = getattr(settings, cfg["api_key_attr"], "")
    if not api_key:
        return f"错误：{cfg['label']} API Key 未配置，请联系管理员设置 DEEPSEEK_API_KEY"

    client = OpenAI(api_key=api_key, base_url=cfg["base_url"])

    # 重置引用计数器
    reset_ref_counter()

    # 构建消息
    messages = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user", "content": message},
    ]

    extra_body = {}
    if thinking == "none":
        extra_body["thinking"] = {"type": "disabled"}
    else:
        extra_body["thinking"] = {"type": "enabled"}
        extra_body["reasoning_effort"] = thinking

    try:
        for round_num in range(max_rounds):
            response = client.chat.completions.create(
                model=cfg["model"],
                messages=messages,
                tools=TOOL_DEFINITIONS,
                extra_body=extra_body,
            )

            choice = response.choices[0]
            finish_reason = choice.finish_reason

            # 处理工具调用
            if finish_reason == "tool_calls" and choice.message.tool_calls:
                # 添加 assistant 消息（含 tool_calls）
                assistant_msg = choice.message.model_dump()
                messages.append({
                    "role": "assistant",
                    "content": assistant_msg.get("content"),
                    "tool_calls": assistant_msg.get("tool_calls"),
                })

                # 执行每个工具
                for tc in choice.message.tool_calls:
                    tool_name = tc.function.name
                    try:
                        tool_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    result_str, error_str = execute_tool(tool_name, tool_args)

                    if error_str:
                        tool_content = json.dumps({"error": error_str}, ensure_ascii=False)
                    else:
                        tool_content = result_str or ""

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_content,
                    })

                continue  # 下一轮

            # finish_reason == "stop" → 返回内容
            content = choice.message.content or ""

            # 补齐引用来源
            collected_refs = get_collected_references()
            if collected_refs:
                ref_lines = ["\n\n---\n**引用来源**\n"]
                for ref_id, url, title, domain in collected_refs:
                    safe_title = title.replace("[", "").replace("]", "")
                    ref_lines.append(f"- **{ref_id}.** [{safe_title}]({url})")
                content += "\n".join(ref_lines)

            return content

        return "已达到最大工具调用轮数，但未获得最终结果。请尝试简化问题。"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"AI 对话出错：{str(e)}"


@mcp.tool()
def ailab_ocr(image_url: str) -> str:
    """
    图片 OCR 识别——将图片中的文字/公式/表格转换为 Markdown 格式。

    适用于：识别截图中的文字、提取图片中的题目、转换手写笔记、扫描文档等。

    Args:
        image_url: 图片的 URL 地址（需可公开访问）
    """
    import requests
    import base64

    api_key = getattr(settings, "OPENROUTER_API_KEY", "")
    if not api_key:
        return "错误：OpenRouter API Key 未配置"

    try:
        # 下载图片并转 base64
        resp = requests.get(image_url, timeout=30)
        resp.raise_for_status()
        img_b64 = base64.b64encode(resp.content).decode("utf-8")
        content_type = resp.headers.get("content-type", "image/png")

        payload = {
            "model": "qwen/qwen3-vl-8b-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content_type};base64,{img_b64}"
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "请将图片内容转换为 Markdown 格式。要求：\n"
                                "1. 保留公式（LaTeX）、表格、代码块等结构\n"
                                "2. 对于手写内容，尽量准确识别\n"
                                "3. 只输出 Markdown 内容，不要添加任何额外说明或前缀\n"
                                "4. 如果图片中有中文、日文、韩文等多语言文字，直接按原文输出"
                            ),
                        },
                    ],
                }
            ],
            "max_tokens": 4096,
            "temperature": 0.1,
        }

        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://www.lzqqq.org",
                "X-Title": "AI Lab OCR",
            },
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"OCR 识别失败：{str(e)}"


@mcp.tool()
def ailab_transcribe(audio_url: str, language: str = "zh") -> str:
    """
    语音转录——将音频文件转换为文字。

    支持多语言，使用 Whisper 模型。适用于：会议记录、语音笔记转文字、采访转录等。

    Args:
        audio_url: 音频文件的 URL 地址（需可公开访问）
        language: 音频语言代码，如 "zh"（中文）、"en"（英文）、"ja"（日文），默认 "zh"
    """
    import requests

    openai_key = getattr(settings, "OPENAI_API_KEY", "")
    openai_base = getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not openai_key:
        return "错误：OpenAI API Key 未配置（语音转录需要 OPENAI_API_KEY）"

    try:
        # 下载音频
        resp = requests.get(audio_url, timeout=60)
        resp.raise_for_status()

        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(resp.content)
            tmp_path = f.name

        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key, base_url=openai_base)

            with open(tmp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                )
            return transcript.text
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        return f"语音转录失败：{str(e)}"


@mcp.tool()
def ailab_emoji_generate(
    template_id: str,
    image_url: str,
) -> str:
    """
    表情包视频生成——上传人像图片，套用表情模板生成动态表情包。

    模板 ID: "mua"（飞吻）、"whistle"（吹口哨）、"wink"（眨眼）、"cute"（可爱）等。

    Args:
        template_id: 表情模板 ID
        image_url: 人像图片的 URL 地址
    """
    import requests

    dashscope_key = getattr(settings, "DASHSCOPE_API_KEY", "")
    if not dashscope_key:
        return "错误：DashScope API Key 未配置（表情包需要 DASHSCOPE_API_KEY）"

    try:
        service = _get_emoji_service()
        if service is None:
            return "错误：EmojiService 初始化失败"

        # 下载图片
        resp = requests.get(image_url, timeout=30)
        resp.raise_for_status()

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(resp.content)
            img_path = f.name

        try:
            # 检测人脸
            face_result = service.detect_face(img_path)
            if not face_result.get("success"):
                return f"人脸检测失败：{face_result.get('error', '未检测到人脸')}"

            # 创建任务
            task_result = service.create_task(template_id, face_result["face_id"])
            if not task_result.get("task_id"):
                return f"创建任务失败：{task_result.get('error', '未知错误')}"

            task_id = task_result["task_id"]

            # 轮询等待完成
            import time
            for _ in range(30):
                status = service.get_task_status(task_id)
                if status.get("status") == "completed":
                    return f"表情包生成成功！\n视频 URL: {status.get('video_url', '')}"
                elif status.get("status") == "failed":
                    return f"表情包生成失败：{status.get('error', '未知错误')}"
                time.sleep(2)

            return f"表情包生成超时，任务 ID: {task_id}，请稍后查询"

        finally:
            os.unlink(img_path)

    except Exception as e:
        return f"表情包生成失败：{str(e)}"


def _get_emoji_service():
    """延迟初始化 EmojiService"""
    try:
        from apps.emoji_generator.services import EmojiService
        return EmojiService()
    except ValueError as e:
        logger.error("EmojiService init failed: %s", e)
        return None


@mcp.tool()
def ailab_search_recipes(query: str = "", limit: int = 10) -> str:
    """
    搜索菜谱——从厨房系统中查找菜谱。

    适用于：查找某道菜的做法、浏览菜谱列表、按食材搜索菜谱等。

    Args:
        query: 搜索关键词（菜名、食材等），留空则返回全部
        limit: 返回数量，默认 10
    """
    from api.models import Recipe

    try:
        qs = Recipe.objects.filter(is_public=True)
        if query:
            qs = qs.filter(title__icontains=query)

        recipes = qs[:limit]
        if not recipes:
            return "未找到匹配的菜谱。"

        lines = [f"找到 {qs.count()} 道菜谱（显示前 {len(recipes)} 道）：\n"]
        for r in recipes:
            time_str = f"{r.cooking_time}分钟" if r.cooking_time else "未知"
            desc = r.description[:80] + "..." if len(r.description) > 80 else r.description
            lines.append(f"- **{r.title}** | 烹饪时间: {time_str}")
            if desc:
                lines.append(f"  {desc}")
        return "\n".join(lines)

    except Exception as e:
        return f"搜索菜谱失败：{str(e)}"


@mcp.tool()
def ailab_get_blog_posts(limit: int = 5, category: str = "") -> str:
    """
    获取技术博客文章。

    适用于：查找技术文章、浏览博客、搜索特定主题的博文。

    Args:
        limit: 返回数量，默认 5
        category: 按分类筛选，留空则返回全部
    """
    from api.models import BlogPost

    try:
        qs = BlogPost.objects.filter(is_published=True)
        if category:
            qs = qs.filter(category__name__icontains=category)

        posts = qs[:limit]
        if not posts:
            return "未找到匹配的博客文章。"

        lines = [f"最新博客文章（共 {qs.count()} 篇）：\n"]
        for p in posts:
            date_str = p.created_at.strftime("%Y-%m-%d") if p.created_at else ""
            lines.append(f"- **{p.title}** ({date_str})")
            if p.summary:
                lines.append(f"  {p.summary[:100]}")
        return "\n".join(lines)

    except Exception as e:
        return f"获取博客失败：{str(e)}"


# ==================== 入口 ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ailab MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "http"], help="传输协议")
    parser.add_argument("--port", type=int, default=8100, help="HTTP 端口（仅 http 模式）")
    parser.add_argument("--host", default="127.0.0.1", help="绑定地址")
    args = parser.parse_args()

    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
