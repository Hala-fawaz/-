import sqlite3
from pathlib import Path

from .txt_loader import load_txt


BACKEND_DIR = Path(__file__).resolve().parents[2]
SOURCES_DIR = BACKEND_DIR / "knowledge" / "sources"
INDEX_DIR = BACKEND_DIR / "knowledge" / "index"
DB_PATH = INDEX_DIR / "knowledge_fts.db"


def build_fts_index():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE VIRTUAL TABLE knowledge_fts USING fts5(
            text,
            source UNINDEXED,
            page UNINDEXED,
            tokenize='unicode61'
        )
    """)

    total_files = 0
    total_pages = 0

    for path in sorted(SOURCES_DIR.rglob("*.txt")):
        pages = load_txt(str(path))
        relative_source = str(path.relative_to(SOURCES_DIR))

        rows = [
            (
                page["text"],
                relative_source,
                str(page["page"])
            )
            for page in pages
            if page["text"].strip()
        ]

        cursor.executemany(
            "INSERT INTO knowledge_fts(text, source, page) VALUES (?, ?, ?)",
            rows,
        )

        total_files += 1
        total_pages += len(rows)

        if total_files % 25 == 0:
            connection.commit()
            print(f"Indexed files: {total_files} | Pages: {total_pages}")

    connection.commit()
    connection.close()

    print(f"Files indexed: {total_files}")
    print(f"Pages indexed: {total_pages}")
    print(f"FTS database: {DB_PATH}")


if __name__ == "__main__":
    build_fts_index()
