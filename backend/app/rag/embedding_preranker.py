from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "intfloat/multilingual-e5-small"


@lru_cache(maxsize=1)
def load_embedding_model():
    return SentenceTransformer(MODEL_NAME)


def embedding_prerank(
    question: str,
    candidates: list[dict],
    top_k: int = 24,
):
    if not candidates:
        return []

    model = load_embedding_model()

    query_text = "query: " + question

    passage_texts = [
        "passage: " + (
            item.get("snippet")
            or item.get("text")
            or ""
        )
        for item in candidates
    ]

    query_embedding = model.encode(
        [query_text],
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]

    passage_embeddings = model.encode(
        passage_texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    scores = np.dot(
        passage_embeddings,
        query_embedding,
    )

    ranked = []

    for item, score in zip(candidates, scores):
        enriched = dict(item)
        enriched["embedding_score"] = float(score)
        ranked.append(enriched)

    ranked.sort(
        key=lambda item: item["embedding_score"],
        reverse=True,
    )

    return ranked[:top_k]
