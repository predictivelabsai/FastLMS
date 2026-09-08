"""Authenticated xAI Realtime voice sessions for the FastLearn tutor."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable

import httpx
from starlette.responses import JSONResponse

import db
from components.i18n import prompt_language_directive


log = logging.getLogger(__name__)

DEFAULT_VOICE_MODEL = "grok-voice-think-fast-2.0"
DEFAULT_VOICE_ID = "eve"
SUPPORTED_LANGUAGES = {"en", "et", "lt", "es"}


def _voice_instructions(user: dict, chat_session: dict, history: list[dict], lang: str) -> str:
    """Build a short, spoken-friendly prompt grounded in the active tutor thread."""
    context = chat_session.get("context") or {}
    role = context.get("role") or user.get("role") or "student"
    role_direction = {
        "teacher": "Help the teacher plan curriculum and support their students.",
        "instructor": "Help the teacher plan curriculum and support their students.",
        "admin": "Help the administrator manage learning programmes and support their school.",
    }.get(role, "Tutor the learner with clear explanations and useful follow-up questions.")
    recent = []
    for message in history[-8:]:
        if message.get("role") not in {"user", "assistant"}:
            continue
        speaker = "Learner" if message["role"] == "user" else "Tutor"
        text = " ".join(str(message.get("content") or "").split())[:500]
        if text:
            recent.append(f"{speaker}: {text}")
    thread_context = "\n".join(recent)
    return (
        "You are FastLearn's conversational voice tutor. "
        f"{role_direction} Keep each spoken response concise, encouraging, and easy to follow. "
        "Use examples when helpful. Never claim that progress, quiz results, or account data changed "
        "unless the learner completes that action in FastLearn."
        f"{prompt_language_directive(lang)}"
        + (f"\n\nRecent tutor conversation:\n{thread_context}" if thread_context else "")
    )


async def _create_client_secret(api_key: str) -> str:
    """Create the short-lived client credential recommended for xAI voice clients."""
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            "https://api.x.ai/v1/realtime/client_secrets",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"expires_after": {"seconds": 300}},
        )
        response.raise_for_status()
        value = str(response.json().get("value") or "")
        if not value:
            raise RuntimeError("xAI did not return a realtime client secret")
        return value


def register_voice_routes(app, get_session_user: Callable):
    """Register session-authenticated voice setup and transcript persistence routes."""

    @app.post("/app/voice/session")
    async def create_voice_session(req):
        user = get_session_user(req)
        if not user:
            return JSONResponse({"error": "Sign in before using voice."}, status_code=401)
        try:
            payload = await req.json()
        except Exception:
            return JSONResponse({"error": "Invalid voice request."}, status_code=400)
        chat_id = str(payload.get("chat") or "").strip()
        lang = str(payload.get("lang") or "en").lower()
        if lang not in SUPPORTED_LANGUAGES:
            lang = "en"
        with db.connect() as conn:
            chat_session = db.get_chat_session(conn, user["id"], chat_id)
            history = db.get_chat_history(
                conn, user["id"], limit=20, session_id=chat_id
            ) if chat_session else []
        if not chat_session:
            return JSONResponse({"error": "Chat not found."}, status_code=404)
        api_key = os.environ.get("XAI_API_KEY", "")
        if not api_key:
            return JSONResponse({"error": "Voice is not configured."}, status_code=503)
        try:
            client_secret = await _create_client_secret(api_key)
        except Exception as exc:  # noqa: BLE001
            log.warning("xAI voice session setup failed: %s", type(exc).__name__)
            return JSONResponse({"error": "Voice is temporarily unavailable."}, status_code=502)
        response = JSONResponse({
            "client_secret": client_secret,
            "model": os.environ.get("XAI_VOICE_MODEL", DEFAULT_VOICE_MODEL),
            "voice": os.environ.get("XAI_VOICE_ID", DEFAULT_VOICE_ID),
            "instructions": _voice_instructions(user, chat_session, history, lang),
        })
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.post("/app/voice/transcript")
    async def save_voice_transcript(req):
        user = get_session_user(req)
        if not user:
            return JSONResponse({"error": "Sign in before using voice."}, status_code=401)
        try:
            payload = await req.json()
        except Exception:
            return JSONResponse({"error": "Invalid transcript."}, status_code=400)
        chat_id = str(payload.get("chat") or "").strip()
        role = str(payload.get("role") or "").strip()
        content = str(payload.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content or len(content) > 20_000:
            return JSONResponse({"error": "Invalid transcript."}, status_code=422)
        with db.begin() as conn:
            chat_session = db.get_chat_session(conn, user["id"], chat_id)
            if not chat_session:
                return JSONResponse({"error": "Chat not found."}, status_code=404)
            db.add_chat_message(
                conn,
                user_id=user["id"],
                session_id=chat_id,
                role=role,
                content=content,
                lesson_id=(chat_session.get("context") or {}).get("lesson_id"),
            )
        response = JSONResponse({"ok": True})
        response.headers["Cache-Control"] = "no-store"
        return response
