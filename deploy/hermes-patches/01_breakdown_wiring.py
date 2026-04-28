"""One-shot patch script: applies the prompt-breakdown changes to a
server-side Hermes checkout in place.

Edits:
  • run_agent.py — add _prompt_segments init; refactor _build_system_prompt
    to track per-bucket text; add compute_prompt_breakdown(); enrich the
    run_conversation result dict.
  • gateway/platforms/api_server.py — surface usage.breakdown in both
    streaming and non-streaming /v1/chat/completions responses.

Idempotent: re-running the script detects already-patched state and skips.
Writes a .bak alongside each modified file on the first run.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path("/home/admin/.hermes/hermes-agent")
RUN_AGENT = ROOT / "run_agent.py"
API_SERVER = ROOT / "gateway/platforms/api_server.py"

SENTINEL = "compute_prompt_breakdown"


def backup_once(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".breakdown.bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        print(f"  backup -> {bak.name}")


def apply_replace(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text()
    if new in text:
        print(f"  [skip] {label}: already applied")
        return
    if old not in text:
        raise SystemExit(
            f"FATAL: anchor for {label} not found in {path}.\n"
            f"Server file may have drifted; aborting before partial patch."
        )
    if text.count(old) != 1:
        raise SystemExit(
            f"FATAL: anchor for {label} matched {text.count(old)} times in {path}; expected 1."
        )
    path.write_text(text.replace(old, new))
    print(f"  [done] {label}")


def patch_run_agent() -> None:
    print(f"== patching {RUN_AGENT.name} ==")
    if SENTINEL in RUN_AGENT.read_text():
        print("  [skip] run_agent.py already patched")
        return
    backup_once(RUN_AGENT)

    # 1) init self._prompt_segments next to _cached_system_prompt
    apply_replace(
        RUN_AGENT,
        "        # Cached system prompt -- built once per session, only rebuilt on compression\n"
        "        self._cached_system_prompt: Optional[str] = None\n",
        "        # Cached system prompt -- built once per session, only rebuilt on compression\n"
        "        self._cached_system_prompt: Optional[str] = None\n"
        "        # Per-bucket system-prompt segments populated by _build_system_prompt().\n"
        "        # Used by compute_prompt_breakdown() to expose a UI-friendly token\n"
        "        # composition (identity / skills / memory / context_files / etc.).\n"
        "        self._prompt_segments: Dict[str, str] = {}\n",
        "init _prompt_segments",
    )

    # 2) refactor _build_system_prompt to track segments
    old_build = (
        "        # Try SOUL.md as primary identity (unless context files are skipped)\n"
        "        _soul_loaded = False\n"
        "        if not self.skip_context_files:\n"
        "            _soul_content = load_soul_md()\n"
        "            if _soul_content:\n"
        "                prompt_parts = [_soul_content]\n"
        "                _soul_loaded = True\n"
        "\n"
        "        if not _soul_loaded:\n"
        "            # Fallback to hardcoded identity\n"
        "            prompt_parts = [DEFAULT_AGENT_IDENTITY]\n"
        "\n"
        "        # Pointer to the hermes-agent skill + docs for user questions about Hermes itself.\n"
        "        prompt_parts.append(HERMES_AGENT_HELP_GUIDANCE)\n"
        "\n"
        "        # Tool-aware behavioral guidance: only inject when the tools are loaded\n"
        "        tool_guidance = []\n"
        "        if \"memory\" in self.valid_tool_names:\n"
        "            tool_guidance.append(MEMORY_GUIDANCE)\n"
        "        if \"session_search\" in self.valid_tool_names:\n"
        "            tool_guidance.append(SESSION_SEARCH_GUIDANCE)\n"
        "        if \"skill_manage\" in self.valid_tool_names:\n"
        "            tool_guidance.append(SKILLS_GUIDANCE)\n"
        "        if tool_guidance:\n"
        "            prompt_parts.append(\" \".join(tool_guidance))\n"
        "\n"
        "        nous_subscription_prompt = build_nous_subscription_prompt(self.valid_tool_names)\n"
        "        if nous_subscription_prompt:\n"
        "            prompt_parts.append(nous_subscription_prompt)\n"
    )
    new_build = (
        "        # Track per-bucket text alongside the flattened prompt so the API\n"
        "        # response can expose a token-usage breakdown matching the layers\n"
        "        # above.  Keys here align with prompt_breakdown.BREAKDOWN_LABELS.\n"
        "        prompt_parts: list = []\n"
        "        segments: dict = {\n"
        "            \"identity\": [],\n"
        "            \"tool_guidance\": [],\n"
        "            \"user_system\": [],\n"
        "            \"memory_files\": [],\n"
        "            \"skills\": [],\n"
        "            \"context_files\": [],\n"
        "            \"env_meta\": [],\n"
        "        }\n"
        "\n"
        "        def _add(bucket: str, text) -> None:\n"
        "            if text is None:\n"
        "                return\n"
        "            text_str = text if isinstance(text, str) else str(text)\n"
        "            if not text_str.strip():\n"
        "                return\n"
        "            prompt_parts.append(text_str)\n"
        "            segments[bucket].append(text_str)\n"
        "\n"
        "        # Try SOUL.md as primary identity (unless context files are skipped)\n"
        "        _soul_loaded = False\n"
        "        if not self.skip_context_files:\n"
        "            _soul_content = load_soul_md()\n"
        "            if _soul_content:\n"
        "                _add(\"identity\", _soul_content)\n"
        "                _soul_loaded = True\n"
        "\n"
        "        if not _soul_loaded:\n"
        "            # Fallback to hardcoded identity\n"
        "            _add(\"identity\", DEFAULT_AGENT_IDENTITY)\n"
        "\n"
        "        # Pointer to the hermes-agent skill + docs for user questions about Hermes itself.\n"
        "        _add(\"tool_guidance\", HERMES_AGENT_HELP_GUIDANCE)\n"
        "\n"
        "        # Tool-aware behavioral guidance: only inject when the tools are loaded\n"
        "        tool_guidance = []\n"
        "        if \"memory\" in self.valid_tool_names:\n"
        "            tool_guidance.append(MEMORY_GUIDANCE)\n"
        "        if \"session_search\" in self.valid_tool_names:\n"
        "            tool_guidance.append(SESSION_SEARCH_GUIDANCE)\n"
        "        if \"skill_manage\" in self.valid_tool_names:\n"
        "            tool_guidance.append(SKILLS_GUIDANCE)\n"
        "        if tool_guidance:\n"
        "            _add(\"tool_guidance\", \" \".join(tool_guidance))\n"
        "\n"
        "        nous_subscription_prompt = build_nous_subscription_prompt(self.valid_tool_names)\n"
        "        if nous_subscription_prompt:\n"
        "            _add(\"tool_guidance\", nous_subscription_prompt)\n"
    )
    apply_replace(RUN_AGENT, old_build, new_build, "_build_system_prompt header")

    # 3) replace remaining prompt_parts.append calls inside _build_system_prompt
    for label, old, new in [
        ("enforcement guidance", "                prompt_parts.append(TOOL_USE_ENFORCEMENT_GUIDANCE)",
         "                _add(\"tool_guidance\", TOOL_USE_ENFORCEMENT_GUIDANCE)"),
        ("google guidance", "                    prompt_parts.append(GOOGLE_MODEL_OPERATIONAL_GUIDANCE)",
         "                    _add(\"tool_guidance\", GOOGLE_MODEL_OPERATIONAL_GUIDANCE)"),
        ("openai guidance", "                    prompt_parts.append(OPENAI_MODEL_EXECUTION_GUIDANCE)",
         "                    _add(\"tool_guidance\", OPENAI_MODEL_EXECUTION_GUIDANCE)"),
        ("user system_message",
         "        if system_message is not None:\n            prompt_parts.append(system_message)",
         "        if system_message is not None:\n            _add(\"user_system\", system_message)"),
        ("memory mem_block",
         "                if mem_block:\n                    prompt_parts.append(mem_block)",
         "                if mem_block:\n                    _add(\"memory_files\", mem_block)"),
        ("memory user_block",
         "                if user_block:\n                    prompt_parts.append(user_block)",
         "                if user_block:\n                    _add(\"memory_files\", user_block)"),
        ("ext memory",
         "                if _ext_mem_block:\n                    prompt_parts.append(_ext_mem_block)",
         "                if _ext_mem_block:\n                    _add(\"memory_files\", _ext_mem_block)"),
        ("skills_prompt",
         "        if skills_prompt:\n            prompt_parts.append(skills_prompt)",
         "        if skills_prompt:\n            _add(\"skills\", skills_prompt)"),
        ("context_files_prompt",
         "            if context_files_prompt:\n                prompt_parts.append(context_files_prompt)",
         "            if context_files_prompt:\n                _add(\"context_files\", context_files_prompt)"),
        ("timestamp_line",
         "            timestamp_line += f\"\\nProvider: {self.provider}\"\n        prompt_parts.append(timestamp_line)",
         "            timestamp_line += f\"\\nProvider: {self.provider}\"\n        _add(\"env_meta\", timestamp_line)"),
        (
            "alibaba guidance",
            "        if self.provider == \"alibaba\":\n"
            "            _model_short = self.model.split(\"/\")[-1] if \"/\" in self.model else self.model\n"
            "            prompt_parts.append(\n"
            "                f\"You are powered by the model named {_model_short}. \"\n"
            "                f\"The exact model ID is {self.model}. \"\n"
            "                f\"When asked what model you are, always answer based on this information, \"\n"
            "                f\"not on any model name returned by the API.\"\n"
            "            )",
            "        if self.provider == \"alibaba\":\n"
            "            _model_short = self.model.split(\"/\")[-1] if \"/\" in self.model else self.model\n"
            "            _add(\n"
            "                \"env_meta\",\n"
            "                f\"You are powered by the model named {_model_short}. \"\n"
            "                f\"The exact model ID is {self.model}. \"\n"
            "                f\"When asked what model you are, always answer based on this information, \"\n"
            "                f\"not on any model name returned by the API.\",\n"
            "            )",
        ),
        ("env hints",
         "        if _env_hints:\n            prompt_parts.append(_env_hints)",
         "        if _env_hints:\n            _add(\"env_meta\", _env_hints)"),
        ("platform hint",
         "        if platform_key in PLATFORM_HINTS:\n            prompt_parts.append(PLATFORM_HINTS[platform_key])",
         "        if platform_key in PLATFORM_HINTS:\n            _add(\"env_meta\", PLATFORM_HINTS[platform_key])"),
    ]:
        apply_replace(RUN_AGENT, old, new, label)

    # 4) snapshot segments before returning the flattened prompt
    apply_replace(
        RUN_AGENT,
        "            _add(\"env_meta\", PLATFORM_HINTS[platform_key])\n"
        "\n"
        "        return \"\\n\\n\".join(p.strip() for p in prompt_parts if p.strip())\n",
        "            _add(\"env_meta\", PLATFORM_HINTS[platform_key])\n"
        "\n"
        "        # Snapshot the per-bucket texts so compute_prompt_breakdown() can\n"
        "        # tokenize each bucket separately for the UI.\n"
        "        self._prompt_segments = {k: \"\\n\\n\".join(v).strip() for k, v in segments.items()}\n"
        "\n"
        "        return \"\\n\\n\".join(p.strip() for p in prompt_parts if p.strip())\n"
        "\n"
        "    def compute_prompt_breakdown(\n"
        "        self,\n"
        "        messages=None,\n"
        "    ):\n"
        "        \"\"\"Build a per-section token breakdown for the most recent request.\"\"\"\n"
        "        try:\n"
        "            from agent import prompt_breakdown\n"
        "        except Exception:\n"
        "            return {}\n"
        "        segments = dict(getattr(self, \"_prompt_segments\", {}) or {})\n"
        "        return prompt_breakdown.make_breakdown(\n"
        "            segments,\n"
        "            tools=self.tools,\n"
        "            messages=messages,\n"
        "            ephemeral_system_prompt=self.ephemeral_system_prompt,\n"
        "        )\n",
        "compute_prompt_breakdown method + segments snapshot",
    )

    # 5) enrich the result dict with prompt_breakdown
    apply_replace(
        RUN_AGENT,
        "            \"last_prompt_tokens\": getattr(self.context_compressor, \"last_prompt_tokens\", 0) or 0,\n"
        "            \"estimated_cost_usd\": self.session_estimated_cost_usd,\n"
        "            \"cost_status\": self.session_cost_status,\n"
        "            \"cost_source\": self.session_cost_source,\n"
        "        }\n",
        "            \"last_prompt_tokens\": getattr(self.context_compressor, \"last_prompt_tokens\", 0) or 0,\n"
        "            \"estimated_cost_usd\": self.session_estimated_cost_usd,\n"
        "            \"cost_status\": self.session_cost_status,\n"
        "            \"cost_source\": self.session_cost_source,\n"
        "        }\n"
        "\n"
        "        # Per-section context breakdown (tools / messages / system layers).\n"
        "        # Best-effort; never block the response on tokenizer issues.\n"
        "        try:\n"
        "            result[\"prompt_breakdown\"] = self.compute_prompt_breakdown(messages)\n"
        "        except Exception as exc:\n"
        "            logger.debug(\"compute_prompt_breakdown failed: %s\", exc)\n"
        "            result[\"prompt_breakdown\"] = {}\n",
        "result.prompt_breakdown",
    )


def patch_api_server() -> None:
    print(f"== patching {API_SERVER.name} ==")
    text = API_SERVER.read_text()
    if "usage[\"breakdown\"]" in text or "breakdown = result.get(\"prompt_breakdown\")" in text:
        print("  [skip] api_server.py already patched")
        return
    backup_once(API_SERVER)

    # 1) usage dict in _run_agent
    apply_replace(
        API_SERVER,
        "            usage = {\n"
        "                \"input_tokens\": getattr(agent, \"session_prompt_tokens\", 0) or 0,\n"
        "                \"output_tokens\": getattr(agent, \"session_completion_tokens\", 0) or 0,\n"
        "                \"total_tokens\": getattr(agent, \"session_total_tokens\", 0) or 0,\n"
        "            }\n"
        "            return result, usage\n",
        "            usage = {\n"
        "                \"input_tokens\": getattr(agent, \"session_prompt_tokens\", 0) or 0,\n"
        "                \"output_tokens\": getattr(agent, \"session_completion_tokens\", 0) or 0,\n"
        "                \"total_tokens\": getattr(agent, \"session_total_tokens\", 0) or 0,\n"
        "            }\n"
        "            # Per-section token breakdown (composition of prompt_tokens).\n"
        "            breakdown = result.get(\"prompt_breakdown\") if isinstance(result, dict) else None\n"
        "            if not breakdown:\n"
        "                try:\n"
        "                    breakdown = agent.compute_prompt_breakdown(\n"
        "                        result.get(\"messages\") if isinstance(result, dict) else None\n"
        "                    )\n"
        "                except Exception:\n"
        "                    breakdown = None\n"
        "            if breakdown:\n"
        "                usage[\"breakdown\"] = breakdown\n"
        "            return result, usage\n",
        "_run_agent usage breakdown",
    )

    # 2) non-streaming response usage
    apply_replace(
        API_SERVER,
        "            \"usage\": {\n"
        "                \"prompt_tokens\": usage.get(\"input_tokens\", 0),\n"
        "                \"completion_tokens\": usage.get(\"output_tokens\", 0),\n"
        "                \"total_tokens\": usage.get(\"total_tokens\", 0),\n"
        "            },\n"
        "        }\n"
        "\n"
        "        return web.json_response(response_data, headers={\"X-Hermes-Session-Id\": session_id})",
        "            \"usage\": {\n"
        "                \"prompt_tokens\": usage.get(\"input_tokens\", 0),\n"
        "                \"completion_tokens\": usage.get(\"output_tokens\", 0),\n"
        "                \"total_tokens\": usage.get(\"total_tokens\", 0),\n"
        "                **({\"breakdown\": usage[\"breakdown\"]} if usage.get(\"breakdown\") else {}),\n"
        "            },\n"
        "        }\n"
        "\n"
        "        return web.json_response(response_data, headers={\"X-Hermes-Session-Id\": session_id})",
        "non-streaming usage breakdown",
    )

    # 3) streaming finish chunk usage
    apply_replace(
        API_SERVER,
        "                \"usage\": {\n"
        "                    \"prompt_tokens\": usage.get(\"input_tokens\", 0),\n"
        "                    \"completion_tokens\": usage.get(\"output_tokens\", 0),\n"
        "                    \"total_tokens\": usage.get(\"total_tokens\", 0),\n"
        "                },\n"
        "            }\n"
        "            await response.write(f\"data: {json.dumps(finish_chunk)}\\n\\n\".encode())",
        "                \"usage\": {\n"
        "                    \"prompt_tokens\": usage.get(\"input_tokens\", 0),\n"
        "                    \"completion_tokens\": usage.get(\"output_tokens\", 0),\n"
        "                    \"total_tokens\": usage.get(\"total_tokens\", 0),\n"
        "                    **({\"breakdown\": usage[\"breakdown\"]} if usage.get(\"breakdown\") else {}),\n"
        "                },\n"
        "            }\n"
        "            await response.write(f\"data: {json.dumps(finish_chunk)}\\n\\n\".encode())",
        "streaming usage breakdown",
    )


def main() -> int:
    if not RUN_AGENT.exists() or not API_SERVER.exists():
        print("ERROR: expected files missing", file=sys.stderr)
        return 1
    patch_run_agent()
    patch_api_server()

    # AST sanity check
    import ast
    for p in (RUN_AGENT, API_SERVER):
        try:
            ast.parse(p.read_text(), str(p))
            print(f"  AST ok: {p.name}")
        except SyntaxError as e:
            print(f"  AST FAIL: {p.name}: {e}", file=sys.stderr)
            return 2
    print("== all patches applied cleanly ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
