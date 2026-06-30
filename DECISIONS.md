# Design Decisions

Why the auditor is built the way it is — the rationale behind the non-obvious
engineering choices. The [README](README.md) covers what it does and how to run
it; this file covers *why*, so each decision can be defended rather than just
pointed at.

## 1. Structured output via forced tool use, not parsed-from-text JSON

The model returns its report through a *forced* tool call whose `input_schema`
is generated directly from the Pydantic `AuditReport` model
(`tool_choice={"type": "tool", ...}`). The result is read from the `tool_use`
block and validated with `AuditReport.model_validate(...)`.

The rejected alternative was to ask for JSON in prose and parse it out of the
text — stripping ` ```json ` fences with string surgery. That couples
correctness to how the model happens to format prose: it breaks silently the
day the wrapping changes, and it turns the schema into a convention rather than
a contract. Forcing tool use makes the Pydantic schema the single source of
truth for the output shape and removes the fence-stripping workaround entirely.

## 2. `suggested_fix` is nullable, and the model must not invent one

Each error carries an optional `suggested_fix`. For mistakes with a single
unambiguous correction — a typo, punctuation, a clear factual error with one
right answer — the model returns the corrected fragment. For anything that
needs human judgment — two conflicting figures in the same document, genuine
ambiguity, style remarks with no single correct form — `suggested_fix` is
strictly `null`, and the system prompt explicitly forbids guessing.

Rationale: a confident-but-wrong autofix on a contradiction is worse than no
fix, because it papers over the conflict the human actually needs to see and
resolve. The tool's job there is to *flag*, not to fabricate a resolution.

## 3. The eval harness is deliberately separate from the production path

Quality is measured against a hand-labeled 10-document set, and the measurement
code lives in `eval/` isolated from `audit.py` / `main.py`, so scoring can never
perturb the product. The methodology choices that make the number trustworthy:

- **A separate, stricter schema for evaluation.** Production errors use a
  free-text `location`; the eval schema uses a closed `type` enum
  (`typo | grammar | factual | contradiction | logic`) and an integer
  `paragraph`. Free-text location cannot be matched deterministically — eval
  needs a key the harness can compare exactly, which is a different goal from
  the human-readable product output.
- **Ground truth is labeled by a human, not the model.** Letting the model
  grade its own output measures self-consistency, not correctness.
- **Matching is deterministic, by `(type, paragraph)` key — never by
  description text.** Comparing free-text descriptions would smuggle a second
  fuzzy judgment into the metric. Duplicate keys are matched one-to-one, so one
  ground-truth error cannot be satisfied by two predictions.
- **`temperature=0`, and the prompt version is an explicit parameter.** A
  precision/recall delta is then attributable to a prompt change, not to
  sampling noise.

## 4. Deterministic checks and LLM checks are different engines

Measurable, rule-based properties — formatting and structure against a style
standard (font, margins, spacing) — belong to a deterministic engine, never to
the LLM: those checks must be 100% reproducible, and a model's
non-determinism is a liability there. The LLM is reserved for content and
meaning errors, where judgment is the whole point.

The current service implements the content engine. Keeping the boundary
explicit — reproducible rules on one side, judgment on the other — is the
reason not to collapse both into one model prompt: it would trade away
reproducibility on exactly the checks that most need it.
