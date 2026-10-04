import re

from .fts_retriever import search_fts, extract_terms


def _clean(text: str):
    text = re.sub(r"[\[\].…]", " ", text)
    return " ".join(text.split()).strip()


def _looks_like_toc(text: str) -> bool:
    return text.count(".") > 25


def hybrid_retrieve(question: str, top_k: int = 8, candidate_k: int = 100):
    # Search happens across the entire indexed knowledge base.
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

        item = dict(item)
        item["matched_terms"] = matched_terms
        ranked.append(item)

    ranked.sort(
        key=lambda item: (
            item["matched_terms"],
            -item["bm25_score"],
        ),
        reverse=True,
    )

    results = []
    seen_sources = set()

    for item in ranked:
        if item["source"] in seen_sources:
            continue

        seen_sources.add(item["source"])
        results.append(item)

        if len(results) >= top_k:
            break

    return results
