import re
import sqlite3
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BACKEND_DIR / "knowledge" / "index" / "knowledge_fts.db"

ARABIC_STOPWORDS = {
    "\u0645\u0627",
    "\u0645\u0627\u0630\u0627",
    "\u0645\u0646",
    "\u0641\u064a",
    "\u0639\u0644\u0649",
    "\u0639\u0646",
    "\u0627\u0644\u0649",
    "\u0647\u0644",
    "\u0643\u064a\u0641",
    "\u0645\u062a\u0649",
    "\u0627\u064a\u0646",
    "\u0644\u0645\u0627\u0630\u0627",
    "\u0647\u0648",
    "\u0647\u064a",
    "\u0643\u0627\u0646",
    "\u0643\u0627\u0646\u062a",
    "\u0647\u0630\u0627",
    "\u0647\u0630\u0647",
    "\u0630\u0644\u0643",
    "\u0627\u0644\u062a\u064a",
    "\u0627\u0644\u0630\u064a",
}


INTENT_WORDS = {
    "أهمية", "اهمية", "أهم", "اهم",
    "اشرح", "وضح", "اذكر",
    "حدثني", "أخبرني", "اخبرني",
}


def _normalize_arabic_word(word: str) -> str:
    word = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", word or "")

    replacements = {
        "\u0623": "\u0627",
        "\u0625": "\u0627",
        "\u0622": "\u0627",
        "\u0649": "\u064a",
        "\u0624": "\u0648",
        "\u0626": "\u064a",
    }

    for source, target in replacements.items():
        word = word.replace(source, target)

    return word


def extract_terms(question: str):
    words = re.findall(r"[\u0600-\u06FFA-Za-z0-9]+", question)

    words = [
        word.strip("\u061f\u060c\u061b:,.!?")
        for word in words
    ]

    normalized_stopwords = {
        _normalize_arabic_word(word)
        for word in ARABIC_STOPWORDS
    }

    normalized_intent_words = {
        _normalize_arabic_word(word)
        for word in INTENT_WORDS
    }

    return [
        word
        for word in words
        if len(word) > 1
        and _normalize_arabic_word(word) not in normalized_stopwords
        and _normalize_arabic_word(word) not in normalized_intent_words
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
