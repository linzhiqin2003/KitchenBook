"""Route xiaomi-provider vision tasks to mimo-v2-omni, not mimo-v2.5.

The ``_PROVIDER_VISION_MODELS`` table in agent/auxiliary_client.py maps
the *main provider* to the model auxiliary vision tasks should hit
when the main chat model isn't multimodal.  For ``xiaomi`` it currently
points to ``mimo-v2.5``, which is text-only — sending the standard
OpenAI ``image_url`` content part to it returns::

    400 - 'unknown variant `image_url`, expected `text`'

That's xiaomi's serde rejecting structured content parts because the
target model can't accept them.  The actually-multimodal model in the
MiMo lineup is ``mimo-v2-omni`` (Hermes already special-cases it on
line 1796 as the only mimo vision target).  Repoint the mapping.

Idempotent — keyed off SENTINEL appearing in the file."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/agent/auxiliary_client.py")
SENTINEL = '"xiaomi": "mimo-v2-omni"'

OLD = '    "xiaomi": "mimo-v2.5",\n'
NEW = '    "xiaomi": "mimo-v2-omni",  # patch14: omni is the only multimodal mimo\n'


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("  [skip] already patched")
        return 0
    if OLD not in text:
        print("FATAL: anchor not found", file=sys.stderr)
        return 2
    if text.count(OLD) != 1:
        print(f"FATAL: anchor matched {text.count(OLD)} times", file=sys.stderr)
        return 2
    bak = P.with_suffix(P.suffix + ".vismap.bak")
    if not bak.exists():
        shutil.copy2(P, bak)
        print(f"  backup -> {bak.name}")
    P.write_text(text.replace(OLD, NEW))
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
