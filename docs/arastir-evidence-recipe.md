# /arastir Evidence Recipe

Use AWEP with `/arastir` when a market-research brief cites web sources and you want a local evidence check for what the agent actually fetched.

## Run ID

Use one run id per research brief:

```powershell
$runId = "market-awep-20260619"
$root = "C:\tmp\awep-market-20260619"
```

## Fetch Main Sources

Fetch 5-8 primary sources from the brief. Pass the claim each source is expected to support, plus labels and tags that make the report easy to scan.

```powershell
awep fetch "https://example.com/source" `
  --run-id $runId `
  --claim "The source supports one specific market-research claim." `
  --agent-id arastir `
  --tool-name web-research `
  --citation-label "Primary source" `
  --tag market `
  --storage-root $root
```

Use focused claims. Do not ask AWEP to decide truth; AWEP records source quality and lexical claim evidence.

## Report And Verify

```powershell
awep report $runId --storage-root $root
awep verify $runId --storage-root $root
```

Attach:

```text
$root\runs\$runId\report.md
```

## Research Log Block

Paste a compact block into the `/arastir` handoff:

```markdown
## AWEP Evidence Check
- Run ID: market-awep-YYYYMMDD
- Receipts: N
- Verification: ok checked N receipts
- OK sources: N
- Blocked/error sources: N
- Notes: blocked pages were not treated as readable evidence; weak/missing claim statuses mean low lexical overlap, not source fetch failure.
```

## Interpreting Results

- `ok`: AWEP fetched and extracted readable source text.
- `blocked`: the fetch hit an anti-bot, auth, rate-limit, or similar barrier.
- `error`: network or safety guard failure.
- `supported`: deterministic lexical overlap between claim and extracted text is strong.
- `weak`: some claim terms appear, but support is limited.
- `missing`: the source may be readable, but the claim text did not lexically match the extracted text. This is common for multilingual pages.

The dogfood run `market-awep-20260619` showed why this matters: readable pages, blocked pages, and low lexical claim matches need to be separated in the research log.
