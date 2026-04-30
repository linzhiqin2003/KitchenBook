"""Auto-inject local image files into messages content parts when the
main model is multimodal — so the agent "sees" pixels directly without
fanning out to vision_analyze.

Bug surfaced in chat: when the main model is mimo-v2.5 (or any other
multimodal model), the agent still calls ``vision_analyze`` on local
image paths it knows about (e.g. /tmp/foo.png from image_gen). That
tool opens a *separate* chat completion to ask "another instance" of
the same model to describe the image, which is ergonomically weird
and wastes a round-trip when the main model could have just looked
at the picture itself.

Fix: at the entry of ``_build_api_kwargs``, scan the chat messages
for absolute paths to image files. If the main model is in the
multimodal whitelist, expand each message's string content into a
multipart ``[{type:"text",...}, {type:"image_url",...}]`` form with
the image inlined as a base64 data URL. The model now receives both
the text and the picture in the same call.

Constraints:
  - Only fires for OpenAI-compatible mode (skip anthropic_messages /
    bedrock_converse — those have their own image conventions).
  - Whitelist of multimodal model name patterns (mimo-v2.5,
    mimo-v2-omni, gpt-4o, gpt-4-turbo, claude-3.5+, gemini-*, qwen-vl,
    glm-5v, llava, pixtral). Easy to extend.
  - Per-call cap: max 6 images attached, ≤ 5 MiB each. Larger files
    or excess matches stay as plain text references.
  - Dedupe by absolute path within a single api_kwargs build so the
    same image isn't repeated across consecutive messages.
  - File is base64-encoded with the right MIME type (png/jpeg/gif/
    webp/bmp). Unreadable / nonexistent paths are left alone.
  - Idempotent on re-runs: messages already in multipart form are
    skipped wholesale.

This installs as an *instance method* shim plus a wrapped
_build_api_kwargs that delegates to the original after rewriting
api_messages.

Idempotent — keyed off SENTINEL appearing in the file."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/run_agent.py")
SENTINEL = "# [patch16] auto-attach local images for multimodal main models"


HELPER_BLOCK = '''
# [patch16] auto-attach local images for multimodal main models
import base64 as _p16_b64
import re as _p16_re
from pathlib import Path as _P16Path

_P16_MULTIMODAL_RE = _p16_re.compile(
    r"(mimo-v2\\.5|mimo-v2-omni|mimo-v2-pro|"
    r"gpt-4o|gpt-4-turbo|gpt-4-vision|gpt-5|"
    r"claude-3\\.5|claude-3\\.7|claude-4|claude-opus|claude-sonnet|claude-haiku|"
    r"gemini-|qwen-vl|qwen2-vl|qwen3-vl|llava|pixtral|glm-5v)",
    _p16_re.IGNORECASE,
)
_P16_PATH_RE = _p16_re.compile(
    r"(?<![/\\w:.\\-])(/(?:[\\w.\\-]+/)+[\\w.\\-]+\\.(?:png|jpe?g|gif|webp|bmp))\\b",
    _p16_re.IGNORECASE,
)
_P16_MIME = {
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
}
_P16_MAX_BYTES = 5 * 1024 * 1024
_P16_MAX_ATTACH = 6


def _p16_is_multimodal(model_name) -> bool:
    if not model_name:
        return False
    return bool(_P16_MULTIMODAL_RE.search(str(model_name)))


def _p16_file_to_data_url(p):
    try:
        path = _P16Path(p)
        if not path.is_absolute() or not path.is_file():
            return None
        size = path.stat().st_size
        if size <= 0 or size > _P16_MAX_BYTES:
            return None
        ext = path.suffix.lower().lstrip(".")
        mime = _P16_MIME.get(ext)
        if not mime:
            return None
        b64 = _p16_b64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


def _p16_attach_images(api_messages, model_name, api_mode):
    """Mutate api_messages in place: convert string content to multipart
    [text, image_url, ...] when an absolute image path is mentioned."""
    if api_mode in {"anthropic_messages", "bedrock_converse"}:
        return  # those modes have their own multimodal conventions
    if not _p16_is_multimodal(model_name):
        return
    if not isinstance(api_messages, list):
        return
    seen = set()
    attached = 0
    for msg in api_messages:
        if attached >= _P16_MAX_ATTACH:
            return
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if not isinstance(content, str) or not content:
            continue
        # Skip if no candidate path
        candidates = list(dict.fromkeys(_P16_PATH_RE.findall(content)))
        if not candidates:
            continue
        new_parts = [{"type": "text", "text": content}]
        for raw in candidates:
            if attached >= _P16_MAX_ATTACH:
                break
            if raw in seen:
                continue
            data_url = _p16_file_to_data_url(raw)
            if data_url is None:
                continue
            new_parts.append({"type": "image_url", "image_url": {"url": data_url}})
            seen.add(raw)
            attached += 1
        if len(new_parts) > 1:
            msg["content"] = new_parts
'''


# Insert the helper block immediately before the AIAgent class (or near top of module).
# Anchor: a stable-looking line near the top of run_agent.py that appears exactly once.

ANCHOR_INSERT = "class AIAgent:\n"
INSERT_NEW = HELPER_BLOCK + "\n\nclass AIAgent:\n"

# Wrap _build_api_kwargs by inserting auto-attach call at its start.
ANCHOR_WRAP = (
    "    def _build_api_kwargs(self, api_messages: list) -> dict:\n"
    '        """Build the keyword arguments dict for the active API mode."""\n'
)
WRAP_NEW = (
    "    def _build_api_kwargs(self, api_messages: list) -> dict:\n"
    '        """Build the keyword arguments dict for the active API mode."""\n'
    "        # [patch16] inject local image files when main model is multimodal\n"
    "        try:\n"
    "            _p16_attach_images(api_messages, getattr(self, \"model\", \"\"), getattr(self, \"api_mode\", \"\"))\n"
    "        except Exception:\n"
    "            pass\n"
)


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("  [skip] already patched")
        return 0

    if ANCHOR_INSERT not in text:
        print("FATAL: AIAgent class anchor not found", file=sys.stderr)
        return 2
    if text.count(ANCHOR_INSERT) != 1:
        print(f"FATAL: AIAgent anchor matched {text.count(ANCHOR_INSERT)} times", file=sys.stderr)
        return 2
    if ANCHOR_WRAP not in text:
        print("FATAL: _build_api_kwargs anchor not found", file=sys.stderr)
        return 2
    if text.count(ANCHOR_WRAP) != 1:
        print(f"FATAL: _build_api_kwargs anchor matched {text.count(ANCHOR_WRAP)} times", file=sys.stderr)
        return 2

    bak = P.with_suffix(P.suffix + ".p16.bak")
    if not bak.exists():
        shutil.copy2(P, bak)
        print(f"  backup -> {bak.name}")

    text = text.replace(ANCHOR_INSERT, INSERT_NEW, 1)
    text = text.replace(ANCHOR_WRAP, WRAP_NEW, 1)
    P.write_text(text)

    import ast
    try:
        ast.parse(P.read_text(), str(P))
        print("  AST ok")
    except SyntaxError as e:
        print(f"AST FAIL: {e}", file=sys.stderr)
        shutil.copy2(bak, P)
        return 3
    print("  patched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
