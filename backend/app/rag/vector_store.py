from pathlib import Path

import faiss
import numpy as np


def build_index(embeddings):
    embeddings = np.asarray(embeddings, dtype="float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index


def save_index(index, index_path: str):
    path = Path(index_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    serialized = faiss.serialize_index(index)
    path.write_bytes(serialized.tobytes())


def load_index(index_path: str):
    path = Path(index_path)

    if not path.exists():
        raise FileNotFoundError(f"FAISS index not found: {path}")

    serialized = np.frombuffer(path.read_bytes(), dtype="uint8")
    return faiss.deserialize_index(serialized)


def search_index(index, query_embedding, top_k=5):
    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )

    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)

    scores, indices = index.search(query_embedding, top_k)

    return scores[0], indices[0]
