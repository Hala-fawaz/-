import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

MODEL_NAME = "allam-2-7b"

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

Evaluate EACH numbered answer sentence independently.

Accept a sentence only when EVERY factual claim, relation, time relation,
cause, identity, number, place, and event in that sentence is directly
supported by the supplied evidence.

Rules:
- Use only the supplied evidence.
- Do not use outside knowledge.
- A sentence must directly contribute to answering the user's exact question.
- Do not accept redundant restatements of a fact already stated by an earlier accepted sentence.
- When two sentences give the same answer, keep the first clear direct sentence and reject
  later repetitions, source-commentary, or paraphrases that add no new requested information.
- Prefer concise direct answers over phrases such as "the text indicates" or
  "according to the supplied evidence" when they merely repeat the same fact.
- Reject a sentence that is factually supported but only provides background,
  biography, ancestry, commentary, or another attribute that the question did not ask for.
- For WHERE questions, keep only sentences that actually provide location information.
- For WHEN questions, keep only sentences that actually provide time information.
- For WHO questions, keep only sentences that identify or directly describe the requested entity.
- Reject a sentence if even one part is unsupported.
- Reject a sentence about the wrong person or entity.
- Reject corrupted, meaningless, or garbled text.
- Reject self-contradictory statements.
- Reject claims that create a new temporal relation such as before/after
  unless that exact relation is supported by the evidence.
- Reject claims that create a new causal relation unless the evidence states it.
- Do not combine separate evidence fragments into a new fact that no supplied
  passage actually states.
- A heading or topic label does not by itself prove an event happened.
- If the evidence says only "before event E, X did Y", that does NOT support
  a claim that "X performed event E before event E".
- Be conservative.

Return only:
ACCEPT: 1,2

or:
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
        max_tokens=30,
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
