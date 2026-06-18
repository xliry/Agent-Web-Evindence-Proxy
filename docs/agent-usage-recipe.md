# Agent Usage Recipe

Use `awep fetch` whenever an agent would otherwise fetch, browse, search-result-open, or scrape a source that may support a final claim.

Pass a stable `run_id` for the agent task so all receipts land in one evidence folder:

```bash
awep fetch "$URL" \
  --claim "$CLAIM" \
  --run-id "$RUN_ID" \
  --agent-id "$AGENT_ID" \
  --tool-name "$TOOL_NAME"
```

Suggested fields:

- `run_id`: one id for the whole agent run, such as `lead-research-20260618`.
- `agent_id`: the caller identity, such as `codex`, `research-agent`, or `sales-bot`.
- `tool_name`: the original tool being mediated, such as `web.run`, `scrape`, or `search`.
- `claim`: the specific sentence or assertion the source is expected to support.

At the end of the run:

```bash
awep report "$RUN_ID"
awep verify "$RUN_ID"
```

Attach `.awep/runs/<run-id>/report.md` to the final handoff. Treat blocked, empty, login-required, or JavaScript-required sources as evidence-quality warnings, not as proof.
