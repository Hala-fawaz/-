"""One place for talking to the language model (Groq).

- The model comes from GROQ_MODEL (default: openai/gpt-oss-120b). If a
  call fails (rate limit, timeout, unknown model...), the guide retries
  once with GROQ_FALLBACK_MODEL (default: allam-2-7b; "none" disables).
  Groq rate limits are per model, so the fallback also absorbs bursts.
- The client is created on first use, not at import time, so the app
  (and the tests) can start without a key.
- parse_accept_ids() reads a verifier's "ACCEPT: 1,3" reply. The old
  regex needed exactly "ACCEPT:", and allam-2-7b answered
  "ACCEPTED SENTENCES:\\n1,2,3" -> every answer was thrown away.
"""

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

from .llm_options import llm_options


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_FALLBACK_MODEL = "allam-2-7b"


class LLMUnavailable(RuntimeError):
    """No model could produce an answer (missing key, outage, limits)."""


@dataclass
class Completion:
    text: str
    finish_reason: str | None
    model: str


def primary_model() -> str:
    return os.getenv("GROQ_MODEL") or DEFAULT_MODEL


def fallback_model() -> str | None:
    value = os.getenv("GROQ_FALLBACK_MODEL", DEFAULT_FALLBACK_MODEL).strip()
    return None if value.lower() in ("", "none", "off", "0") else value


_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise LLMUnavailable("GROQ_API_KEY is not set")
        from groq import Groq  # imported here so tests do not need the package
        _client = Groq(api_key=api_key, timeout=40.0, max_retries=1)
    return _client


def set_client(client) -> None:
    """Use another client object (tests pass a fake one)."""
    global _client
    _client = client


Messages = list[dict]


def complete(
    messages: Messages | Callable[[str], Messages],
    answer_tokens: int | Callable[[str], int],
    temperature: float = 0.0,
    models: list[str] | None = None,
) -> Completion:
    """Run one chat completion, falling back to the second model on failure.

    `messages` and `answer_tokens` may be functions of the model name,
    so a model with a small context window gets fewer passages and a
    smaller answer budget.
    """
    candidates = [m for m in (models or [primary_model(), fallback_model()]) if m]
    candidates = list(dict.fromkeys(candidates))
    errors = []

    for model in candidates:
        payload = messages(model) if callable(messages) else messages
        tokens = answer_tokens(model) if callable(answer_tokens) else answer_tokens
        try:
            response = get_client().chat.completions.create(
                model=model,
                messages=payload,
                temperature=temperature,
                **llm_options(model, tokens),
            )
        except LLMUnavailable:
            raise
        except Exception as error:  # rate limit, timeout, bad model id...
            errors.append(f"{model}: {error.__class__.__name__}: {error}")
            print(f"[rag] model call failed ({model}): {error!r}", file=sys.stderr)
            continue

        choice = response.choices[0]
        text = (choice.message.content or "").strip()

        if not text:
            # A reasoning model can spend the whole budget thinking.
            errors.append(f"{model}: empty reply (finish_reason={choice.finish_reason})")
            continue

        return Completion(text=text, finish_reason=choice.finish_reason, model=model)

    raise LLMUnavailable("; ".join(errors) or "no model configured")


_ACCEPT_RE = re.compile(r"ACCEPT(?:ED)?\b[^:\n]{0,40}:\s*(.*)", re.IGNORECASE | re.DOTALL)


def parse_accept_ids(output: str, count: int) -> set[int] | None:
    """Item numbers from a verifier reply such as "ACCEPT: 1,3".

    Returns the accepted numbers, an empty set for "ACCEPT: NONE", or
    None when the reply cannot be read at all (the caller then keeps
    the answer instead of discarding it).

    Accepted shapes include "ACCEPT: 1,3", "accept: 1, 3",
    "ACCEPTED SENTENCES:\\n1,2,3" and "ACCEPT: 1,3\\n\\nexplanation...".
    """
    match = _ACCEPT_RE.search(output or "")
    if not match:
        return None

    rest = match.group(1).strip()
    first_block = re.split(r"\n\s*\n", rest, maxsplit=1)[0]

    if re.match(r"(?:NONE|NO\b|لا\s*شيء)", first_block, re.IGNORECASE):
        return set()

    numbers = {
        int(number)
        for number in re.findall(r"\d+", first_block)
        if 1 <= int(number) <= count
    }
    return numbers or None
