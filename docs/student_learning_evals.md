# Student-learning evaluations

This suite covers only the learner experience: the three England-first science
courses, the Estonia Grade 8 chemistry reference course, guided chemistry
tasks, public mobile lesson bundles, visualization portability, and free-text
science explanations. It does not inspect staff,
school, billing or administration flows.

The checks are deliberately split by what can be proved deterministically and
what needs a language model:

| Check | Ground truth | Judge |
|---|---|---|
| Course/module/lesson shape | `student_course_contract.json` | Exact comparison |
| Chemistry answers | `chemistry_exercises.json` | Server-compatible deterministic grader |
| Mobile lesson privacy and charts | API contract | Answer-key scan and visualization validator |
| Learner explanations (EN/ET) | `tutor_explanations.json` | `JUDGE_LLM` through LangChain structured output |

Expected answers are never requested from the public API. The private eval
fixtures live outside the web static path and are used only by the offline job.

## Run locally

Create the ignored `.env` from `.env.example`, then set `OPENAI_API_KEY` there
or export it in the shell. Keep `JUDGE_LLM=gpt-5.1` unless a deliberate judge
comparison is being made.

```bash
.venv/bin/python -m evals.student_learning
```

This writes a timestamped JSON report to the ignored `artifacts/evals/`
directory, checks the deployed public student API, and runs the explanation
judge. For fast, network-free regression tests:

```bash
.venv/bin/python -m evals.student_learning --skip-live --skip-judge
.venv/bin/python -m pytest tests/test_student_learning_evals.py
```

A judge outage is a failed judge result; a missing local key is explicitly
reported as skipped. Deterministic contract failures always make the command
exit non-zero.

## Coolify follow-up

When the local baseline is accepted, add `OPENAI_API_KEY` as a Coolify secret
and set `JUDGE_LLM`, `STUDENT_EVAL_API_BASE_URL`, and `EVAL_OUTPUT_DIR` from
`.env.coolify.sample`. Mount the report directory if reports need to survive
container recreation. Configure a separate scheduled job in the same image to
run:

```bash
python -m evals.student_learning
```

Start with a daily schedule and publish the JSON summary to the chosen report
destination only after its retention and access policy is agreed.
