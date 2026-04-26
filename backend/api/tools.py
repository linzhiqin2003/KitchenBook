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
import threading
import urllib.request
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)

# ==================== 请求级引用计数器（线程安全） ====================
_ref_state = threading.local()


def reset_ref_counter():
    """在每次新的 agentic loop 开始时调用，重置引用编号和收集列表。"""
    _ref_state.counter = 0
    _ref_state.references = []  # [(ref_id, url, title, domain), ...]


def _next_ref_id():
    """获取下一个全局引用编号（同一请求内单调递增）。"""
    if not hasattr(_ref_state, 'counter'):
        _ref_state.counter = 0
    _ref_state.counter += 1
    return _ref_state.counter


def _collect_ref(ref_id, url, title, domain):
    """将引用信息收集到请求级列表中，供最终补齐用。"""
    if not hasattr(_ref_state, 'references'):
        _ref_state.references = []
    _ref_state.references.append((ref_id, url, title, domain))


def get_collected_references():
    """获取本次请求中所有工具调用收集到的引用列表。"""
    return getattr(_ref_state, 'references', [])


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
                    },
                    "focus": {
                        "type": "string",
                        "description": "告诉摘要 AI 重点提取什么信息。例如：'关注最新季度营收和利润数据'、'重点提取技术架构和性能指标'。不传则做通用提取。"
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

# 抓取 top N URL（None = 全部抓取）
_SCRAPE_TOP_N = None

# Cerebras API 配置
_CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
_CEREBRAS_MODEL = "qwen-3-32b"
# 必须设置浏览器 User-Agent，否则 Cloudflare 返回 403
_CEREBRAS_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

# Cerebras key pool round-robin 计数器
_cerebras_key_index = 0

# Cerebras 熔断器：连续失败 N 次后自动跳过，避免浪费时间
_cerebras_consecutive_fails = 0
_CEREBRAS_CIRCUIT_BREAKER_THRESHOLD = 3


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


def _jina_scrape(url, timeout=10):
    """使用 Jina Reader 抓取网页内容（纯文本）"""
    jina_url = f"https://r.jina.ai/{url}"
    req = urllib.request.Request(
        jina_url,
        headers={
            "Accept": "text/plain",
            "User-Agent": "Mozilla/5.0 (compatible; AILabBot/1.0)",
        },
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
    global _cerebras_consecutive_fails

    # ── 尝试 Cerebras（极速推理）── 熔断器未打开时才尝试
    if _cerebras_consecutive_fails < _CEREBRAS_CIRCUIT_BREAKER_THRESHOLD:
        cerebras_key = _get_cerebras_key()
        if cerebras_key:
            payload = json.dumps({
                "model": _CEREBRAS_MODEL,
                "messages": [
                    {"role": "system", "content": "/no_think\n" + system_msg},
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
                    "User-Agent": _CEREBRAS_USER_AGENT,
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                text = (data["choices"][0]["message"].get("content") or "").strip()
                # qwen-3-32b 推理模型：剥离 <think>...</think> 标签
                text = re.sub(r'<think>[\s\S]*?</think>\s*', '', text).strip()
                if text:
                    _cerebras_consecutive_fails = 0  # 成功，重置计数器
                    logger.info("LLM call via Cerebras OK (%d chars)", len(text))
                    return text
            except Exception as e:
                _cerebras_consecutive_fails += 1
                logger.warning(
                    "Cerebras failed (%d/%d, key=%s...): %s",
                    _cerebras_consecutive_fails,
                    _CEREBRAS_CIRCUIT_BREAKER_THRESHOLD,
                    cerebras_key[:12],
                    e,
                )
    else:
        logger.debug("Cerebras circuit breaker OPEN (fails=%d), skipping to DeepSeek", _cerebras_consecutive_fails)

    # ── 降级到 DeepSeek ──
    api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
    base_url = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    if not api_key:
        return None

    payload = json.dumps({
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "thinking": {"type": "disabled"},
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
        text = data["choices"][0]["message"]["content"].strip()
        logger.info("LLM call via DeepSeek fallback OK (%d chars)", len(text))
        return text
    except Exception as e:
        logger.warning("DeepSeek LLM call also failed: %s", e)
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


def _ai_extract(title, content, ref_id, url, focus=""):
    """使用 Cerebras/DeepSeek 对网页内容做结构化提取"""
    focus_block = ""
    if focus:
        focus_block = f"\n【检索重点】\n{focus}\n请围绕上述重点提取信息，忽略无关内容。\n"
    prompt = _EXTRACT_PROMPT_TEMPLATE.format(
        ref_id=ref_id,
        title=title,
        url=url,
        content=content[:6000],
    )
    # 将 focus 插入到 prompt 开头（在正文之前）
    if focus_block:
        prompt = focus_block + "\n" + prompt
    return _llm_call(_EXTRACT_SYSTEM_MSG, prompt, max_tokens=2048, timeout=20)


def _ai_consolidate(summaries, references, query, focus=""):
    """使用 Cerebras/DeepSeek 对多条摘要做综合报告"""
    # 构建引用映射表
    ref_mapping = ""
    for ref_id, url, title, domain in references:
        ref_mapping += f"- [REF:{ref_id}] {url}\n"

    # 构建待综合内容
    combined = ""
    for s in summaries:
        combined += f"\n--- [REF:{s['ref_id']}] {s['title']} ---\n{s['content']}\n"

    focus_block = ""
    if focus:
        focus_block = f"\n【用户关注重点】\n{focus}\n请围绕上述重点组织综合报告，优先呈现相关内容。\n\n"

    prompt = _CONSOLIDATE_PROMPT_TEMPLATE.format(
        query=query,
        ref_mapping=ref_mapping,
        content=combined,
    )
    if focus_block:
        prompt = focus_block + prompt
    return _llm_call(_CONSOLIDATE_SYSTEM_MSG, prompt, max_tokens=4096, timeout=45)


def handle_web_search(query="", search_type="search", max_results=5, focus="", **kwargs):
    """增强版 web_search（generator）：搜索 + 抓取 + AI 摘要 + 引用标记
    yield {"progress": msg} 报告阶段进度，yield {"result": text} 返回最终结果。
    """
    query = query.strip()
    if not query:
        raise ValueError("搜索关键词不能为空")

    max_results = max(1, min(10, int(max_results)))

    # ── 1. 双引擎搜索：Google CSE → Serper ──
    yield {"progress": "正在搜索..."}
    search_results = None

    if search_type != "news":
        search_results = _search_google_cse(query, num=max_results)
        if search_results:
            logger.info("Search via Google CSE: %d results", len(search_results))

    if not search_results:
        search_results = _search_serper(query, search_type=search_type, num=max_results)
        if search_results:
            logger.info("Search via Serper: %d results", len(search_results))

    if not search_results:
        raise ValueError("搜索引擎均不可用，请检查 API 配置")

    # ── 2. 构建引用列表 & 清理 URL（使用全局引用计数器，避免多次调用编号重叠） ──
    references = []
    for item in search_results[:max_results]:
        ref_id = _next_ref_id()
        url = _normalize_url(item.get("link", ""))
        title = item.get("title", "无标题")
        domain = _extract_domain(url)
        references.append((ref_id, url, title, domain))
        _collect_ref(ref_id, url, title, domain)

    # ── 3. Jina Reader 并行抓取 ──
    scrape_refs = references[:_SCRAPE_TOP_N]

    # 构建 URL 进度追踪列表 — 供前端渲染 favicon 标签
    url_progress = [
        {"ref_id": ref_id, "domain": domain, "status": "pending"}
        for ref_id, url, title, domain in scrape_refs
    ]

    yield {
        "progress": f"找到 {len(references)} 条结果，正在抓取 {len(scrape_refs)} 个网页...",
        "urls": [dict(u) for u in url_progress],
    }

    scraped = []
    scrape_status = {}

    to_scrape = [(r, s) for r, s in zip(scrape_refs, search_results) if r[1]]
    for ref_id, url, title, domain in scrape_refs:
        if not url:
            scrape_status[ref_id] = 'skipped'

    done_count = 0
    total_to_scrape = len(to_scrape)
    with ThreadPoolExecutor(max_workers=max(total_to_scrape, 1)) as pool:
        future_map = {}
        for (ref_id, url, title, domain), sr in to_scrape:
            future_map[pool.submit(_jina_scrape, url)] = (ref_id, url, title, domain, sr)

        for future in as_completed(future_map):
            ref_id, url, title, domain, sr = future_map[future]
            content = future.result()
            done_count += 1
            ok = content and len(content) > 100
            if ok:
                scraped.append({"ref_id": ref_id, "title": title, "content": content, "url": url})
                scrape_status[ref_id] = 'scraped'
            else:
                snippet = sr.get("snippet", "")
                if snippet:
                    scraped.append({"ref_id": ref_id, "title": title, "content": snippet, "url": url})
                scrape_status[ref_id] = 'snippet'
            # 更新 URL 进度状态
            for u in url_progress:
                if u["ref_id"] == ref_id:
                    u["status"] = "done" if ok else "fail"
            yield {
                "progress": f"正在抓取网页... ({done_count}/{total_to_scrape})",
                "urls": [dict(u) for u in url_progress],
            }

    if _SCRAPE_TOP_N is not None:
        for ref_id, url, title, domain in references[_SCRAPE_TOP_N:]:
            scrape_status[ref_id] = 'skipped'

    scraped_count = sum(1 for s in scrape_status.values() if s == 'scraped')

    # ── 4. Cerebras/DeepSeek 并行结构化提取 ──
    # 重置进度列表用于提取阶段
    extract_url_progress = [
        {"ref_id": it["ref_id"], "domain": _extract_domain(it["url"]), "status": "pending"}
        for it in scraped
    ]
    yield {
        "progress": f"已抓取 {scraped_count} 个网页，AI 正在提取关键信息...",
        "urls": [dict(u) for u in extract_url_progress],
    }

    summaries = []
    if scraped:
        extract_done = 0
        total_extract = len(scraped)
        with ThreadPoolExecutor(max_workers=total_extract) as pool:
            future_map = {
                pool.submit(_ai_extract, it["title"], it["content"], it["ref_id"], it["url"], focus): it
                for it in scraped
            }
            for future in as_completed(future_map):
                item = future_map[future]
                extracted = future.result()
                extract_done += 1
                if extracted:
                    summaries.append({
                        "ref_id": item["ref_id"],
                        "title": item["title"],
                        "content": extracted,
                    })
                else:
                    summaries.append({
                        "ref_id": item["ref_id"],
                        "title": item["title"],
                        "content": item["content"][:500],
                    })
                # 更新提取进度
                for u in extract_url_progress:
                    if u["ref_id"] == item["ref_id"]:
                        u["status"] = "done" if extracted else "fail"
                yield {
                    "progress": f"AI 正在提取关键信息... ({extract_done}/{total_extract})",
                    "urls": [dict(u) for u in extract_url_progress],
                }
        summaries.sort(key=lambda s: s["ref_id"])

    # ── 构建输出辅助块 ──
    status_lines = [f"🔍 搜索「{query}」| {len(references)} 条结果，已抓取 {scraped_count} 个网页\n"]
    for ref_id, url, title, domain in references:
        st = scrape_status.get(ref_id, 'skipped')
        if st == 'scraped':
            status_lines.append(f"  [REF:{ref_id}] {domain} ✅")
        elif st == 'snippet':
            status_lines.append(f"  [REF:{ref_id}] {domain} ⚠️ 仅摘要")
        else:
            status_lines.append(f"  [REF:{ref_id}] {domain}")
    scrape_header = "\n".join(status_lines) + "\n\n"

    ref_lines = ["### 引用来源"]
    for ref_id, url, title, domain in references:
        ref_lines.append(f"[REF:{ref_id}] {title} - {url}")
    ref_block = "\n".join(ref_lines)

    # ── 5. Consolidation ──
    total_summary_len = sum(len(s["content"]) for s in summaries)

    if len(summaries) >= 2 and total_summary_len > 500:
        yield {"progress": "正在生成综合报告..."}
        consolidated = _ai_consolidate(summaries, references, query, focus)
        if consolidated:
            yield {"result": scrape_header + consolidated + "\n\n" + ref_block}
            return

    # ── 6. 降级：直接拼接摘要 + 引用列表 ──
    lines = [scrape_header]

    if summaries:
        for s in summaries:
            lines.append(f"**[REF:{s['ref_id']}] {s['title']}**")
            lines.append(s["content"])
            lines.append("")
    else:
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

    lines.append(ref_block)
    yield {"result": "\n".join(lines)}


# ==================== 工具映射 & 统一执行入口 ====================

TOOL_HANDLERS = {
    "get_current_datetime": handle_get_current_datetime,
    "calculator": handle_calculator,
    "web_search": handle_web_search,
}


def execute_tool(name, args):
    """非流式执行入口，返回 (result_str, error_str)。兼容 generator 工具。"""
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return None, f"未知工具: {name}"
    try:
        result = handler(**args)
        if hasattr(result, '__next__'):
            final = None
            for event in result:
                if "result" in event:
                    final = event["result"]
                elif "error" in event:
                    return None, event["error"]
            return str(final) if final is not None else None, None
        return str(result), None
    except Exception as exc:
        return None, str(exc)


def execute_tool_streaming(name, args):
    """流式执行入口（generator），yield {"progress": msg} 或 {"result": str} 或 {"error": str}。"""
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        yield {"error": f"未知工具: {name}"}
        return
    try:
        result = handler(**args)
        if hasattr(result, '__next__'):
            for event in result:
                yield event
        else:
            yield {"result": str(result)}
    except Exception as exc:
        yield {"error": str(exc)}
