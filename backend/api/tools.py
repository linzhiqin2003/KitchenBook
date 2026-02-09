"""
AI Lab 工具注册表 - 供 agentic loop 使用

增强版 web_search：
- Google CSE + Serper 双引擎搜索
- Jina Reader 网页抓取
- Cerebras AI 结构化提取（DeepSeek 降级）
- Consolidation 综合报告 + 引用标记 [REF:n]
"""
import json
import logging
import re
import math
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


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
            "description": "搜索互联网获取实时信息。自动抓取网页并生成 AI 摘要，结果包含引用标记 [REF:n]。当用户询问最新新闻、实时数据、不确定的事实、或任何需要联网查询的问题时使用。",
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


# ==================== 增强版 Web Search ====================

# 需要去除的 tracking 参数
_TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'gclid', 'fbclid', 'ref', 'source', 'spm', 'from', 'isappinstalled',
}

# Jina 抓取内容最大字符数
_JINA_MAX_CHARS = 8000

# 抓取 top N URL
_SCRAPE_TOP_N = 3

# Cerebras API 配置
_CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
_CEREBRAS_MODEL = "gpt-oss-120b"

# Cerebras key pool round-robin 计数器
_cerebras_key_index = 0


def _normalize_url(url):
    """清理 URL：去除 tracking 参数和 fragment"""
    try:
        parsed = urllib.parse.urlparse(url)
        # 去除 fragment
        parsed = parsed._replace(fragment='')
        # 过滤 tracking 参数
        qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=False)
        cleaned_qs = {
            k: v for k, v in qs.items()
            if k.lower() not in _TRACKING_PARAMS
        }
        new_query = urllib.parse.urlencode(cleaned_qs, doseq=True)
        parsed = parsed._replace(query=new_query)
        return urllib.parse.urlunparse(parsed)
    except Exception:
        return url


def _extract_domain(url):
    """从 URL 提取域名"""
    try:
        return urllib.parse.urlparse(url).netloc
    except Exception:
        return url


def _search_google_cse(query, num=5):
    """Google Custom Search Engine 搜索"""
    api_key = getattr(settings, 'GOOGLE_CSE_API_KEY', '')
    cx = getattr(settings, 'GOOGLE_CSE_CX', '')
    if not api_key or not cx:
        return None

    params = urllib.parse.urlencode({
        'key': api_key,
        'cx': cx,
        'q': query,
        'num': min(num, 10),
    })
    url = f"https://www.googleapis.com/customsearch/v1?{params}"
    req = urllib.request.Request(url, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        logger.warning("Google CSE search failed: %s", e)
        return None

    items = data.get("items", [])
    if not items:
        return None

    results = []
    for item in items:
        results.append({
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "link": item.get("link", ""),
        })
    return results


def _search_serper(query, search_type="search", num=5):
    """Serper API 搜索（备用引擎）"""
    api_key = getattr(settings, 'SERPER_API_KEY', '')
    if not api_key:
        return None

    endpoint = "news" if search_type == "news" else "search"
    url = f"https://google.serper.dev/{endpoint}"
    payload = json.dumps({"q": query, "num": num}).encode("utf-8")
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        logger.warning("Serper search failed: %s", e)
        return None

    raw_items = data.get("news" if search_type == "news" else "organic", [])
    if not raw_items:
        return None

    results = []
    for item in raw_items:
        results.append({
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "link": item.get("link", ""),
            "date": item.get("date", ""),
        })
    return results


def _jina_scrape(url, timeout=15):
    """使用 Jina Reader 抓取网页内容（纯文本）"""
    jina_url = f"https://r.jina.ai/{url}"
    req = urllib.request.Request(
        jina_url,
        headers={"Accept": "text/plain"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8", errors="replace").strip()
            # 截断到最大字符数
            if len(content) > _JINA_MAX_CHARS:
                content = content[:_JINA_MAX_CHARS] + "\n...(内容已截断)"
            return content
    except Exception as e:
        logger.warning("Jina scrape failed for %s: %s", url, e)
        return None


def _get_cerebras_key():
    """从 key pool 中轮询取一个 Cerebras API key"""
    global _cerebras_key_index
    pool_str = getattr(settings, 'CEREBRAS_API_KEY_POOL', '')
    if not pool_str:
        return None
    keys = [k.strip() for k in pool_str.split(',') if k.strip()]
    if not keys:
        return None
    key = keys[_cerebras_key_index % len(keys)]
    _cerebras_key_index += 1
    return key


def _llm_call(system_msg, user_msg, max_tokens=2048, timeout=30):
    """通用 LLM 调用：Cerebras 优先 → DeepSeek 降级。返回文本或 None。"""
    # ── 尝试 Cerebras（极速推理）──
    cerebras_key = _get_cerebras_key()
    if cerebras_key:
        payload = json.dumps({
            "model": _CEREBRAS_MODEL,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{_CEREBRAS_BASE_URL}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {cerebras_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"].strip()
            if text:
                return text
        except Exception as e:
            logger.warning("Cerebras LLM call failed, falling back to DeepSeek: %s", e)

    # ── 降级到 DeepSeek ──
    api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
    base_url = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    if not api_key:
        return None

    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning("DeepSeek LLM call failed: %s", e)
        return None


# ── 结构化提取 prompt（移植自 research_agent） ──

_EXTRACT_SYSTEM_MSG = (
    "你是严谨的研究助手，专注于从网页中提取结构化信息。"
    "你的输出将直接供下游分析使用，因此必须：\n"
    "1) 严格遵循指定的 Markdown 输出格式\n"
    "2) 保留所有量化数据（数字、百分比、金额）及其上下文\n"
    "3) 保持信息密度，不要注水或重复\n"
    "4) 如果信息不确定，明确标注 [待核实]\n"
    "5) 使用中文输出"
)

_EXTRACT_PROMPT_TEMPLATE = (
    "基于以下网页正文，提取结构化研究摘要。\n\n"
    "来源标记：[REF:{ref_id}]\n\n"
    "【严格要求】\n"
    "- 只基于提供的文本，禁止编造任何信息\n"
    "- 保留所有关键数字、日期、百分比、金额、人名、公司名\n"
    "- 使用中文输出\n\n"
    "【输出格式】按以下 Markdown 结构输出：\n\n"
    "### 核心发现\n"
    "(用 1-3 句话概括本页最重要的信息，标注 [REF:{ref_id}])\n\n"
    "### 关键数据\n"
    "| 指标 | 数值 | 时间/口径 | 变动 |\n"
    "| --- | --- | --- | --- |\n"
    "| (指标名) | (具体数值) | (财年/季度/日期) | (同比/环比变化) |\n\n"
    "(如页面无量化数据，写「本页无量化数据」)\n\n"
    "### 定性要点\n"
    "- (重要的非数值信息，标注 [REF:{ref_id}])\n\n"
    "--- 网页正文 ---\n"
    "标题：{title}\n"
    "URL：{url}\n\n"
    "{content}"
)

# ── Consolidation prompt（移植自 research_agent） ──

_CONSOLIDATE_SYSTEM_MSG = (
    "你是严谨的研究助手。你的任务是将多个网页摘要综合为一份精炼的研究摘要。\n"
    "要求：\n"
    "1) 保留所有量化数据（数字、百分比、金额）及其上下文\n"
    "2) 去除不同来源间的重复信息，保留最详细的版本\n"
    "3) 按主题组织信息，而不是按来源罗列\n"
    "4) 使用【引用映射表】中提供的全局 [REF:n] 编号标注数据来源，禁止自行编造引用编号\n"
    "5) 使用中文输出\n"
    "6) 只基于提供的内容，禁止编造"
)

_CONSOLIDATE_PROMPT_TEMPLATE = (
    "以下是针对搜索词「{query}」从多个网页提取的摘要。"
    "请将所有来源的信息综合为一份精炼的结构化研究摘要。\n\n"
    "【引用映射表】\n"
    "以下是本次涉及的页面 URL 及其全局引用 ID，请在输出中使用这些 [REF:n] 编号标注数据来源：\n"
    "{ref_mapping}\n\n"
    "【严格要求】\n"
    "- 在关键数据表和正文中必须使用上方【引用映射表】提供的 [REF:n] 编号标注数据出处\n"
    "- 禁止自行编造引用编号；如某数据无法归属到具体来源，注明「来源不明」\n\n"
    "【输出格式】\n"
    "### 核心发现\n"
    "(3-5 条最重要的发现，每条一行，标注 [REF:n])\n\n"
    "### 关键数据\n"
    "| 指标 | 数值 | 时间/口径 | 变动 | 来源 |\n"
    "| --- | --- | --- | --- | --- |\n"
    "(合并所有来源的量化数据，「来源」列使用 [REF:n] 编号)\n\n"
    "### 详细分析\n"
    "(按主题组织的深入分析，关键数据标注 [REF:n])\n\n"
    "### 风险与不确定性\n"
    "(如有相关信息，标注 [REF:n])\n\n"
    "--- 待综合内容 ---\n"
    "{content}"
)


def _ai_extract(title, content, ref_id, url):
    """使用 Cerebras/DeepSeek 对网页内容做结构化提取"""
    prompt = _EXTRACT_PROMPT_TEMPLATE.format(
        ref_id=ref_id,
        title=title,
        url=url,
        content=content[:6000],
    )
    return _llm_call(_EXTRACT_SYSTEM_MSG, prompt, max_tokens=2048, timeout=30)


def _ai_consolidate(summaries, references, query):
    """使用 Cerebras/DeepSeek 对多条摘要做综合报告"""
    # 构建引用映射表
    ref_mapping = ""
    for ref_id, url, title, domain in references:
        ref_mapping += f"- [REF:{ref_id}] {url}\n"

    # 构建待综合内容
    combined = ""
    for s in summaries:
        combined += f"\n--- [REF:{s['ref_id']}] {s['title']} ---\n{s['content']}\n"

    prompt = _CONSOLIDATE_PROMPT_TEMPLATE.format(
        query=query,
        ref_mapping=ref_mapping,
        content=combined,
    )
    return _llm_call(_CONSOLIDATE_SYSTEM_MSG, prompt, max_tokens=4096, timeout=45)


def handle_web_search(query="", search_type="search", max_results=5, **kwargs):
    """增强版 web_search：搜索 + 抓取 + AI 摘要 + 引用标记"""
    query = query.strip()
    if not query:
        raise ValueError("搜索关键词不能为空")

    max_results = max(1, min(10, int(max_results)))

    # ── 1. 双引擎搜索：Google CSE → Serper ──
    search_results = None

    # 优先 Google CSE（news 模式 CSE 不支持，直接走 Serper）
    if search_type != "news":
        search_results = _search_google_cse(query, num=max_results)
        if search_results:
            logger.info("Search via Google CSE: %d results", len(search_results))

    # CSE 失败或 news 模式，走 Serper
    if not search_results:
        search_results = _search_serper(query, search_type=search_type, num=max_results)
        if search_results:
            logger.info("Search via Serper: %d results", len(search_results))

    if not search_results:
        raise ValueError("搜索引擎均不可用，请检查 API 配置")

    if not search_results:
        return f"未找到与 \"{query}\" 相关的结果。"

    # ── 2. 构建引用列表 & 清理 URL ──
    references = []  # [(ref_id, url, title, domain)]
    for i, item in enumerate(search_results[:max_results], 1):
        url = _normalize_url(item.get("link", ""))
        title = item.get("title", "无标题")
        domain = _extract_domain(url)
        references.append((i, url, title, domain))

    # ── 3. Jina Reader 抓取 top N URL ──
    scraped = []  # [{ref_id, title, content, url}]
    for ref_id, url, title, domain in references[:_SCRAPE_TOP_N]:
        if not url:
            continue
        content = _jina_scrape(url)
        if content and len(content) > 100:
            scraped.append({
                "ref_id": ref_id,
                "title": title,
                "content": content,
                "url": url,
            })
        else:
            # Jina 抓取失败，用搜索 snippet 替代
            snippet = search_results[ref_id - 1].get("snippet", "")
            if snippet:
                scraped.append({
                    "ref_id": ref_id,
                    "title": title,
                    "content": snippet,
                    "url": url,
                })

    # ── 4. Cerebras/DeepSeek 结构化提取 ──
    summaries = []
    for item in scraped:
        extracted = _ai_extract(
            item["title"], item["content"], item["ref_id"], item["url"],
        )
        if extracted:
            summaries.append({
                "ref_id": item["ref_id"],
                "title": item["title"],
                "content": extracted,
            })
        else:
            # AI 提取失败，用截断的原文内容替代
            truncated = item["content"][:500]
            summaries.append({
                "ref_id": item["ref_id"],
                "title": item["title"],
                "content": truncated,
            })

    # ── 5. Consolidation（2+ 条摘要且总长度 > 500 字） ──
    total_summary_len = sum(len(s["content"]) for s in summaries)

    if len(summaries) >= 2 and total_summary_len > 500:
        consolidated = _ai_consolidate(summaries, references, query)
        if consolidated:
            return consolidated

    # ── 6. 降级：直接拼接摘要 + 引用列表 ──
    lines = [f"搜索 \"{query}\" 的结果：\n"]

    # 有摘要时输出摘要
    if summaries:
        for s in summaries:
            lines.append(f"**[REF:{s['ref_id']}] {s['title']}**")
            lines.append(s["content"])
            lines.append("")
    else:
        # 没有摘要，输出原始搜索结果
        for i, item in enumerate(search_results[:max_results], 1):
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

    # 附引用列表
    lines.append("### 引用来源")
    for ref_id, url, title, domain in references:
        lines.append(f"[REF:{ref_id}] {title} - {url}")

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
