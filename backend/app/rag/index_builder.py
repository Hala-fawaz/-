import json
from pathlib import Path

from .chunker import chunk_pages
from .embedder import create_embeddings
from .pdf_loader import load_pdf
from .txt_loader import load_txt
from .vector_store import build_index, save_index


BACKEND_DIR = Path(__file__).resolve().parents[2]
SOURCES_DIR = BACKEND_DIR / "knowledge" / "sources"
INDEX_DIR = BACKEND_DIR / "knowledge" / "index"

FAISS_PATH = INDEX_DIR / "knowledge.faiss"
CHUNKS_PATH = INDEX_DIR / "chunks.json"


def load_all_sources():
    pages = []

    for path in sorted(SOURCES_DIR.rglob("*")):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()

        if suffix == ".txt":
            print(f"Loading TXT: {path.name}")
            pages.extend(load_txt(str(path)))

        elif suffix == ".pdf":
            print(f"Loading PDF: {path.name}")
            pages.extend(load_pdf(str(path)))

    return pages


def build_knowledge_index():
    pages = load_all_sources()

    if not pages:
        raise RuntimeError("No supported knowledge sources were found.")

    chunks = chunk_pages(pages)

    print(f"Pages loaded: {len(pages)}")
    print(f"Chunks created: {len(chunks)}")
    print("Creating embeddings...")

    embeddings = create_embeddings(chunks)

    print("Building FAISS index...")
    index = build_index(embeddings)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    save_index(index, str(FAISS_PATH))

    with CHUNKS_PATH.open("w", encoding="utf-8") as file:
        json.dump(chunks, file, ensure_ascii=False)

    print(f"FAISS saved: {FAISS_PATH}")
    print(f"Metadata saved: {CHUNKS_PATH}")
    print(f"Vectors saved: {index.ntotal}")

    return {
        "pages": len(pages),
        "chunks": len(chunks),
        "vectors": index.ntotal,
    }


if __name__ == "__main__":
    build_knowledge_index()
