"""Add an explicit ``view_image`` tool that loads a local image into the
agent's context, then unwraps it into a multipart user message so the
main multimodal model can actually see the pixels in the next turn.

Why a dedicated tool (vs. patch15 + auto-attach)?
  - The existing ``vision_analyze`` tool ships images to a *separate*
    chat completion (often a different model), then returns a text
    description. Two round-trips, the main model never reasons on
    pixels itself.
  - Auto-attaching every path mention silently rewrites the user's
    message — surprising behaviour, no trace, hard to debug.
  - The agent already operates the file system via its other tools
    (terminal, Read, etc). Asking it to call ``view_image(path)``
    explicitly to "load this picture for me to look at" is the
    natural pattern, mirrors how a human assistant would describe
    looking at a file.

Mechanics:
  - Register a ``view_image`` tool in ``tools/vision_tools.py``
    alongside ``vision_analyze``.
  - Handler reads the file, base64-encodes it, returns a marker
    string: a JSON payload tagged with ``__hermes_view_image__: true``
    and the data URL.
  - Hook ``_build_api_kwargs`` in ``run_agent.py`` to scan the
    messages right before each chat completion. When it finds a
    tool result with that marker:
      1. replace the tool message body with a short success line
         (so the model still sees a clean tool result string and
         the spec is satisfied — tool role stays text-only),
      2. insert a synthetic ``user`` message immediately after with
         the image attached as an ``image_url`` content part.
  - On the next turn the model sees: tool result "Image loaded."
    followed by the user-role image. It then reasons on the pixels
    directly — no second round-trip, no hidden auto-magic.

Skipped for ``api_mode in {anthropic_messages, bedrock_converse}``
since those have native ``image`` content blocks the next adapter
should hold onto independently.

Idempotent — keyed off SENTINEL appearing in each file.
"""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

VT = Path("/home/admin/.hermes/hermes-agent/tools/vision_tools.py")
RA = Path("/home/admin/.hermes/hermes-agent/run_agent.py")
SENTINEL_VT = "# [patch16-view] view_image tool"
SENTINEL_RA = "# [patch16-view] view_image inline-rewrite"


# ── tools/vision_tools.py: register a new tool at the bottom ─────────

VT_APPEND = '''

# [patch16-view] view_image tool — reads a local image and hands it to
# the main multimodal model via a synthetic user message (rewritten in
# run_agent._build_api_kwargs). The tool itself just packages the data
# URL into a marker payload that the rewrite step understands.
import base64 as _p16v_b64
import json as _p16v_json
from pathlib import Path as _p16vPath

_P16V_MAX_BYTES = 10 * 1024 * 1024  # 10 MiB hard cap
_P16V_MIME = {
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
}

VIEW_IMAGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "view_image",
        "description": (
            "Load a local image file into your visual context so you can see "
            "it on the next turn. Use this when the user references a picture "
            "by path (e.g. \\"看一下 /tmp/cat.png\\"), or when you generated "
            "an image with image_generate / image_gen and want to reason on "
            "the pixels yourself. After this call returns, the next user "
            "message will carry the image inline; describe what you see in "
            "your reply."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Absolute path to the image (PNG / JPEG / GIF / WEBP / BMP).",
                },
            },
            "required": ["image_path"],
        },
    },
}


def _handle_view_image(args, **kw):
    raw_path = (args.get("image_path") or "").strip()
    if not raw_path:
        return tool_error("image_path is required")
    try:
        path = _p16vPath(raw_path).expanduser()
    except Exception as e:
        return tool_error(f"invalid path: {e}")
    if not path.is_absolute():
        return tool_error("image_path must be absolute")
    if not path.is_file():
        return tool_error(f"file not found: {path}")
    try:
        size = path.stat().st_size
    except OSError as e:
        return tool_error(f"stat failed: {e}")
    if size <= 0:
        return tool_error("file is empty")
    if size > _P16V_MAX_BYTES:
        return tool_error(f"file too large ({size} bytes; cap {_P16V_MAX_BYTES})")
    ext = path.suffix.lower().lstrip(".")
    mime = _P16V_MIME.get(ext)
    if not mime:
        return tool_error(f"unsupported image extension: .{ext}")
    try:
        b64 = _p16v_b64.b64encode(path.read_bytes()).decode("ascii")
    except Exception as e:
        return tool_error(f"read failed: {e}")
    payload = {
        "__hermes_view_image__": True,
        "path": str(path),
        "size": size,
        "mime": mime,
        "data_url": f"data:{mime};base64,{b64}",
    }
    return _p16v_json.dumps(payload)


registry.register(
    name="view_image",
    toolset="vision",
    schema=VIEW_IMAGE_SCHEMA,
    handler=_handle_view_image,
    is_async=False,
    emoji="\U0001f5bc️",
)
'''


# ── run_agent.py: rewrite tool results + inject synthetic user msg ───

# Helper block — placed once near the top of run_agent.py.
RA_HELPER_OLD = "class AIAgent:\n"
RA_HELPER_NEW = '''# [patch16-view] view_image inline-rewrite — pull the data URL out of
# the tool result payload and inject a synthetic user message with
# image_url so the model sees pixels on its next reasoning step.
import json as _p16v_run_json


def _p16v_rewrite_view_image_messages(api_messages, api_mode):
    """Mutate api_messages: convert any view_image tool result whose
    body is the marker JSON into (a) a clean tool-role success string,
    (b) a fresh user-role multipart message right after carrying the
    image as an image_url content part.

    Idempotent — once a tool message has been rewritten its content no
    longer parses as the marker, so subsequent calls are no-ops.
    """
    if api_mode in {"anthropic_messages", "bedrock_converse"}:
        return  # native image blocks live in those transports
    if not isinstance(api_messages, list) or not api_messages:
        return
    out = []
    for msg in api_messages:
        out.append(msg)
        if not isinstance(msg, dict):
            continue
        if msg.get("role") != "tool":
            continue
        body = msg.get("content")
        if not isinstance(body, str) or "__hermes_view_image__" not in body:
            continue
        try:
            payload = _p16v_run_json.loads(body)
        except Exception:
            continue
        if not isinstance(payload, dict) or not payload.get("__hermes_view_image__"):
            continue
        data_url = payload.get("data_url")
        if not isinstance(data_url, str) or not data_url.startswith("data:"):
            continue
        path = payload.get("path", "")
        size = payload.get("size", 0)
        # Replace tool body with a short, deterministic success line.
        msg["content"] = (
            f"Image loaded: {path} ({size} bytes). The image is shown in the "
            "next user message — describe what you see."
        )
        # Append synthetic user message with the actual image bytes.
        out.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": (
                    "[Above is the image you loaded with view_image. "
                    "Continue your previous response based on what you see.]"
                )},
            ],
        })
    api_messages[:] = out


class AIAgent:
'''

# Hook _build_api_kwargs at its top.
RA_HOOK_OLD = (
    "    def _build_api_kwargs(self, api_messages: list) -> dict:\n"
    '        """Build the keyword arguments dict for the active API mode."""\n'
)
RA_HOOK_NEW = (
    "    def _build_api_kwargs(self, api_messages: list) -> dict:\n"
    '        """Build the keyword arguments dict for the active API mode."""\n'
    "        # [patch16-view] unwrap view_image tool results into image_url parts\n"
    "        try:\n"
    "            _p16v_rewrite_view_image_messages(api_messages, getattr(self, \"api_mode\", \"\"))\n"
    "        except Exception:\n"
    "            pass\n"
)


def patch_file(path, anchors, sentinel):
    text = path.read_text()
    if sentinel in text:
        print(f"  [skip] {path.name} already patched")
        return True
    bak = path.with_suffix(path.suffix + ".p16v.bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        print(f"  backup -> {bak.name}")
    for old, new, label in anchors:
        if new in text:
            print(f"  [skip] {label}")
            continue
        if old not in text:
            print(f"FATAL: anchor missing: {label}", file=sys.stderr)
            return False
        if text.count(old) != 1:
            print(f"FATAL: anchor matched {text.count(old)}x: {label}", file=sys.stderr)
            return False
        text = text.replace(old, new, 1)
        print(f"  [done] {label}")
    path.write_text(text)
    import ast
    try:
        ast.parse(path.read_text(), str(path))
        print(f"  AST ok ({path.name})")
        return True
    except SyntaxError as e:
        print(f"AST FAIL: {e}", file=sys.stderr)
        shutil.copy2(bak, path)
        return False


def main() -> int:
    ok = True
    # 1) Append view_image tool registration at end of vision_tools.py
    vt_text = VT.read_text()
    if SENTINEL_VT not in vt_text:
        bak = VT.with_suffix(VT.suffix + ".p16v.bak")
        if not bak.exists():
            shutil.copy2(VT, bak)
            print(f"  backup -> {bak.name}")
        VT.write_text(vt_text.rstrip() + "\n" + VT_APPEND)
        import ast
        try:
            ast.parse(VT.read_text(), str(VT))
            print(f"  AST ok ({VT.name})")
        except SyntaxError as e:
            print(f"AST FAIL: {e}", file=sys.stderr)
            shutil.copy2(bak, VT)
            ok = False
        else:
            print(f"  [done] vision_tools.py: appended view_image registration")
    else:
        print(f"  [skip] {VT.name} already patched")

    # 2) Patch run_agent.py — helper block + _build_api_kwargs hook
    ok = patch_file(
        RA,
        [
            (RA_HELPER_OLD, RA_HELPER_NEW, "run_agent.py: helper block"),
            (RA_HOOK_OLD, RA_HOOK_NEW, "run_agent.py: _build_api_kwargs hook"),
        ],
        SENTINEL_RA,
    ) and ok

    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
