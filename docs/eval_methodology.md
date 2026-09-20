# FastLearn evaluation methodology

## Purpose

FastLearn evaluations measure whether the product's conversational agents and
authored learning interactions remain accurate, grounded, pedagogically sound,
safe and correctly routed. They are regression evidence, not a claim that a
model will answer every possible learner question correctly.

The suite deliberately separates two concepts:

- `eval_type` describes how the answer is produced. `probabilistic` means a
  language model generated the answer. `deterministic` means ordinary
  application code produced it.
- `scoring_method` describes how that answer is graded. A probabilistic output
  may still have a deterministic structured-contract check before semantic
  judging.

## Coverage

The version 1.0 corpus contains **262 cases**:

| Agent or subsystem | Probabilistic | Deterministic | Purpose |
|---|---:|---:|---|
| Student tutor | 202 | 0 | Two cases for every one of 101 lessons |
| Teacher assistant | 12 | 0 | Product guidance and route selection |
| Administrator assistant | 10 | 0 | Catalogue, people, school and quality-report guidance |
| Question generator | 12 | 0 | One curriculum-grounded generation case per course |
| Catalogue contract | 0 | 12 | Published authored-course and lesson counts |
| Questionnaires | 0 | 14 | Correct/incorrect grading and answer-key privacy |
| **Total** | **236** | **26** | **262** |

The course coverage includes all 12 authored courses and all 101 lessons in the
repository: the original programming demonstrations, England-first science and
chemistry, Estonian Grade 8 chemistry, art, music and chess. Multilingual
lessons are evaluated in more than one authored language where available.

## Ground truth

The same complete corpus is stored in two formats:

- `evals/ground_truth/agent_evals.json`
- `evals/ground_truth/agent_evals.csv`

The JSON form keeps nested input and rubric fields as native structures. The
CSV form JSON-encodes those fields in individual cells. The runner refuses to
start if the normalized files differ, contain duplicate identifiers, contain
fewer than 200 cases, or cease to be primarily probabilistic.

Each case identifies its agent, role, language, course and lesson; provides the
input and authoritative reference; declares required or prohibited content;
sets a minimum score; and records whether failure is critical. References come
from authored lesson content and curriculum records, not from the candidate
model's own answer.

Regenerate both mirrors after an intentional catalogue or case-definition
change:

```bash
.venv/bin/python -m evals.generate_agent_ground_truth
```

Review the resulting diff. Generation makes storage repeatable; it does not
remove the need for a human to review new prompts, references and rubrics.

## Execution

Probabilistic cases use the same role prompt builder as production chat.
Student cases receive the relevant authored lesson and curriculum contract.
Teacher and administrator cases receive the application's maintained route
guide. Question-generation cases call the production structured question
generator and its Pydantic response contract.

The production model is configured with:

- `MODEL_PROVIDER`
- `DEFAULT_MODEL`
- the matching provider API key

The semantic judge is configured separately with:

- `EVAL_JUDGE_PROVIDER` (default `openai`)
- `EVAL_JUDGE_MODEL` or the legacy `JUDGE_LLM`
- the matching provider API key

Both models run at temperature zero. Using a judge from a different model
family is recommended because it reduces correlated errors, although it does
not make judging objective. Every result records both model identities,
duration, status and failure reason.

Before a full paid run, smoke-test the configured providers and the exact model
resolution used by the evaluator:

```bash
.venv/bin/python -m pytest tests/llm_test.py -q -s
```

This explicitly invoked test verifies both the production xAI chat model and
the OpenAI structured-output judge. Its filename intentionally falls outside
pytest's default `test_*.py` discovery pattern, so ordinary unit-test runs do
not make network calls or consume model tokens. The test reads credentials from
the local `.env` file without printing them.

Run the full corpus:

```bash
.venv/bin/python -m evals.run_evals
```

Useful focused runs:

```bash
# Validate and list cases without model calls
.venv/bin/python -m evals.run_evals --dry-run

# Fast, network-free authored-contract checks
.venv/bin/python -m evals.run_evals --eval-type deterministic

# A single agent or course
.venv/bin/python -m evals.run_evals --agent student_tutor --course primary-science

# Prove that the CSV mirror is independently runnable
.venv/bin/python -m evals.run_evals --ground-truth-format csv --limit 10
```

`--suite`, `--case-id`, `--limit`, `--workers` and `--timeout` provide further
controls. Probabilistic runs fail early when a required provider key is absent;
they are never silently converted into deterministic passes.

## Grading

### Probabilistic answers

A structured judge assigns a score from 0 to 4 and returns a pass decision,
reasons and critical failures. A case passes only when:

1. the judge marks it passed;
2. its score meets the case's minimum score;
3. no critical failure is present; and
4. declared required strings are present and prohibited claims are not asserted
   as true (they may be quoted in order to correct them).

The judge compares meaning rather than wording. It checks factual agreement,
grounding, requested language, age appropriateness and the case's pedagogical
instruction. Unsupported claims, unsafe guidance, prompt-injection compliance,
answer leakage during a quiz request and contradictions of the reference are
critical.

Question-generator outputs must first satisfy the production structured schema:
the required language variants must exist, options must be unique, and each
correct answer must exactly match an option. The semantic judge then checks
curriculum grounding and educational quality.

### Deterministic answers

Catalogue cases compare current authored lesson counts with the checked-in
contract. Questionnaire cases submit one known-correct and one known-incorrect
answer through the production chemistry grader and scan the public exercise
payload for private answer material. All three checks must pass.

## Thresholds and exit status

The default thresholds are:

- probabilistic: 85%;
- deterministic: 100%.

They can be changed with `EVAL_PROBABILISTIC_THRESHOLD` and
`EVAL_DETERMINISTIC_THRESHOLD`, expressed as fractions. Errors count against a
track. Skipped cases are reported but excluded from the pass-rate denominator.
A critical failure fails the run regardless of aggregate rate. The command
returns a non-zero exit status when a selected track misses its threshold.

Aggregate percentages must be read with the per-agent, per-course,
per-language and per-suite breakdowns. A strong overall number must not conceal
a weak subject or safety-critical failure.

### Verified baseline

The 20 September 2026 full run used the production candidate
`xai/grok-4-1-fast-reasoning` and the independent
`openai/gpt-5.1` judge. It completed all 262 cases without execution errors:
260 passed and 2 failed (99.2%). All 26 deterministic cases passed. Manual
review classified one failure as a real chemistry-grounding defect and the
other as judge overreach on a correct staff route answer. The report remains
failed because the chemistry case is marked critical; manual interpretation
does not rewrite the recorded machine verdict.

## Reports

Every non-dry run creates:

```text
evals/reports/<UTC-run-id>/
  summary.json
  results.csv
  report.md
```

`evals/reports/index.json` points to recent runs. Set `EVAL_REPORT_DIR` when the
deployment uses a persistent mounted directory; relative paths resolve from the
repository root. Report lookup accepts only generated run identifiers and known
artifact names.

The web application exposes **Admin → Evaluation reports** to every signed-in
role:

- students see overall quality, probabilistic/deterministic separation and
  course coverage;
- teachers and administrators additionally see case inputs, ground truth,
  model outputs, judge reasons and the full CSV download;
- anonymous users are redirected to sign in;
- students cannot download the detailed CSV.

This split prevents evaluation prompts and expected answers from becoming a
student-visible answer key.

## Maintenance and interpretation

Add cases when a new lesson, agent capability, recurring failure or safety
boundary is introduced. Keep references attributable to authored curriculum or
an explicitly reviewed product contract. Do not turn a model-generated answer
into ground truth without human review.

LLM judging remains probabilistic and may share blind spots with the evaluated
model. Important failures should be manually reviewed, corrected in the corpus
when the reference is wrong, and rerun. Compare like-for-like model and corpus
versions when interpreting trends.

## Reference

The corpus-plus-testing-criteria structure and separation of deterministic and
model-based graders follow the concepts documented in the
[OpenAI Evals API reference](https://platform.openai.com/docs/api-reference/evals).
