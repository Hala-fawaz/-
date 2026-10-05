from .embedder import load_embedding_model
from .vector_store import search_index


def retrieve(query, index, chunks, top_k=5):
    model = load_embedding_model()

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
    )

    scores, indices = search_index(
        index,
        query_embedding,
        top_k=top_k,
    )

    results = []

    for score, index_number in zip(scores, indices):
        if index_number == -1:
            continue

        results.append({
            "text": chunks[index_number]["text"],
            "page": chunks[index_number]["page"],
            "source": chunks[index_number]["source"],
            "score": float(score),
        })

    return results

