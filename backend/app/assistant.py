"""Builds the "Ask about today" answer and streams it to the client.

Two answer sources:
  - a deterministic template over the day's tasks (always available, no
    API key, no network call) -- this is what the brief asks for and what
    runs by default.
  - an optional pass-through to Groq's streaming chat-completions API if
    GROQ_API_KEY is set, for a more natural sentence. If that call fails
    for any reason (no key, no network, rate limit) we fall back to the
    template so the feature never breaks.

Either way, streaming to the UI is via the same word-at-a-time generator
contract: an async generator of small text chunks.
"""

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime

import httpx

from app.config import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _time_str(iso_value: str) -> str:
    dt = datetime.fromisoformat(iso_value)
    return dt.strftime("%I:%M %p").lstrip("0").lower()


def _task_brief(task: dict) -> str:
    return f"{_time_str(task['due_at'])} {task['title']}"


def build_context(recipient_name: str, grouping: dict) -> dict:
    """Turn a grouping of ORM task rows into a small, JSON-serializable dict.

    This is exactly what gets logged in the AIInteraction.context column,
    so keep it compact and readable.
    """

    def fmt(task) -> dict:
        return {
            "title": task.title,
            "category": getattr(task.category, "value", task.category),
            "due_at": task.due_at.isoformat(),
            "completed_by": task.completed_by.name if task.completed_by else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    return {
        "recipient": recipient_name,
        "overdue": [fmt(t) for t in grouping["overdue"]],
        "due": [fmt(t) for t in grouping["due"]],
        "done": [fmt(t) for t in grouping["done"]],
    }


def build_template_answer(question: str, context: dict) -> str:
    recipient = context["recipient"]
    overdue, due, done = context["overdue"], context["due"], context["done"]
    q = question.lower()

    # Light keyword steering: a question naming someone narrows the "done" mention.
    named_done = [t for t in done if t["completed_by"] and t["completed_by"].lower() in q]
    highlight_done = named_done[0] if named_done else (done[0] if done else None)

    parts: list[str] = []

    if overdue:
        parts.append(f"{recipient}'s {_task_brief(overdue[0])} is still pending.")
        if len(overdue) > 1:
            parts.append(f"{len(overdue) - 1} more task(s) are also overdue.")
    else:
        parts.append(f"Nothing is overdue for {recipient} right now.")

    if highlight_done:
        who = highlight_done["completed_by"] or "Someone"
        parts.append(f"{who} did the {_task_brief(highlight_done)}.")

    if due:
        parts.append(f"Next up: {_task_brief(due[0])}.")

    parts.append(f"Today so far: {len(done)} done, {len(due)} due, {len(overdue)} overdue.")
    return " ".join(parts)


async def _stream_words(text: str, delay: float = 0.04) -> AsyncGenerator[str, None]:
    words = text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        await asyncio.sleep(delay)


async def _stream_groq(question: str, context: dict) -> AsyncGenerator[str, None]:
    system = (
        "You are a brief, caring assistant for a family coordinating a parent's care. "
        "Answer in 1-3 short sentences using only the task data given as JSON context. "
        "Never invent tasks or names not present in the context."
    )
    payload = {
        "model": settings.groq_model,
        "stream": True,
        "temperature": 0.2,
        "max_tokens": 200,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Context: {json.dumps(context)}\n\nQuestion: {question}"},
        ],
    }
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}

    async with httpx.AsyncClient(timeout=15) as client:
        async with client.stream("POST", GROQ_URL, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[len("data: "):]
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                delta = chunk["choices"][0]["delta"].get("content")
                if delta:
                    yield delta


async def stream_answer(question: str, context: dict) -> AsyncGenerator[str, None]:
    """Yield the answer in small chunks, and return the full text via the
    caller collecting the stream (see routers/assistant.py), so it can be
    logged once streaming finishes."""
    if settings.groq_api_key:
        try:
            async for chunk in _stream_groq(question, context):
                yield chunk
            return
        except Exception:
            pass  # fall back to the template below

    answer = build_template_answer(question, context)
    async for chunk in _stream_words(answer):
        yield chunk
