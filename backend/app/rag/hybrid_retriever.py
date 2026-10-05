import re
from difflib import SequenceMatcher

from .fts_retriever import search_fts, extract_terms


def _clean(text: str):
    text = re.sub(r"[\[\].…]", " ", text)
    return " ".join(text.split()).strip()


def _looks_like_toc(text: str) -> bool:
    return text.count(".") > 25


def _term_span(text: str, terms: list[str]) -> int:
    positions = []
    for term in terms:
        index = text.find(term)
        if index >= 0:
            positions.append(index)
    if len(positions) < 2:
        return 10_000
    return max(positions) - min(positions)


def _intent_score(question: str, text: str) -> int:
    score = 0

    when_words = ("\u0645\u062a\u0649", "\u062a\u0627\u0631\u064a\u062e", "\u0648\u0644\u0627\u062f\u0629", "\u0645\u064a\u0644\u0627\u062f")
    where_words = ("\u0623\u064a\u0646", "\u0627\u064a\u0646", "\u0645\u0643\u0627\u0646", "\u0645\u0648\u0636\u0639")
    who_words = ("\u0645\u0646",)
    how_many_words = ("\u0643\u0645", "\u0639\u062f\u062f")

    if any(word in question for word in when_words):
        if re.search(r"(?:\u062a\u0627\u0631\u064a\u062e|\u0645\u064a\u0644\u0627\u062f|\u0648\u0644\u0627\u062f\w*)", text):
            score += 8
        if re.search(r"\u0648\u0644\u062f.{0,30}(?:\u0639\u0627\u0645|\u0633\u0646\u0629|\u064a\u0648\u0645)", text):
            score += 8
        if re.search(r"(?:\u0639\u0627\u0645|\u0633\u0646\u0629)\s+(?:\d{2,4}|[\u0660-\u0669]{2,4})", text):
            score += 6
        if re.search(r"\b\d{3,4}\b|[\u0660-\u0669]{3,4}", text):
            score += 4
        for word in ("\u0639\u0627\u0645", "\u0633\u0646\u0629", "\u064a\u0648\u0645", "\u0627\u0644\u0627\u062b\u0646\u064a\u0646", "\u0631\u0628\u064a\u0639", "\u0631\u0645\u0636\u0627\u0646"):
            if word in text:
                score += 2


        date_parts = 0

        if re.search(r"(?:\u0627\u0644\u0627\u062b\u0646\u064a\u0646|\u0627\u0644\u062b\u0644\u0627\u062b\u0627\u0621|\u0627\u0644\u0623\u0631\u0628\u0639\u0627\u0621|\u0627\u0644\u062e\u0645\u064a\u0633|\u0627\u0644\u062c\u0645\u0639\u0629|\u0627\u0644\u0633\u0628\u062a|\u0627\u0644\u0623\u062d\u062f)", text):
            date_parts += 1

        if re.search(r"(?:\u0645\u062d\u0631\u0645|\u0635\u0641\u0631|\u0631\u0628\u064a\u0639\s+\u0627\u0644\u0623\u0648\u0644|\u0631\u0628\u064a\u0639\s+\u0627\u0644\u0622\u062e\u0631|\u062c\u0645\u0627\u062f\u0649|\u0631\u062c\u0628|\u0634\u0639\u0628\u0627\u0646|\u0631\u0645\u0636\u0627\u0646|\u0634\u0648\u0627\u0644|\u0630\u0648\s+\u0627\u0644\u0642\u0639\u062f\u0629|\u0630\u0648\s+\u0627\u0644\u062d\u062c\u0629)", text):
            date_parts += 1

        if re.search(r"(?:\u0633\u0646\u0629|\u0639\u0627\u0645).{0,20}(?:\d{3,4}|[\u0660-\u0669]{3,4})", text):
            date_parts += 1

        if "\u0639\u0627\u0645 \u0627\u0644\u0641\u064a\u0644" in text or "\u062d\u0627\u062f\u062b\u0629 \u0627\u0644\u0641\u064a\u0644" in text:
            date_parts += 1

        if re.search(r"(?:\u0648\u0644\u062f|\u0645\u064a\u0644\u0627\u062f|\u0648\u0644\u0627\u062f\w*).{0,180}(?:\u0633\u0646\u0629|\u0639\u0627\u0645).{0,20}(?:\d{3,4}|[\u0660-\u0669]{3,4})", text):
            score += 14

        score += date_parts * 4
        if date_parts >= 3:
            score += 8


    importance_words = (
        "\u0623\u0647\u0645\u064a\u0629",
        "\u0644\u0645\u0627\u0630\u0627",
        "\u0633\u0628\u0628",
        "\u062f\u0648\u0631",
        "\u0623\u062b\u0631",
    )

    if any(word in question for word in importance_words):
        for phrase, weight in (
            ("\u0627\u0644\u062f\u0648\u0631", 8),
            ("\u0623\u0647\u0645\u064a\u0629", 8),
            ("\u0645\u0631\u0643\u0632", 6),
            ("\u0645\u0646\u0637\u0644\u0642", 8),
            ("\u0628\u062f\u0627\u064a\u0629", 4),
            ("\u0627\u0644\u062f\u0639\u0648\u0629 \u0627\u0644\u0633\u0631\u064a\u0629", 8),
            ("\u0627\u0644\u062f\u0648\u0631 \u0627\u0644\u0645\u0643\u064a", 8),
            ("\u0623\u0647\u0644 \u0645\u0643\u0629", 5),
            ("\u0623\u0631\u0636 \u0645\u0643\u0629", 5),
        ):
            if phrase in text:
                score += weight

        if re.search(
            r"(?:\u0644\u0623\u0646|\u0644\u0630\u0627|\u062d\u064a\u062b|\u0628\u0633\u0628\u0628|\u0645\u0645\u0627|\u0623\u062f\u0649|\u0633\u0627\u0639\u062f)",
            text,
        ):
            score += 6

        if re.search(
            r"(?:\u0645\u0631\u062d\u0644\u0629|\u0628\u062f\u0627\u064a\u0629).{0,80}\u0627\u0644\u062f\u0639\u0648\u0629",
            text,
        ):
            score += 6


    if any(word in question for word in importance_words):
        for phrase, weight in (
            ("\u0645\u0631\u0643\u0632 \u062f\u064a\u0646", 12),
            ("\u0627\u0644\u0625\u0635\u0644\u0627\u062d", 10),
            ("\u0645\u0646 \u0627\u0644\u062d\u0643\u0645\u0629", 12),
            ("\u0644\u0626\u0644\u0627", 8),
            ("\u064a\u0632\u062f\u0627\u062f \u0639\u0633\u0631", 8),
            ("\u0627\u0644\u0645\u0642\u0635\u0648\u062f", 6),
            ("\u0627\u0644\u0643\u0639\u0628\u0629", 6),
        ):
            if phrase in text:
                score += weight

    if any(word in question for word in where_words):
        for word in ("\u0641\u064a", "\u0645\u0643\u0629", "\u0627\u0644\u0645\u062f\u064a\u0646\u0629", "\u0628\u0644\u062f", "\u0645\u0643\u0627\u0646", "\u0645\u0648\u0636\u0639"):
            if word in text:
                score += 2

    if any(word in question.split() for word in who_words):
        if re.search(r"(?:\u0647\u0648|\u0647\u064a|\u0627\u0633\u0645\u0647|\u0627\u0633\u0645\u0647\u0627)", text):
            score += 4

    if any(word in question for word in how_many_words):
        if re.search(r"\d+|[\u0660-\u0669]+", text):
            score += 5

    return score


def hybrid_retrieve(question: str, top_k: int = 8, candidate_k: int = 100):
    candidates = search_fts(question, top_k=candidate_k)
    terms = extract_terms(question)

    ranked = []
    seen = set()

    for item in candidates:
        if _looks_like_toc(item["text"]):
            continue

        cleaned = _clean(item["snippet"])
        fingerprint = cleaned[:300]

        if fingerprint in seen:
            continue

        seen.add(fingerprint)

        matched_terms = sum(
            1 for term in terms
            if term in cleaned
        )

        span = _term_span(cleaned, terms)
        proximity_score = max(0, 12 - min(span, 600) // 50)
        intent_score = _intent_score(question, cleaned)

        item = dict(item)
        item["matched_terms"] = matched_terms
        item["intent_score"] = intent_score
        item["proximity_score"] = proximity_score
        ranked.append(item)

    ranked.sort(
        key=lambda item: (
            item["intent_score"],
            item["matched_terms"],
            item["proximity_score"],
            -item["bm25_score"],
        ),
        reverse=True,
    )

    results = []
    seen_sources = set()
    seen_texts = []

    for item in ranked:
        if item["source"] in seen_sources:
            continue

        candidate_text = _clean(item["snippet"])

        if any(
            SequenceMatcher(None, candidate_text, previous).ratio() >= 0.90
            for previous in seen_texts
        ):
            continue

        seen_sources.add(item["source"])
        seen_texts.append(candidate_text)
        results.append(item)

        if len(results) >= top_k:
            break

    return results
