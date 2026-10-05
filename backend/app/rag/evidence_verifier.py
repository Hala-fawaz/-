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


def _normalize_arabic(text: str) -> str:
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text or "")
    text = (
        text.replace("\u0623", "\u0627")
            .replace("\u0625", "\u0627")
            .replace("\u0622", "\u0627")
            .replace("\u0649", "\u064a")
    )
    return re.sub(r"\s+", " ", text).strip()


def _relation_clause_filter(question: str, candidates: list[dict]) -> list[dict]:
    q = _normalize_arabic(question)

    tokens = re.findall(r"[\u0600-\u06FF]+", q)
    if len(tokens) < 2:
        return candidates

    question_type = tokens[0]

    relation_types = {
        "\u0627\u064a\u0646",
        "\u0645\u062a\u064a",
        "\u0643\u0645",
        "\u0643\u064a\u0641",
        "\u0644\u0645\u0627\u0630\u0627",
    }

    if question_type not in relation_types:
        return candidates

    stopwords = {
        "\u0641\u064a", "\u0645\u0646", "\u0627\u0644\u064a",
        "\u0639\u0644\u064a", "\u0639\u0646",
        "\u0647\u0648", "\u0647\u064a",
    }

    content = [
        token
        for token in tokens[1:]
        if token not in stopwords and len(token) >= 2
    ]

    if len(content) < 2:
        return candidates

    relation = content[0]
    entity_markers = [
        token
        for token in content[1:]
        if len(token) >= 3
    ]

    # General title equivalence used across the Islamic corpus.
    if "\u0627\u0644\u0646\u0628\u064a" in entity_markers:
        entity_markers.extend([
            "\u0627\u0644\u0631\u0633\u0648\u0644",
            "\u0631\u0633\u0648\u0644 \u0627\u0644\u0644\u0647",
        ])

    entity_markers = list(dict.fromkeys(entity_markers))

    def has_required_answer_type(clause: str) -> bool:
        if question_type == "\u0627\u064a\u0646":
            return bool(
                re.search(
                    r"(?:\b\u0641\u064a\b|\b\u0641\u064a\u0647\b|\b\u0641\u064a\u0647\u0627\b|"
                    r"\b\u0639\u0646\u062f\b|\b\u062f\u0627\u062e\u0644\b|\b\u062e\u0627\u0631\u062c\b|"
                    r"\b\u0642\u0631\u0628\b|\b\u0645\u0643\u0627\u0646\b|\b\u0645\u0648\u0636\u0639\b)",
                    clause,
                )
            )

        if question_type == "\u0645\u062a\u064a":
            return bool(
                re.search(
                    r"\d|"
                    r"(?:\u0633\u0646\u0629|\u0639\u0627\u0645|\u064a\u0648\u0645|\u0634\u0647\u0631|"
                    r"\u0644\u064a\u0644\u0629|\u0642\u0628\u0644|\u0628\u0639\u062f|\u0627\u0644\u0647\u062c\u0631\u0629|"
                    r"\u0631\u0645\u0636\u0627\u0646|\u0645\u062d\u0631\u0645|\u0635\u0641\u0631|\u0631\u0628\u064a\u0639|"
                    r"\u0634\u0639\u0628\u0627\u0646|\u0634\u0648\u0627\u0644)",
                    clause,
                )
            )

        if question_type == "\u0643\u0645":
            return bool(
                re.search(r"\d|[\u0660-\u0669]", clause)
            )

        return True

    accepted = []

    for item in candidates:
        raw = item.get("snippet") or item.get("text") or ""
        normalized = _normalize_arabic(raw)

        clauses = [
            part.strip()
            for part in re.split(r"[\u060C\u061B\u061F,;.!?\n]+", normalized)
            if part.strip()
        ]

        valid = False

        for clause in clauses:
            if relation not in clause:
                continue

            if not any(marker in clause for marker in entity_markers):
                continue

            if not has_required_answer_type(clause):
                continue

            valid = True
            break

        if valid:
            accepted.append(item)

    return accepted


def verify_evidence(question: str, candidates: list[dict], max_items: int = 8):
    candidates = _relation_clause_filter(question, candidates)
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

The candidate evidence has already passed a deterministic filter for the
requested relation and answer type.

For each numbered item, decide whether its relevant claim directly answers
the user's exact question about the SAME entity.

Rules:
- Use only the question and supplied evidence.
- Accept clear titles, aliases, shortened names, or pronouns when the text
  clearly refers to the same requested entity.
- Do not require identical wording between the question and evidence.
- Reject evidence when the relevant event or attribute belongs to another entity.
- Reject keyword overlap, nearby mentions, background information, or unrelated facts.
- Do not use outside knowledge.
- When uncertain about the entity or relation, reject.

Return only:
ACCEPT: 1,3

If none are valid:
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
        **llm_options(MODEL_NAME, 40),
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
