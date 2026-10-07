"""Optional second pass: drop answer sentences the passages do not support.

Off by default (set RAG_VERIFY_ANSWERS=1 to turn it on). It costs one
more model call per question, and with a small model it was the step
that threw away correct answers: allam-2-7b replied
"ACCEPTED SENTENCES: 1,2,3" and the old parser, which only understood
"ACCEPT:", turned that into "no evidence".

When enabled it now fails open: if the reply cannot be read, or the
model call fails, the answer is kept as it is. Only an explicit
"ACCEPT: NONE" replaces the answer with the abstention message.
"""

import os
import re
import sys

from .arabic_text import remove_diacritics
from .llm import complete, parse_accept_ids


INSUFFICIENT_ANSWER = "لم أجد في المصادر المتاحة دليلًا كافيًا للإجابة عن هذا السؤال."

SYSTEM_PROMPT = """You check an Arabic answer against Arabic source passages.

For each numbered answer sentence, decide whether the passages support it.
Accept a sentence when its facts (names, dates, numbers, places, events)
appear in the passages, even if the wording differs. Accept short
reflective closing sentences (a lesson or moral) when they follow from
the passages. Reject a sentence that adds facts not found in the passages.

Reply with one line only, for example:
ACCEPT: 1,2,4
or, if no sentence is supported:
ACCEPT: NONE"""

_SENTENCE_RE = re.compile(r"(?<=[.!?؟])\s+")


def verification_enabled() -> bool:
    return os.getenv("RAG_VERIFY_ANSWERS", "0").strip().lower() in ("1", "true", "yes", "on")


def verify_generated_answer(question: str, answer: str, evidence: list[dict]) -> str:
    answer = (answer or "").strip()
    if not answer or answer == INSUFFICIENT_ANSWER:
        return INSUFFICIENT_ANSWER

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", answer) if p.strip()]
    sentences = [
        (p_index, sentence.strip())
        for p_index, paragraph in enumerate(paragraphs)
        for sentence in _SENTENCE_RE.split(paragraph)
        if sentence.strip()
    ]
    if not sentences:
        return INSUFFICIENT_ANSWER

    passages = "\n\n".join(
        f"[{i}] " + remove_diacritics(item.get("text") or item.get("snippet") or "")
        for i, item in enumerate(evidence, 1)
    )
    numbered = "\n".join(f"{i}. {sentence}" for i, (_, sentence) in enumerate(sentences, 1))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"QUESTION:\n{question}\n\nPASSAGES:\n{passages}\n\nANSWER SENTENCES:\n{numbered}"},
    ]

    try:
        reply = complete(messages, answer_tokens=80, temperature=0.0).text
    except Exception as error:
        print(f"[rag] answer verification skipped: {error!r}", file=sys.stderr)
        return answer

    accepted = parse_accept_ids(reply, len(sentences))
    if accepted is None:
        print(f"[rag] unreadable verifier reply kept the answer: {reply[:120]!r}", file=sys.stderr)
        return answer
    if not accepted:
        return INSUFFICIENT_ANSWER

    rebuilt: dict[int, list[str]] = {}
    for number, (p_index, sentence) in enumerate(sentences, 1):
        if number in accepted:
            rebuilt.setdefault(p_index, []).append(sentence)

    return "\n\n".join(" ".join(parts) for _, parts in sorted(rebuilt.items()))
