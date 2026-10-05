import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from .semantic_reranker import _question_type


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

MODEL_NAME = "allam-2-7b"

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

INSUFFICIENT_ANSWER = "\u0644\u0645 \u0623\u062c\u062f \u0641\u064a \u0627\u0644\u0645\u0635\u0627\u062f\u0631 \u0627\u0644\u0645\u062a\u0627\u062d\u0629 \u062f\u0644\u064a\u0644\u064b\u0627 \u0643\u0627\u0641\u064a\u064b\u0627 \u0644\u0644\u0625\u062c\u0627\u0628\u0629 \u0639\u0646 \u0647\u0630\u0627 \u0627\u0644\u0633\u0624\u0627\u0644."


def _clean_answer(answer: str) -> str:
    answer = (answer or "").strip()

    source_labels = (
        "\u0627\u0644\u0645\u0635\u0627\u062f\u0631",
        "\u0627\u0644\u0645\u0631\u0627\u062c\u0639",
        "\u0627\u0644\u0645\u0635\u0627\u062f\u0631 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645\u0629",
    )

    for label in source_labels:
        marker = "\n" + label
        if marker in answer:
            answer = answer.split(marker, 1)[0]

    answer = re.sub(r"\s+", " ", answer).strip()

    if not answer:
        return INSUFFICIENT_ANSWER

    return answer


def generate_answer(question: str, sources: list[dict]) -> str:
    if not sources:
        return INSUFFICIENT_ANSWER

    # For factual typed questions, preserve the strongest verified
    # evidence verbatim instead of letting the language model
    # introduce a different person, place, date, or number.
    question_kind = _question_type(question)

    if question_kind != "general":
        for source in sources:
            text = (
                source.get("snippet")
                or source.get("text")
                or ""
            ).strip()

            if text:
                return _clean_answer(text)

        return INSUFFICIENT_ANSWER

    context_parts = []

    for i, source in enumerate(sources[:4], 1):
        text = source.get("snippet") or source.get("text", "")
        text = text.replace("[", "").replace("]", "").strip()

        if not text:
            continue

        context_parts.append(
            f"EVIDENCE {i}:\n{text}"
        )

    if not context_parts:
        return INSUFFICIENT_ANSWER

    context = "\n\n".join(context_parts)

    system_prompt = """
You are the grounded knowledge guide for the Risalah platform.

Answer the user's Arabic question ONLY from the supplied evidence.

Mandatory rules:
1. Do not use outside knowledge, memory, assumptions, calculations, or guessed facts.
2. Every factual statement in the answer must be directly supported by the supplied evidence.
3. Answer the exact question directly and concisely, normally in one to three Arabic sentences.
4. Do not copy footnotes, bibliographies, reference numbers, editorial notes, or unrelated surrounding text.
5. Do not mention a date, number, place, person, cause, or detail unless the evidence explicitly supports it.
6. If the evidence contains different accounts or conflicting dates/numbers, state that the available sources differ and summarize only the alternatives actually present.
7. If the evidence does not actually answer the question, respond exactly with:
   ?? ??? ?? ??????? ??????? ?????? ?????? ??????? ?? ??? ??????.
8. Do not provide personal religious rulings or fatwas.
9. Do not list sources in the answer; the application displays them separately.
10. Start directly with the answer. Do not say "according to the context" or describe your reasoning.
""".strip()

    user_prompt = f"""QUESTION:
{question}

TRUSTED EVIDENCE:
{context}

Write only the grounded Arabic answer.
""".strip()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        max_tokens=140,
    )

    answer = response.choices[0].message.content

    return _clean_answer(answer)
