"""Voice tutor security, prompt grounding, and client wiring regressions."""

import asyncio
import os
import tempfile
from pathlib import Path

from fasthtml.common import to_xml

_AUTH_TEMP = tempfile.TemporaryDirectory(prefix="fastlearn-voice-tests-")
os.environ["FASTSME_AUTH_DB"] = str(Path(_AUTH_TEMP.name) / "accounts.sqlite")

import main
import voice
from components.layout import page_head


def test_voice_routes_and_client_are_loaded():
    paths = {route.path for route in main.app.routes}
    assert "/app/voice/session" in paths
    assert "/app/voice/transcript" in paths
    assert 'src="/static/voice.js"' in to_xml(page_head("Tutor"))


def test_voice_prompt_is_role_aware_language_aware_and_thread_grounded():
    prompt = voice._voice_instructions(
        {"role": "student"},
        {"context": {"role": "teacher"}},
        [
            {"role": "user", "content": "Help me teach fractions."},
            {"role": "assistant", "content": "Start with visual pieces."},
        ],
        "et",
    )
    assert "Help the teacher" in prompt
    assert "Help me teach fractions" in prompt
    assert "visual pieces" in prompt
    assert "Vasta eesti keeles" in prompt


def test_xai_client_secret_request_is_short_lived_and_server_authenticated(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"value": "temporary-browser-secret"}

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, url, **kwargs):
            captured["url"] = url
            captured["request"] = kwargs
            return FakeResponse()

    monkeypatch.setattr(voice.httpx, "AsyncClient", FakeClient)
    result = asyncio.run(voice._create_client_secret("server-only-api-key"))

    assert result == "temporary-browser-secret"
    assert captured["url"].endswith("/v1/realtime/client_secrets")
    assert captured["request"]["headers"]["Authorization"] == "Bearer server-only-api-key"
    assert captured["request"]["json"] == {"expires_after": {"seconds": 300}}


def test_voice_browser_uses_ephemeral_secret_and_current_audio_contract():
    source = Path("static/voice.js").read_text()
    assert "xai-client-secret.${session.client_secret}" in source
    assert 'turn_detection: {type: "server_vad"}' in source
    assert 'transcription: {model: "grok-transcribe"}' in source
    assert "XAI_API_KEY" not in source
    assert "voice-sonogram" not in source  # Web uses semantic voice-wave classes.
