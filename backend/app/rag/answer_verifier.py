import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from .llm_options import llm_options


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

MODEL_NAME = os.getenv("GROQ_MODEL", "allam-2-7b")

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

INSUFFICIENT_ANSWER = "\u0644\u0645 \u0623\u062c\u062f \u0641\u064a \u0627\u0644\u0645\u0635\u0627\u062f\u0631 \u0627\u0644\u0645\u062a\u0627\u062d\u0629 \u062f\u0644\u064a\u0644\u064b\u0627 \u0643\u0627\u0641\u064a\u064b\u0627 \u0644\u0644\u0625\u062c\u0627\u0628\u0629 \u0639\u0646 \u0647\u0630\u0627 \u0627\u0644\u0633\u0624\u0627\u0644."


def verify_generated_answer(
    question: str,
    answer: str,
    evidence: list[dict],
) -> str:
    answer = (answer or "").strip()

    if not answer:
        return INSUFFICIENT_ANSWER

    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?\u061f])\s+", answer)
        if part.strip()
    ]

    if not sentences:
        return INSUFFICIENT_ANSWER

    evidence_text = "\n\n".join(
        (item.get("snippet") or item.get("text") or "").strip()
        for item in evidence
        if (item.get("snippet") or item.get("text") or "").strip()
    )

    if not evidence_text:
        return INSUFFICIENT_ANSWER

    numbered = "\n".join(
        f"[{i}] {sentence}"
        for i, sentence in enumerate(sentences, 1)
    )

    system_prompt = """
You are a strict factual answer verifier.

For each numbered sentence from an AI answer, decide whether EVERY factual claim
in that sentence is directly supported by the supplied evidence and answers the user's question.

Rules:
- Use only the supplied evidence.
- Do not use outside knowledge.
- Reject a sentence containing any unsupported claim.
- Reject a sentence about the wrong person/entity.
- Reject corrupted, meaningless, or garbled text.
- Reject commentary about evidence unless the evidence itself supports it.
- Be conservative.
- Return only:
ACCEPT: 1,2
or
ACCEPT: NONE
""".strip()

    user_prompt = f"""QUESTION:
{question}

EVIDENCE:
{evidence_text}

ANSWER SENTENCES:
{numbered}
""".strip()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        **llm_options(MODEL_NAME, 30),
    )

    output = (response.choices[0].message.content or "").strip()

    match = re.search(r"ACCEPT\s*:\s*([^\n]+)", output, flags=re.I)

    if not match:
        return INSUFFICIENT_ANSWER

    value = match.group(1).strip()

    if value.upper().startswith("NONE"):
        return INSUFFICIENT_ANSWER

    accepted_ids = {
        int(number)
        for number in re.findall(r"\d+", value)
        if 1 <= int(number) <= len(sentences)
    }

    verified_sentences = []

    for index, sentence in enumerate(sentences, 1):
        if index not in accepted_ids:
            continue

        cleaned = re.sub(
            r"^\s*(?:(?:[-\u2022]\s*)|(?:\d+[\.\)\-:]\s*))+",
            "",
            sentence,
        ).strip()

        if cleaned:
            verified_sentences.append(cleaned)

    verified_sentences = verified_sentences[:3]

    if not verified_sentences:
        return INSUFFICIENT_ANSWER

    return " ".join(verified_sentences)
