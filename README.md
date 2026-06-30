# Document Auditor

**Live demo:** https://document-auditor.onrender.com — POST a `.txt`/`.docx`
to `/audit`, get back a structured error report (Claude on the backend,
cold start on Render free tier can take ~30-60s on the first request).

**60s demo video:** https://youtu.be/qG_BL9XDU40

FastAPI service that takes a document (`.txt`/`.docx`), sends it to the
Claude API with an auditor system prompt, and returns a structured report
of errors found in the text (typos, factual inconsistencies, contradictions,
logic issues), each with a suggested fix where one is unambiguous. Portfolio
project for an Applied AI / LLM Engineer role.

## Try it

```bash
curl -X POST "https://document-auditor.onrender.com/audit" \
  -F "file=@sample.txt"
```

Response is a JSON `AuditReport`:

```json
{
  "errors": [
    {
      "type": "factual",
      "location": "...",
      "description": "...",
      "suggested_fix": "..."
    }
  ],
  "summary": "..."
}
```

## Quality

The content-auditing engine is measured against a hand-labeled 10-document
eval set, not eyeballed: **precision 0.769 / recall 0.833 / F1 0.8**
(aggregate, prompt v1). Details, methodology, and failure-mode analysis in
[eval/README.md](eval/README.md).

## Stack

Python, Anthropic SDK (tool use / structured output), Pydantic, FastAPI,
python-docx.

## Run locally

```bash
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-..." > .env
uvicorn main:app --port 8000
```

## Demo protection

`/audit` spends Anthropic tokens on every call and is publicly reachable, so
the endpoint is rate-limited rather than left open (a deliberately different
threat model from the fail-closed write endpoint in the sister project):

- **Global daily cap** (`AUDIT_DAILY_CAP`, default 100) — a hard ceiling on
  spend regardless of source IP. This is the real budget guard, since a
  per-IP limit alone is bypassed by rotating addresses.
- **Per-IP rate limit** (`AUDIT_RATE_LIMIT`, default 5 per 60s).
- **Input size cap** (`AUDIT_MAX_INPUT_CHARS`, default 50000) — bounds the
  cost of a single call (`413` when exceeded).
- **Optional API key** (`AUDIT_API_KEY`) — if set, `/audit` requires an
  `X-API-Key` header (constant-time compare); if unset, the public demo stays
  open under the limits above.

All knobs are environment variables, so the public demo keeps working out of
the box while a private deployment can lock it down by setting `AUDIT_API_KEY`.

## Architecture notes

- `audit.py` — core extraction + Claude call, forced tool use against a
  Pydantic-derived schema (`AuditReport`), usable standalone as a CLI.
- `main.py` — FastAPI wrapper (`POST /audit`), token-spend protected
  (see Demo protection), maps extraction/validation failures to 400/413/502
  instead of bare 500s.
- `eval/` — separate harness with its own closed-schema matching, used to
  score the auditor numerically against ground truth. See
  [eval/README.md](eval/README.md) for why it's a separate schema from the
  production one.
