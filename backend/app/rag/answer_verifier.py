"""Second pass: drop answer sentences that the passages do not support.

RAG_VERIFY_ANSWERS controls it:
- "auto" (default): on when the answer came from a large-context model
  such as openai/gpt-oss-120b, off for allam-2-7b. With allam-2-7b this
  step used to throw away correct answers: it replied
  "ACCEPTED SENTENCES: 1,2,3" and the old parser only knew "ACCEPT:".
- "1" always on, "0" always off.

It costs one more call to the same model per question, and it fails
open: if the reply cannot be read, or the call fails, the answer is
kept as it is. Only an explicit "ACCEPT: NONE" replaces the answer
with the abstention message.
"""

import os
import re
import sys

from .arabic_text import remove_diacritics
from .llm import complete, parse_accept_ids
from .llm_options import model_profile


INSUFFICIENT_ANSWER = "لم أجد في المصادر المتاحة دليلًا كافيًا للإجابة عن هذا السؤال."

SYSTEM_PROMPT = """You check an Arabic answer against Arabic source passages.

For each numbered answer sentence, decide whether the passages support it.
Accept a sentence when its facts (names, dates, numbers, places, events,
and who did what) appear in the passages, even if the wording differs.
Reject a sentence that adds a fact, or gives a person or a place a role
or an action, that the passages do not state. A name appearing in a
passage does not prove what the sentence says about it.
Accept a short closing sentence with a lesson when it follows from the
passages.

Reply with one line only, for example:
ACCEPT: 1,2,4
or, if no sentence is supported:
ACCEPT: NONE"""

_SENTENCE_RE = re.compile(r"(?<=[.!?؟])\s+")


def verification_mode() -> str:
    value = os.getenv("RAG_VERIFY_ANSWERS", "auto").strip().lower()
    if value in ("1", "true", "yes", "on"):
        return "on"
    if value in ("0", "false", "no", "off"):
        return "off"
    return "auto"


def should_verify(model: str | None) -> bool:
    mode = verification_mode()
    if mode == "off" or not model:
        return False
    if mode == "on":
        return True
    return model_profile(model).context_tokens > 8192


def verification_enabled() -> bool:
    """Older helper: True when verification is explicitly turned on."""
    return verification_mode() == "on"


def verify_generated_answer(question: str, answer: str, evidence: list[dict], model: str | None = None) -> str:
    answer = (answer or "").strip()
    if not answer or answer == INSUFFICIENT_ANSWER:
        return INSUFFICIENT_ANSWER

    # (paragraph, line, sentence) so lists and paragraphs survive.
    units = []
    for p_index, paragraph in enumerate(re.split(r"\n\s*\n", answer)):
        for l_index, line in enumerate(paragraph.strip().splitlines()):
            for sentence in _SENTENCE_RE.split(line.strip()):
                if sentence.strip():
                    units.append((p_index, l_index, sentence.strip()))
    if not units:
        return INSUFFICIENT_ANSWER

    if model:
        from .generator import fit_evidence  # same passages the model answered from
        evidence = fit_evidence(evidence, model)

    passages = "\n\n".join(
        f"[{i}] " + remove_diacritics(item.get("text") or item.get("snippet") or "")
        for i, item in enumerate(evidence, 1)
    )
    numbered = "\n".join(f"{i}. {sentence}" for i, (_, _, sentence) in enumerate(units, 1))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"QUESTION:\n{question}\n\nPASSAGES:\n{passages}\n\nANSWER SENTENCES:\n{numbered}"},
    ]

    try:
        reply = complete(messages, answer_tokens=120, temperature=0.0, models=[model] if model else None).text
    except Exception as error:
        print(f"[rag] answer verification skipped: {error!r}", file=sys.stderr)
        return answer

    accepted = parse_accept_ids(reply, len(units))
    if accepted is None:
        print(f"[rag] unreadable verifier reply kept the answer: {reply[:120]!r}", file=sys.stderr)
        return answer
    if not accepted:
        return INSUFFICIENT_ANSWER

    rebuilt: dict[int, dict[int, list[str]]] = {}
    for number, (p_index, l_index, sentence) in enumerate(units, 1):
        if number in accepted:
            rebuilt.setdefault(p_index, {}).setdefault(l_index, []).append(sentence)

    return "\n\n".join(
        "\n".join(" ".join(parts) for _, parts in sorted(lines.items()))
        for _, lines in sorted(rebuilt.items())
    )
