"""Live smoke tests for the production candidate and evaluation judge.

This file is intentionally outside pytest's default ``test_*.py`` pattern so a
normal unit-test run never spends tokens. Run it explicitly:

    .venv/bin/python -m pytest tests/llm_test.py -q -s
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from byok import llm as llm_factory  # noqa: E402
from evals.run_evals import _model_config  # noqa: E402


class SmokeVerdict(BaseModel):
    score: int = Field(ge=0, le=4)
    passed: bool
    reason: str


def _required_key(provider: str) -> str:
    spec = llm_factory.PROVIDERS.get(provider)
    assert spec, f"Unknown provider: {provider}"
    key = os.getenv(spec["env"], "")
    assert key, f"{spec['env']} is not configured in .env"
    return key


def test_xai_production_model_smoke():
    config = _model_config()
    assert config["provider"] == "xai", config
    model = llm_factory.build_chat_model(
        config["provider"], _required_key(config["provider"]), config["model"],
        temperature=0, streaming=False,
    )
    response = model.invoke([
        SystemMessage(content="Follow the user's formatting instruction exactly."),
        HumanMessage(content="Reply with exactly FASTLEARN_XAI_OK and nothing else."),
    ])
    content = str(response.content).strip()
    assert content == "FASTLEARN_XAI_OK", content
    print(f"xAI production smoke passed: {config['model']}")


def test_openai_evaluation_judge_structured_output_smoke():
    config = _model_config()
    assert config["judge_provider"] == "openai", config
    judge = llm_factory.build_chat_model(
        config["judge_provider"], _required_key(config["judge_provider"]),
        config["judge_model"], temperature=0, streaming=False,
    ).with_structured_output(SmokeVerdict)
    verdict = judge.invoke([
        SystemMessage(content="Return the requested structured evaluation."),
        HumanMessage(content="The candidate exactly equals the reference. Score it 4 and mark it passed."),
    ])
    if not isinstance(verdict, SmokeVerdict):
        verdict = SmokeVerdict.model_validate(verdict)
    assert verdict.passed is True
    assert verdict.score == 4
    assert verdict.reason.strip()
    print(f"OpenAI judge smoke passed: {config['judge_model']}")
