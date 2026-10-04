import re
import sqlite3
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BACKEND_DIR / "knowledge" / "index" / "knowledge_fts.db"

ARABIC_STOPWORDS = {
    "ما", "ماذا", "من", "في", "على", "عن", "إلى", "الى",
    "هل", "كيف", "متى", "أين", "اين", "لماذا", "هو", "هي",
    "كان", "كانت", "هذا", "هذه", "ذلك", "التي", "الذي",
}

INTENT_WORDS = {
    "أهمية", "اهمية", "أهم", "اهم",
    "اشرح", "وضح", "اذكر",
    "حدثني", "أخبرني", "اخبرني",
}


def extract_terms(question: str):
    words = re.findall(r"[\u0600-\u06FFA-Za-z0-9]+", question)

    words = [
        word.strip("\u061f\u060c\u061b:,.!?")
        for word in words
    ]

    return [
        word
        for word in words
        if len(word) > 1
        and word not in ARABIC_STOPWORDS
        and word not in INTENT_WORDS
    ]


def search_fts(question: str, top_k: int = 30):
    terms = extract_terms(question)

    if not terms:
        return []

    near_terms = " ".join(f'"{term}"' for term in terms)
    near_query = f"NEAR({near_terms}, 25)"

    strict_query = " AND ".join(f'"{term}"' for term in terms)
    broad_query = " OR ".join(f'"{term}"' for term in terms)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    def run(query, limit):
        return connection.execute(
            """
            SELECT
                rowid,
                source,
                page,
                text,
                snippet(knowledge_fts, 0, '[', ']', '...', 64) AS snippet,
                bm25(knowledge_fts) AS bm25_score
            FROM knowledge_fts
            WHERE knowledge_fts MATCH ?
            ORDER BY bm25(knowledge_fts)
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()

    rows = []
    seen = set()

    for query in (near_query, strict_query, broad_query):
        try:
            found = run(query, top_k * 2)
        except sqlite3.OperationalError:
            continue

        for row in found:
            if row["rowid"] in seen:
                continue

            rows.append(row)
            seen.add(row["rowid"])

            if len(rows) >= top_k:
                break

        if len(rows) >= top_k:
            break

    connection.close()

    return [
        {
            "rowid": row["rowid"],
            "source": row["source"],
            "page": row["page"],
            "text": row["text"],
            "snippet": row["snippet"],
            "bm25_score": float(row["bm25_score"]),
        }
        for row in rows[:top_k]
    ]
