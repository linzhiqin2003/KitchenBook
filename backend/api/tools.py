"""
AI Lab 工具注册表 - 供 agentic loop 使用
"""
import json
import re
import math
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from django.conf import settings


# ==================== 工具定义（OpenAI 格式） ====================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "获取当前的日期和时间，包括星期几。当用户询问现在几点、今天几号、星期几等时间相关问题时使用。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "安全计算数学表达式。支持加减乘除、幂运算、括号、常用数学函数（sin, cos, sqrt, log 等）。当用户需要数学计算时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，例如 '123 * 456'、'sqrt(144)'、'2 ** 10'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索互联网获取实时信息。当用户询问最新新闻、实时数据、不确定的事实、或任何需要联网查询的问题时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["search", "news"],
                        "description": "搜索类型：'search' 为常规网页搜索，'news' 为新闻搜索。默认 'search'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "返回结果数量，1-10，默认 5"
                    }
                },
                "required": ["query"]
            }
        }
    },
]


# ==================== 工具处理函数 ====================

def handle_get_current_datetime(**kwargs):
    """返回当前日期时间和星期几"""
    now = datetime.now()
    weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
    return (
        f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')} "
        f"{weekdays[now.weekday()]}"
    )


# 计算器允许的安全名称
_CALC_SAFE_NAMES = {
    "abs": abs, "round": round, "min": min, "max": max,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sqrt": math.sqrt, "log": math.log, "log2": math.log2, "log10": math.log10,
    "exp": math.exp, "pow": pow, "ceil": math.ceil, "floor": math.floor,
    "pi": math.pi, "e": math.e,
}

# 白名单字符
_CALC_ALLOWED_CHARS = re.compile(r'^[0-9+\-*/().,%^ \t\n\w]+$')


def handle_calculator(expression="", **kwargs):
    """安全计算数学表达式"""
    expression = expression.strip()
    if not expression:
        raise ValueError("表达式不能为空")

    if not _CALC_ALLOWED_CHARS.match(expression):
        raise ValueError(f"表达式包含不允许的字符: {expression}")

    # 将 ^ 替换为 **（幂运算）
    expression = expression.replace('^', '**')

    try:
        result = eval(expression, {"__builtins__": {}}, _CALC_SAFE_NAMES)  # noqa: S307
    except Exception as exc:
        raise ValueError(f"计算失败: {exc}") from exc

    return f"{expression.replace('**', '^')} = {result}"


def handle_web_search(query="", search_type="search", max_results=5, **kwargs):
    """通过 Serper API 搜索互联网"""
    query = query.strip()
    if not query:
        raise ValueError("搜索关键词不能为空")

    api_key = getattr(settings, 'SERPER_API_KEY', '')
    if not api_key:
        raise ValueError("搜索服务未配置 (SERPER_API_KEY)")

    max_results = max(1, min(10, int(max_results)))
    endpoint = "news" if search_type == "news" else "search"
    url = f"https://google.serper.dev/{endpoint}"

    payload = json.dumps({"q": query, "num": max_results}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise ValueError("Serper API 认证失败，请检查 API Key") from e
        if e.code == 429:
            raise ValueError("搜索 API 请求频率超限，请稍后再试") from e
        raise ValueError(f"搜索 API 错误: HTTP {e.code}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise ValueError(f"搜索请求失败: {e}") from e

    # 解析结果
    raw_items = data.get("news" if search_type == "news" else "organic", [])

    if not raw_items:
        return f"未找到与 \"{query}\" 相关的结果。"

    lines = [f"搜索 \"{query}\" 的结果：\n"]
    for i, item in enumerate(raw_items[:max_results], 1):
        title = item.get("title", "无标题")
        snippet = item.get("snippet", "无摘要")
        link = item.get("link", "")
        date_str = item.get("date", "")
        lines.append(f"{i}. {title}")
        if date_str:
            lines.append(f"   日期: {date_str}")
        lines.append(f"   {snippet}")
        if link:
            lines.append(f"   链接: {link}")
        lines.append("")

    return "\n".join(lines)


# ==================== 工具映射 & 统一执行入口 ====================

TOOL_HANDLERS = {
    "get_current_datetime": handle_get_current_datetime,
    "calculator": handle_calculator,
    "web_search": handle_web_search,
}


def execute_tool(name, args):
    """统一执行入口，返回 (result_str, error_str)"""
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return None, f"未知工具: {name}"
    try:
        result = handler(**args)
        return str(result), None
    except Exception as exc:
        return None, str(exc)
