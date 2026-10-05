from functools import lru_cache

from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
EVIDENCE_THRESHOLD = -1.2


@lru_cache(maxsize=1)
def load_reranker():
    return CrossEncoder(MODEL_NAME)


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

    model = load_reranker()

    chunk_candidates = []

    for item in candidates:
        source_text = item.get("text") or item.get("snippet") or ""

        for chunk in chunk_text(source_text):
            enriched = dict(item)
            enriched["snippet"] = chunk
            chunk_candidates.append(enriched)

            if len(chunk_candidates) >= max_chunks:
                break

        if len(chunk_candidates) >= max_chunks:
            break

    if not chunk_candidates:
        return []

    pairs = [
        [question, item["snippet"]]
        for item in chunk_candidates
    ]

    scores = model.predict(pairs)

    reranked = []

    for item, score in zip(chunk_candidates, scores):
        enriched = dict(item)
        enriched["semantic_score"] = float(score)
        reranked.append(enriched)

    reranked.sort(
        key=lambda item: item["semantic_score"],
        reverse=True,
    )

    return reranked[:top_k]


def _minimum_term_span(text: str, terms: list[str]) -> int:
    if not terms:
        return 99999

    positions = []

    for term in terms:
        start = 0
        while True:
            index = text.find(term, start)
            if index < 0:
                break
            positions.append((index, term))
            start = index + 1

    if not positions:
        return 99999

    positions.sort()
    required = set(terms)
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


def has_sufficient_evidence(
    results: list[dict],
    question_terms: list[str] | None = None,
) -> bool:
    if not results:
        return False

    best = results[0]
    semantic_score = best.get("semantic_score", -999)

    if semantic_score < EVIDENCE_THRESHOLD:
        return False

    if not question_terms:
        return True

    text = best.get("snippet") or best.get("text") or ""

    matched_terms = [
        term for term in question_terms
        if term in text
    ]

    coverage = len(matched_terms) / max(len(question_terms), 1)

    if coverage < 0.80:
        return False

    if len(matched_terms) >= 2:
        span = _minimum_term_span(text, matched_terms)

        if span > 300:
            return False

    return True


def sentence_rerank(
    question: str,
    candidates: list[dict],
    top_k: int = 10,
    min_length: int = 35,
):
    import re

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
            sentence_candidates.append(enriched)

    if not sentence_candidates:
        return []

    model = load_reranker()

    scores = model.predict([
        [question, item["snippet"]]
        for item in sentence_candidates
    ])

    reranked = []

    for item, score in zip(sentence_candidates, scores):
        enriched = dict(item)
        enriched["sentence_score"] = float(score)
        reranked.append(enriched)

    reranked.sort(
        key=lambda item: item["sentence_score"],
        reverse=True,
    )

    return reranked[:top_k]
