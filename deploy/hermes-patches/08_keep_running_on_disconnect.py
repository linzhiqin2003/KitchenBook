"""Stop killing the agent when the SSE client disconnects.

Today, if the user closes the browser tab mid-stream, the SSE writer
catches ConnectionResetError, calls ``agent.interrupt()`` and cancels
the asyncio task — the agent's work is lost.  Frontend never gets to
POST the assistant message back to Django, so when the user reopens
the page the answer is gone.

This patch lets the agent finish in the background.  When the SSE
writer detects the client is gone, it schedules a small async watcher
that:
  1. Awaits the still-running agent_task to completion.
  2. POSTs the final assistant reply to the Django internal endpoint
     ``/api/ai/conversations/<id>/messages/internal/`` with a shared
     secret + the user-id header so the message lands in the right
     conversation.

Required env vars on the Hermes systemd unit (or .env):
  HERMES_INTERNAL_TOKEN  — same value as Django's HERMES_INTERNAL_TOKEN
  DJANGO_BASE_URL        — e.g. http://127.0.0.1:8000

Idempotent."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path

P = Path("/home/admin/.hermes/hermes-agent/gateway/platforms/api_server.py")
SENTINEL = "_schedule_post_result_to_django"


HELPER = '''
async def _schedule_post_result_to_django(
    agent_task,
    *,
    user_id: str,
    conversation_id: str,
    model_name: str,
    completion_id: str,
):
    """Background watcher invoked when the SSE client disconnects but we
    want the agent to keep running.

    Awaits ``agent_task``, then POSTs the final response to the AI Lab
    Django backend so the user sees it on their next page load.
    """
    import os as _os
    import json as _json
    try:
        result, _usage = await agent_task
    except asyncio.CancelledError:
        return
    except Exception as exc:
        logger.warning("[ailab-bg] agent task failed after disconnect (%s): %s", completion_id, exc)
        return

    final_response = ""
    try:
        final_response = (result or {}).get("final_response") or ""
    except Exception:
        pass
    if not final_response:
        logger.info("[ailab-bg] no final_response; nothing to post (%s)", completion_id)
        return

    token = (_os.environ.get("HERMES_INTERNAL_TOKEN") or "").strip()
    base_url = (_os.environ.get("DJANGO_BASE_URL") or "http://127.0.0.1:8000").rstrip("/")
    if not token:
        logger.warning("[ailab-bg] HERMES_INTERNAL_TOKEN not configured; skipping post-back")
        return
    if not user_id or not conversation_id:
        logger.info("[ailab-bg] missing user_id/conversation_id; skipping post-back (%s)", completion_id)
        return

    url = f"{base_url}/api/ai/conversations/{conversation_id}/messages/internal/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Hermes-User-Id": str(user_id),
    }
    payload = {
        "role": "assistant",
        "content": final_response,
        "model_name": model_name or "Hermes",
    }
    try:
        import aiohttp as _aiohttp
        async with _aiohttp.ClientSession() as sess:
            async with sess.post(url, json=payload, headers=headers, timeout=30) as r:
                if r.status >= 400:
                    body = await r.text()
                    logger.warning("[ailab-bg] Django post returned %s: %s", r.status, body[:200])
                else:
                    logger.info("[ailab-bg] saved completion %s to conversation %s", completion_id, conversation_id)
    except Exception as exc:
        logger.warning("[ailab-bg] Django post-back failed: %s", exc)
'''


# Replace the entire disconnect-handler block in _write_sse_chat_completion.
OLD_DISCONNECT_BLOCK = (
    '        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):\n'
    '            # Client disconnected mid-stream.  Interrupt the agent so it\n'
    '            # stops making LLM API calls at the next loop iteration, then\n'
    '            # cancel the asyncio task wrapper.\n'
    '            agent = agent_ref[0] if agent_ref else None\n'
    '            if agent is not None:\n'
    '                try:\n'
    '                    agent.interrupt("SSE client disconnected")\n'
    '                except Exception:\n'
    '                    pass\n'
    '            if not agent_task.done():\n'
    '                agent_task.cancel()\n'
    '                try:\n'
    '                    await agent_task\n'
    '                except (asyncio.CancelledError, Exception):\n'
    '                    pass\n'
    '            logger.info("SSE client disconnected; interrupted agent task %s", completion_id)\n'
    '\n'
    '        return response\n'
)

NEW_DISCONNECT_BLOCK = (
    '        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):\n'
    '            # Client disconnected mid-stream — DO NOT interrupt the agent.\n'
    '            # The user wants their work to survive a closed tab; let the\n'
    '            # task run to completion in the background and POST the final\n'
    '            # answer back to Django so the next page load shows it.\n'
    '            ailab_user_id = (request.headers.get("X-Hermes-User-Id") or "").strip()\n'
    '            ailab_conv_id = (request.headers.get("X-AILab-Conversation-Id") or "").strip()\n'
    '            if not agent_task.done() and ailab_user_id and ailab_conv_id:\n'
    '                asyncio.ensure_future(_schedule_post_result_to_django(\n'
    '                    agent_task,\n'
    '                    user_id=ailab_user_id,\n'
    '                    conversation_id=ailab_conv_id,\n'
    '                    model_name=model,\n'
    '                    completion_id=completion_id,\n'
    '                ))\n'
    '                logger.info(\n'
    '                    "[ailab-bg] SSE disconnected, agent_task %s left running for conv=%s user=%s",\n'
    '                    completion_id, ailab_conv_id, ailab_user_id,\n'
    '                )\n'
    '            else:\n'
    '                # No AI Lab routing info; old behavior — interrupt to save tokens\n'
    '                agent = agent_ref[0] if agent_ref else None\n'
    '                if agent is not None:\n'
    '                    try:\n'
    '                        agent.interrupt("SSE client disconnected")\n'
    '                    except Exception:\n'
    '                        pass\n'
    '                if not agent_task.done():\n'
    '                    agent_task.cancel()\n'
    '                    try:\n'
    '                        await agent_task\n'
    '                    except (asyncio.CancelledError, Exception):\n'
    '                        pass\n'
    '                logger.info("SSE client disconnected; interrupted agent task %s", completion_id)\n'
    '\n'
    '        return response\n'
)


def main() -> int:
    text = P.read_text()
    if SENTINEL in text:
        print("[skip] already patched")
        return 0

    # 1) Insert the helper near top of the module — placed just before the
    #    APIServerAdapter class, after the existing per-user helpers.
    anchor = "class APIServerAdapter(BasePlatformAdapter):"
    if text.count(anchor) != 1:
        print(f"FATAL: expected 1 APIServerAdapter, found {text.count(anchor)}", file=sys.stderr)
        return 2
    text = text.replace(anchor, HELPER + "\n" + anchor, 1)

    # 2) Replace disconnect handler in _write_sse_chat_completion only —
    #    /v1/responses path uses a different writer; leave it untouched.
    n = text.count(OLD_DISCONNECT_BLOCK)
    if n == 0:
        print("FATAL: disconnect block anchor not found", file=sys.stderr)
        return 2
    if n != 1:
        print(f"WARN: matched {n} occurrences; replacing all", file=sys.stderr)
    text = text.replace(OLD_DISCONNECT_BLOCK, NEW_DISCONNECT_BLOCK)

    bak = P.with_suffix(P.suffix + ".keepalive.bak")
    if not bak.exists():
        shutil.copy2(P, bak)
        print(f"backup -> {bak.name}")
    P.write_text(text)
    import ast
    try:
        ast.parse(P.read_text(), str(P))
        print("AST ok")
    except SyntaxError as e:
        print(f"AST FAIL: {e}", file=sys.stderr)
        return 3
    print(f"patched ({n} disconnect block(s) rewritten)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
