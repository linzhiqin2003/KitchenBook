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
import asyncio
import logging
from functools import partial

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

mcp = FastMCP("ailab", instructions="AI Lab 智能工具集 — DeepSeek 对话、OCR、语音转录、表情包生成、菜谱搜索")

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


# ==================== MCP 工具（async-safe） ====================

@mcp.tool()
async def ailab_search_recipes(query: str = "", limit: int = 10) -> str:
    """
    搜索菜谱——从厨房系统中查找菜谱。

    适用于：查找某道菜的做法、浏览菜谱列表、按食材搜索菜谱等。

    Args:
        query: 搜索关键词（菜名、食材等），留空则返回全部
        limit: 返回数量，默认 10
    """
    def _search():
        from django.db import connection
        connection.close_if_unusable_or_obsolete()
        from api.models import Recipe
        try:
            qs = Recipe.objects.filter(is_public=True)
            if query:
                qs = qs.filter(title__icontains=query)
            total = qs.count()
            recipes = list(qs[:limit])
            if not recipes:
                return "未找到匹配的菜谱。"

            lines = [f"找到 {total} 道菜谱（显示前 {len(recipes)} 道）：\n"]
            for r in recipes:
                time_str = f"{r.cooking_time}分钟" if r.cooking_time else "未知"
                desc = r.description[:80] + "..." if len(r.description) > 80 else r.description
                lines.append(f"- **{r.title}** | 烹饪时间: {time_str}")
                if desc:
                    lines.append(f"  {desc}")
            return "\n".join(lines)
        except Exception as e:
            return f"搜索菜谱失败：{str(e)}"

    return await asyncio.to_thread(_search)


@mcp.tool()
async def ailab_get_blog_posts(limit: int = 5, category: str = "") -> str:
    """
    获取技术博客文章。

    适用于：查找技术文章、浏览博客、搜索特定主题的博文。

    Args:
        limit: 返回数量，默认 5
        category: 按分类筛选，留空则返回全部
    """
    def _get_posts():
        from django.db import connection
        connection.close_if_unusable_or_obsolete()
        from api.models import BlogPost
        try:
            qs = BlogPost.objects.filter(is_published=True)
            if category:
                qs = qs.filter(category__name__icontains=category)
            total = qs.count()
            posts = list(qs[:limit])
            if not posts:
                return "未找到匹配的博客文章。"

            lines = [f"最新博客文章（共 {total} 篇）：\n"]
            for p in posts:
                date_str = p.created_at.strftime("%Y-%m-%d") if p.created_at else ""
                lines.append(f"- **{p.title}** ({date_str})")
                if p.summary:
                    lines.append(f"  {p.summary[:100]}")
            return "\n".join(lines)
        except Exception as e:
            return f"获取博客失败：{str(e)}"

    return await asyncio.to_thread(_get_posts)


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
