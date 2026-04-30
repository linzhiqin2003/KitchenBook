"""把 agent 消息里的本地文件路径 hardlink 到 MEDIA/ailab/ 并改写为公网 URL。

复刻 Hermes 平台层 ``extract_local_files`` 的语义，但走 Django MEDIA 而不是
平台 send_image_file API —— 因为 web 客户端拿到的是 markdown 文本，需要
URL 才能渲染成 ``<img>``。

规则：
  - 仅匹配绝对路径（``/foo/bar.png``）或 ``~/foo`` （本函数只处理绝对，~由
    上层展开），扩展名是常见 image / pdf / 视频
  - 跳过已经在 MEDIA_ROOT 内的路径（避免无限套娃）
  - 跳过 URL 上下文里的路径（``https://x/y.png`` 不该被改）—— 用 negative
    lookbehind 防 URL chars 前缀
  - 一条消息里同一路径只发布一次（dedupe）
  - 跨文件系统时回退到 ``shutil.copy2``；同 fs 优先 hardlink（零空间）
"""

from __future__ import annotations

import logging
import os
import re
import secrets
import shutil
import time
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


_PUBLISH_SUBDIR = "ailab"
_DEFAULT_BASE_URL = "/media/ailab"
_PUBLISHED_EXTS = (
    "png", "jpg", "jpeg", "gif", "webp",
    "pdf",
    "mp4", "mov", "webm", "mkv",
)

# 匹配绝对路径到目标后缀；前面不能是 URL 字符或路径字符（避免吃 URL 中段或更长路径的子串）
_PATH_RE = re.compile(
    r"(?<![/\w:.\-])(/(?:[\w.\-]+/)+[\w.\-]+\.(?:" + "|".join(_PUBLISHED_EXTS) + r"))\b",
    re.IGNORECASE,
)
_MEDIA_TAG_RE = re.compile(
    r"MEDIA:\s*([^\s)]+)",
    re.IGNORECASE,
)


def _publish_dir() -> Path:
    return Path(settings.MEDIA_ROOT) / _PUBLISH_SUBDIR


def _base_url() -> str:
    return getattr(settings, "AILAB_PUBLISH_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")


def _is_under_media(path: Path) -> bool:
    try:
        path.resolve().relative_to(Path(settings.MEDIA_ROOT).resolve())
        return True
    except (ValueError, OSError):
        return False


def publish_local_assets_in_content(content: str) -> str:
    """扫描 content，找到本地资源路径，发布并替换为公网 URL。"""
    if not content or "/" not in content:
        return content

    pub_dir = _publish_dir()
    try:
        pub_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.warning("ailab publish dir mkdir failed: %s", e)
        return content

    base_url = _base_url()
    cache: dict[str, str] = {}

    def _publish_path(path_str: str, original: str) -> str:
        if path_str in cache:
            return cache[path_str]
        try:
            src = Path(path_str)
            if not src.is_absolute():
                return original
            if not src.is_file():
                return original
            if _is_under_media(src):
                return original
            suffix = src.suffix.lower() or ".bin"
            fname = f"{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_urlsafe(6)}{suffix}"
            dst = pub_dir / fname
            try:
                os.link(src, dst)
            except OSError:
                shutil.copy2(src, dst)
            public_url = f"{base_url}/{fname}"
            cache[path_str] = public_url
            logger.info("ailab published %s -> %s", path_str, public_url)
            return public_url
        except Exception as e:
            logger.warning("ailab publish failed for %s: %s", path_str, e)
            return original

    def _replace_media_tag(match: "re.Match[str]") -> str:
        target = (match.group(1) or "").strip()
        if not target:
            return match.group(0)
        if target.startswith(("http://", "https://", "/media/")):
            return target
        return _publish_path(target, match.group(0))

    def _replace_path(match: "re.Match[str]") -> str:
        path_str = match.group(1)
        return _publish_path(path_str, match.group(0))

    content = _MEDIA_TAG_RE.sub(_replace_media_tag, content)
    return _PATH_RE.sub(_replace_path, content)
