"""
AI Lab 工具注册表 - 供 DeepSeek Speciale agentic loop 使用
"""
import re
import math
from datetime import datetime


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


# ==================== 工具映射 & 统一执行入口 ====================

TOOL_HANDLERS = {
    "get_current_datetime": handle_get_current_datetime,
    "calculator": handle_calculator,
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
