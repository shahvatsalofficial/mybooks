# CCAR-F / CCA-F Exam Quick-Reference Cheat Sheet

## Exam Format
- **Questions:** 60 scenario-based MC/MR | **Time:** 120 min | **Pass:** 720 / 1000 | **Validity:** 12 months

## 5 Official Domains
1. **Agentic Architecture & Orchestration (27%):** Handle `stop_reason` (`end_turn`, `tool_use`, `max_tokens`, `refusal`). Isolate subagent context (pass scoped briefs, never full parent history). Enforce `max_turns` and HITL gates before mutating tools.
2. **Claude Code Configuration & Workflows (20%):** `CLAUDE.md` hierarchy (global -> repo root -> subdir). Headless CI via `-p` and `--output-format json`. Use `/compact` vs `/clear` for long sessions.
3. **Prompt Engineering & Structured Output (20%):** Separate `<instructions>` from `<untrusted_data>` with XML tags. Enforce JSON via tool schemas + Pydantic validators, never prose alone.
4. **Tool Design & MCP Integration (18%):** Descriptions drive tool routing. Stay below the 18–20 tool degradation cliff. Return `isError: true` with actionable guidance. Know `tool_choice`: `auto`, `any`, `tool`.
5. **Context Management & Reliability (15%):** Use `cache_control: {"type": "ephemeral"}` on stable prefixes. Prefer deterministic code checks over extra prompting. Use exponential backoff + jitter for HTTP 429/529.
