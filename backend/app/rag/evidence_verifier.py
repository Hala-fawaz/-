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


def verify_evidence(question: str, candidates: list[dict], max_items: int = 8):
    candidates = candidates[:max_items]

    if not candidates:
        return []

    blocks = []

    for index, item in enumerate(candidates, 1):
        text = item.get("snippet") or item.get("text") or ""

        blocks.append(
            f"[{index}]\n{text}"
        )

    evidence = "\n\n".join(blocks)

    system_prompt = """
You are a strict evidence verifier.

For each numbered evidence item, decide whether it DIRECTLY helps answer the user's exact question about the SAME subject/entity.

Rules:
- Use only the supplied question and evidence.
- Reject an item that merely shares similar words.
- Reject an item about a different person, place, event, date, object, or subject.
- Reject background text that does not directly support an answer.
- Do not use outside knowledge.
- Be conservative: when uncertain, reject.
- Return only this exact format:
ACCEPT: 1,3
- If none are valid, return:
ACCEPT: NONE
""".strip()

    user_prompt = f"""QUESTION:
{question}

EVIDENCE ITEMS:
{evidence}
""".strip()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        max_tokens=40,
    )

    output = (response.choices[0].message.content or "").strip()

    match = re.search(r"ACCEPT\s*:\s*([^\n]+)", output, flags=re.I)

    if not match:
        return []

    value = match.group(1).strip()

    if value.upper().startswith("NONE"):
        return []

    accepted_ids = {
        int(number)
        for number in re.findall(r"\d+", value)
        if 1 <= int(number) <= len(candidates)
    }

    return [
        item
        for index, item in enumerate(candidates, 1)
        if index in accepted_ids
    ]
