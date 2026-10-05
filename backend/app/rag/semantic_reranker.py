import re
import unicodedata


EVIDENCE_THRESHOLD = 0.12

STOP_WORDS = {
    "??", "??", "???", "???", "???", "??", "??", "????", "??", "??", "??",
    "???", "????", "??", "???", "???", "???", "???", "?????", "??",
    "the", "a", "an", "of", "in", "on", "to", "is", "was", "were", "who",
    "what", "where", "when", "how", "why"
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", text)
    text = (
        text.replace("?", "?")
        .replace("?", "?")
        .replace("?", "?")
        .replace("?", "?")
        .replace("?", "?")
        .replace("?", "?")
    )
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def _tokens(text: str) -> list[str]:
    text = _normalize(text)
    tokens = re.findall(r"[a-z0-9\u0600-\u06FF]+", text)
    return [token for token in tokens if len(token) > 1 and token not in STOP_WORDS]


def _minimum_term_span_tokens(doc_tokens: list[str], query_terms: list[str]) -> int:
    if not doc_tokens or not query_terms:
        return 99999

    positions = []

    for term in set(query_terms):
        for index, token in enumerate(doc_tokens):
            if token == term:
                positions.append((index, term))

    if not positions:
        return 99999

    positions.sort()
    required = set(query_terms)
    counts = {}
    left = 0
    best = 99999

    for right, (position, term) in enumerate(positions):
        counts[term] = counts.get(term, 0) + 1

        while required.issubset(counts.keys()):
            best = min(best, positions[right][0] - positions[left][0])

            left_term = positions[left][1]
            counts[left_term] -= 1

            if counts[left_term] == 0:
                del counts[left_term]

            left += 1

    return best


def _score(question: str, text: str) -> float:
    query_tokens = _tokens(question)
    doc_tokens = _tokens(text)

    if not query_tokens or not doc_tokens:
        return 0.0

    query_set = set(query_tokens)
    doc_set = set(doc_tokens)

    matched = query_set & doc_set
    coverage = len(matched) / max(len(query_set), 1)

    normalized_question = _normalize(question)
    normalized_text = _normalize(text)

    phrase_bonus = 1.0 if normalized_question and normalized_question in normalized_text else 0.0

    span = _minimum_term_span_tokens(doc_tokens, list(matched))

    if span == 99999:
        proximity = 0.0
    elif span <= 8:
        proximity = 1.0
    elif span <= 20:
        proximity = 0.65
    elif span <= 40:
        proximity = 0.35
    else:
        proximity = 0.10

    density = min(
        1.0,
        len(matched) / max(min(len(doc_set), 30), 1)
    )

    return (
        0.70 * coverage
        + 0.15 * proximity
        + 0.10 * phrase_bonus
        + 0.05 * density
    )


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 180):
    text = " ".join((text or "").split())

    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(0, end - overlap)

    return chunks


def semantic_rerank(
    question: str,
    candidates: list[dict],
    top_k: int = 10,
    max_chunks: int = 120,
):
    if not candidates:
        return []

    chunk_candidates = []

    for item in candidates:
        source_text = item.get("text") or item.get("snippet") or ""

        for chunk in chunk_text(source_text):
            enriched = dict(item)
            enriched["snippet"] = chunk
            enriched["semantic_score"] = _score(question, chunk)
            chunk_candidates.append(enriched)

            if len(chunk_candidates) >= max_chunks:
                break

        if len(chunk_candidates) >= max_chunks:
            break

    chunk_candidates.sort(
        key=lambda item: item["semantic_score"],
        reverse=True,
    )

    return chunk_candidates[:top_k]


def _minimum_term_span(text: str, terms: list[str]) -> int:
    doc_tokens = _tokens(text)
    normalized_terms = []

    for term in terms:
        normalized_terms.extend(_tokens(term))

    return _minimum_term_span_tokens(doc_tokens, normalized_terms)


def has_sufficient_evidence(
    results: list[dict],
    question_terms: list[str] | None = None,
) -> bool:
    if not results:
        return False

    best = results[0]
    semantic_score = best.get("semantic_score", 0.0)

    if semantic_score < EVIDENCE_THRESHOLD:
        return False

    if not question_terms:
        return True

    text = best.get("snippet") or best.get("text") or ""
    normalized_text = _normalize(text)

    normalized_terms = []

    for term in question_terms:
        pieces = _tokens(term)
        normalized_terms.extend(pieces)

    if not normalized_terms:
        return True

    matched_terms = [
        term for term in normalized_terms
        if term in normalized_text
    ]

    coverage = len(set(matched_terms)) / max(len(set(normalized_terms)), 1)

    if coverage < 0.60:
        return False

    if len(set(matched_terms)) >= 2:
        span = _minimum_term_span(text, list(set(matched_terms)))

        if span > 40:
            return False

    return True


def sentence_rerank(
    question: str,
    candidates: list[dict],
    top_k: int = 10,
    min_length: int = 35,
):
    if not candidates:
        return []

    sentence_candidates = []

    for item in candidates:
        text = item.get("snippet") or item.get("text") or ""

        parts = re.split(
            r"(?<=[.!?\u061f])\s+|\n+",
            text,
        )

        for part in parts:
            part = " ".join(part.split()).strip()

            if len(part) < min_length:
                continue

            enriched = dict(item)
            enriched["snippet"] = part
            enriched["sentence_score"] = _score(question, part)
            sentence_candidates.append(enriched)

    sentence_candidates.sort(
        key=lambda item: item["sentence_score"],
        reverse=True,
    )

    return sentence_candidates[:top_k]
