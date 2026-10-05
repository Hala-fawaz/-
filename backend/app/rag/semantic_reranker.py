import re
from functools import lru_cache

from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

# This cross-encoder returns raw logits, not probabilities:
# sigmoid(score) is the probability that the text is relevant,
# so a score of 0.0 means 50%. The old chunk threshold of -1.2
# accepted text the model rated only ~23% relevant.
EVIDENCE_THRESHOLD = 0.0
SENTENCE_THRESHOLD = 0.0

# Share of question terms a chunk must contain literally. The old
# value (0.80) rejected correct passages that said "the Prophet"
# without repeating "Muhammad", or that never used the word "start".
# The cross-encoder score is now the main relevance check.
MIN_TERM_COVERAGE = 0.50

# Invisible direction / joiner characters found in the source files.
ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200f\ufeff]")


@lru_cache(maxsize=1)
def load_reranker():
    return CrossEncoder(MODEL_NAME)


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 180):
    # Normalise spaces inside each line but KEEP the line breaks.
    # Headings, footnotes and the running book title sit on their own
    # lines in the source pages, and sentence_rerank splits on line
    # breaks to separate them from the real sentences.
    text = ZERO_WIDTH_RE.sub("", text or "")
    lines = (" ".join(line.split()) for line in text.splitlines())
    text = "\n".join(line for line in lines if line)

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


def _term_hits(text: str, terms: list[str]) -> int:
    return sum(1 for term in terms if term in text)


def semantic_rerank(
    question: str,
    candidates: list[dict],
    top_k: int = 10,
    max_chunks: int = 120,
    question_terms: list[str] | None = None,
    chunks_per_page: int = 2,
):
    if not candidates:
        return []

    model = load_reranker()
    terms = question_terms or []

    chunk_candidates = []

    for item in candidates:
        source_text = item.get("text") or item.get("snippet") or ""
        chunks = chunk_text(source_text)

        # Long pages split into many chunks. Taking them in order let a
        # few long pages use up the whole budget, so later pages were
        # never scored. Keep only the chunks of each page that mention
        # the most question terms (sorted() is stable, so ties keep
        # their original order).
        if terms and len(chunks) > chunks_per_page:
            chunks = sorted(
                chunks,
                key=lambda chunk: _term_hits(chunk, terms),
                reverse=True,
            )[:chunks_per_page]

        for chunk in chunks:
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

    if coverage < MIN_TERM_COVERAGE:
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
        score = float(score)

        # Below 0.0 the model thinks the sentence is more likely
        # irrelevant than relevant; never pass it on as evidence.
        if score < SENTENCE_THRESHOLD:
            continue

        enriched = dict(item)
        enriched["sentence_score"] = score
        reranked.append(enriched)

    reranked.sort(
        key=lambda item: item["sentence_score"],
        reverse=True,
    )

    return reranked[:top_k]
