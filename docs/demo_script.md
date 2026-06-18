# Demo script (60 seconds)

Goal: show the full path from "upload a document" to "structured error
report", on the live public URL — not localhost. No narration script
needed beyond what's below; keep it screen + cursor, no talking head
required.

## Beats

1. **(0:00-0:08) Context card or title slide**: "Document Auditor — Claude
   API + FastAPI, finds errors in documents and suggests fixes."
   One line: "Live demo, deployed on Render."

2. **(0:08-0:15) Show the doc that will be audited.** Open `sample.txt` (or
   `sample.docx`) in a text editor/Word, scroll once so the viewer sees
   it's a real, plausible document with at least one visible planted
   error (e.g. a wrong number or a factual slip) — don't point it out yet,
   let the report find it.

3. **(0:15-0:35) Send the request.** Terminal, run the curl command from
   the README against the live URL:
   ```bash
   curl -X POST "https://document-auditor.onrender.com/audit" -F "file=@sample.txt"
   ```
   If cold start is a risk, fire a throwaway warm-up request a few seconds
   before recording starts (not shown on camera) so the recorded request
   returns quickly instead of sitting on a 30-60s Render free-tier cold
   start.

4. **(0:35-0:55) Show the JSON response.** Pipe through `jq .` (or open
   the saved output in an editor) so it's readable, not a wall of raw
   JSON. Scroll to one `errors[]` entry and point out (cursor highlight,
   no voiceover needed) the four fields: `type`, `location`,
   `description`, `suggested_fix`. Pick an entry where `suggested_fix` is
   a concrete string, not `null`, since that's the more interesting case
   to show.

5. **(0:55-1:00) Closing card**: GitHub URL + "precision 0.77 / recall 0.83
   on a 10-doc eval set" as a one-liner, pointing at the repo/eval results
   for anyone who wants the methodology.

## What NOT to show

- Don't show the `.env` file or the API key, even blurred — just don't
  open it on camera.
- Don't show a `null` suggested_fix as the only example; pick a request/
  document that produces at least one concrete fix, since that's the more
  interesting half of the feature.
- Don't pad with a tour of the codebase — this is a product demo (input →
  output), not a code walkthrough. The repo link in the closing card is
  where code-curious viewers go next.

## Prep before recording

- Pick (or write) a `sample.txt` with 2-3 unambiguous errors so the
  response isn't empty and isn't overwhelming within a 60s window.
- Confirm the Render service is awake (hit `/audit` once, throwaway,
  right before recording) so the real take doesn't sit on a cold start.
- Have the curl command and `jq` ready in shell history so there's no
  typing delay on camera.
