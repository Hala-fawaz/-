import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

MODEL_NAME = "allam-2-7b"
MAX_TOKENS = 220
MAX_SENTENCES = 3

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

INSUFFICIENT_ANSWER = "\u0644\u0645 \u0623\u062c\u062f \u0641\u064a \u0627\u0644\u0645\u0635\u0627\u062f\u0631 \u0627\u0644\u0645\u062a\u0627\u062d\u0629 \u062f\u0644\u064a\u0644\u064b\u0627 \u0643\u0627\u0641\u064a\u064b\u0627 \u0644\u0644\u0625\u062c\u0627\u0628\u0629 \u0639\u0646 \u0647\u0630\u0627 \u0627\u0644\u0633\u0624\u0627\u0644."

# Opening words of the abstention sentence ("lam ajid").
ABSTAIN_MARKER = "\u0644\u0645 \u0623\u062c\u062f"

# Words showing the model is talking about the evidence itself
# ("adilla" = evidence, "dalil" = proof) instead of answering.
META_WORDS = (
    "\u0623\u062f\u0644\u0629",
    "\u062f\u0644\u064a\u0644",
)

# Clauses like "according to the mentioned evidence": a lead word
# (wifq / hasab / istinad / bina') followed, before the next comma or
# full stop, by a word for evidence / sources / texts.
META_CLAUSE_RE = re.compile(
    r"[\u060c,]?\s*"
    r"(?:\u0648\u0641\u0642|\u062d\u0633\u0628|\u0627\u0633\u062a\u0646\u0627\u062f|\u0628\u0646\u0627\u0621)"
    r"[^\u060c,.!?\u061f]*?"
    r"(?:\u0623\u062f\u0644\u0629|\u062f\u0644\u064a\u0644|\u0645\u0635\u0627\u062f\u0631|\u0646\u0635\u0648\u0635)"
    r"[^\u060c,.!?\u061f]*"
)

# Invisible direction / joiner characters found in the source files.
ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200f\ufeff]")

# Footnote reference marks inside the main text, e.g. <<2>> or [2].
FOOTNOTE_MARK_RE = re.compile(r"\u00ab\s*\d+\s*\u00bb|\[\s*\d+\s*\]")

# A passage that starts with "(3)" is the body of a footnote
# (editor note / bibliography), not the main text.
FOOTNOTE_BODY_RE = re.compile(r"^\(\s*\d+\s*\)")

# List numbering at the start of a passage, e.g. "2- ".
LEADING_NUMBER_RE = re.compile(r"^\d+\s*[-.)]\s*")

# Optional volume suffix of a running title, e.g. " - (jim) 6".
VOLUME_SUFFIX = r"(?:\s*-\s*\u062c\u0640?\s*\d+)?"

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!\u061f])\s+")

# Leftovers of the old corrupted prompt ("?? ??? ...").
QUESTION_MARK_RUN_RE = re.compile(r"\?{2,}[\s?]*")


def _source_title(source_name: str) -> str:
    name = (source_name or "").replace("\\", "/").split("/")[0].strip()

    if name.lower().endswith(".txt"):
        name = name[:-4]

    return name.strip()


def _clean_evidence_text(text: str, source_name: str) -> str:
    text = ZERO_WIDTH_RE.sub("", text or "")
    text = FOOTNOTE_MARK_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()

    # The page layout glues the book's running title to the end of
    # the last sentence on a page; remove it.
    title = _source_title(source_name)
    if title:
        text = re.sub(
            re.escape(title) + VOLUME_SUFFIX + r"\s*$",
            "",
            text,
        ).strip()

    text = text.replace("[", "").replace("]", "").strip()

    return text


def _trim_incomplete(answer: str) -> str:
    last_stop = max(answer.rfind(ch) for ch in (".", "!", "\u061f"))

    if last_stop == -1:
        return answer

    return answer[: last_stop + 1]


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

    answer = QUESTION_MARK_RUN_RE.sub(" ", answer)
    answer = re.sub(r"\s+", " ", answer).strip()

    if not answer or answer.startswith(ABSTAIN_MARKER):
        return INSUFFICIENT_ANSWER

    kept = []

    for sentence in SENTENCE_SPLIT_RE.split(answer):
        # An abstention sentence appended after a real answer.
        if ABSTAIN_MARKER in sentence:
            continue

        # Remove "according to the evidence" clauses, then any comma
        # or space left dangling at the start.
        sentence = META_CLAUSE_RE.sub("", sentence).strip()
        sentence = sentence.lstrip("\u060c, ").strip()

        # Sentences still about the evidence itself carry no facts.
        if any(word in sentence for word in META_WORDS):
            continue

        # Fragments left after removing a clause (e.g. "this.").
        if len(sentence.split()) < 3:
            continue

        kept.append(sentence)

    kept = kept[:MAX_SENTENCES]

    if not kept:
        return INSUFFICIENT_ANSWER

    return " ".join(kept)


def generate_answer(question: str, sources: list[dict]) -> str:
    if not sources:
        return INSUFFICIENT_ANSWER

    context_parts = []

    for source in sources[:4]:
        raw_text = source.get("snippet") or source.get("text", "")
        text = _clean_evidence_text(raw_text, source.get("source", ""))

        if not text or FOOTNOTE_BODY_RE.match(text):
            continue

        text = LEADING_NUMBER_RE.sub("", text).strip()

        if text:
            context_parts.append(text)

    if not context_parts:
        return INSUFFICIENT_ANSWER

    # Plain separators instead of numbered labels, so the model has
    # no "evidence 1 / evidence 2" names to talk about.
    context = "\n---\n".join(context_parts)

    system_prompt = f"""
You are the grounded knowledge guide for the Risalah platform.

Answer the user's Arabic question ONLY from the supplied evidence.

Mandatory rules:
1. Do not use outside knowledge, memory, assumptions, calculations, or guessed facts.
2. Every factual statement in the answer must be directly supported by the supplied evidence.
3. Answer the exact question directly and concisely, in one to three Arabic sentences.
4. Do not copy footnotes, bibliographies, reference numbers, editorial notes, or unrelated surrounding text.
5. Do not mention a date, number, place, person, cause, or detail unless the evidence explicitly supports it.
6. If the evidence contains different accounts or conflicting dates/numbers, state that the available sources differ and summarize only the alternatives actually present.
7. If the evidence does not actually answer the question, respond exactly with:
   {INSUFFICIENT_ANSWER}
8. Do not provide personal religious rulings or fatwas.
9. Never mention the evidence itself, passage numbers, book titles, authors, or page numbers; the application displays sources separately.
10. Start directly with the answer. Do not say "according to the evidence" or describe your reasoning.
""".strip()

    user_prompt = f"""QUESTION:
{question}

TRUSTED EVIDENCE (passages separated by ---):
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
        max_tokens=MAX_TOKENS,
    )

    choice = response.choices[0]
    answer = choice.message.content or ""

    # Cut a reply that hit the token limit back to its last full sentence.
    if choice.finish_reason == "length":
        answer = _trim_incomplete(answer)

    return _clean_answer(answer)