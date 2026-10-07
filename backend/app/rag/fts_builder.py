"""Build the full-text search index used by the guide (/api/guide).

Run from the backend folder:

    python -m app.rag.fts_builder

It reads every .txt file under knowledge/sources, splits it into
passages (see source_parser.py), normalizes the Arabic text (see
arabic_text.py) and writes knowledge/index/knowledge_fts.db.

Layout of the database (index version 2):
- passages      : one row per passage with the display text, book
                  title, page and section heading.
- passages_fts  : SQLite FTS5 index over the normalized heading and
                  body. It stores no text of its own (content=''); a
                  match returns a rowid that points into passages.
- meta          : index version and build statistics.

The new database is written to a temporary file and only renamed over
the old one when the build succeeds, so a failed build never leaves
the server without an index.
"""

import hashlib
import os
import sqlite3
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .arabic_text import index_text
from .source_parser import parse_file


BACKEND_DIR = Path(__file__).resolve().parents[2]
SOURCES_DIR = BACKEND_DIR / "knowledge" / "sources"
INDEX_DIR = BACKEND_DIR / "knowledge" / "index"
DB_PATH = INDEX_DIR / "knowledge_fts.db"

INDEX_VERSION = "2"
LOCK_STALE_SECONDS = 15 * 60

SCHEMA = """
CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE passages (
    id      INTEGER PRIMARY KEY,
    source  TEXT NOT NULL,
    title   TEXT NOT NULL,
    page    TEXT,
    heading TEXT NOT NULL,
    text    TEXT NOT NULL
);
CREATE VIRTUAL TABLE passages_fts USING fts5(
    heading,
    body,
    content = '',
    tokenize = 'unicode61 remove_diacritics 0'
);
"""


def _source_files(sources_dir: Path) -> tuple[list[Path], list[str]]:
    """All .txt sources, skipping exact duplicates (e.g. a "copy" folder)."""
    files = sorted(
        sources_dir.rglob("*.txt"),
        key=lambda p: ("copy" in p.relative_to(sources_dir).as_posix().lower(), p.as_posix()),
    )
    seen, unique, skipped = set(), [], []

    for path in files:
        digest = hashlib.sha1(path.read_bytes()).hexdigest()
        if digest in seen:
            skipped.append(path.relative_to(sources_dir).as_posix())
            continue
        seen.add(digest)
        unique.append(path)

    return unique, skipped


def _prepare_file(job: tuple[Path, Path]) -> list[tuple]:
    """Parse one file and normalize its passages (runs in a worker process)."""
    path, sources_dir = job
    return [
        (
            passage.source, passage.title, passage.page, passage.heading, passage.text,
            index_text(passage.heading), index_text(passage.text),
        )
        for passage in parse_file(path, sources_dir)
    ]


def build_fts_index(
    sources_dir: Path | None = None,
    db_path: Path | None = None,
    verbose: bool = True,
    workers: int = 1,
) -> dict:
    sources_dir = Path(sources_dir or SOURCES_DIR)
    db_path = Path(db_path or DB_PATH)
    started = time.time()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = db_path.with_name(f"{db_path.name}.building-{os.getpid()}")

    if tmp_path.exists():
        tmp_path.unlink()

    files, skipped = _source_files(sources_dir)
    connection = sqlite3.connect(tmp_path)
    jobs = [(path, sources_dir) for path in files]
    executor = ProcessPoolExecutor(max_workers=workers) if workers > 1 else None

    try:
        connection.executescript(SCHEMA)
        passage_id = 0
        files_done = 0
        prepared = executor.map(_prepare_file, jobs, chunksize=4) if executor else map(_prepare_file, jobs)

        for file_rows in prepared:
            rows, fts_rows = [], []

            for source, title, page, heading, text, heading_index, body_index in file_rows:
                passage_id += 1
                rows.append((passage_id, source, title, page, heading, text))
                fts_rows.append((passage_id, heading_index, body_index))

            connection.executemany(
                "INSERT INTO passages(id, source, title, page, heading, text) VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )
            connection.executemany(
                "INSERT INTO passages_fts(rowid, heading, body) VALUES (?, ?, ?)",
                fts_rows,
            )

            files_done += 1
            if verbose and files_done % 25 == 0:
                connection.commit()
                print(f"Indexed files: {files_done}/{len(files)} | passages: {passage_id}")

        connection.execute("INSERT INTO passages_fts(passages_fts) VALUES ('optimize')")

        stats = {
            "version": INDEX_VERSION,
            "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "files": str(files_done),
            "passages": str(passage_id),
            "skipped_duplicates": ",".join(skipped),
        }
        connection.executemany("INSERT INTO meta(key, value) VALUES (?, ?)", stats.items())
        connection.commit()
    except BaseException:
        connection.close()
        tmp_path.unlink(missing_ok=True)
        raise
    finally:
        if executor:
            executor.shutdown()

    connection.close()
    os.replace(tmp_path, db_path)

    stats["seconds"] = f"{time.time() - started:.0f}"

    if verbose:
        print(f"Files indexed: {stats['files']} (skipped duplicates: {len(skipped)})")
        print(f"Passages indexed: {stats['passages']}")
        print(f"Built in {stats['seconds']}s -> {db_path}")

    return stats


def index_version(db_path: Path | None = None) -> str | None:
    """Version of the index on disk, or None when it is missing/old."""
    db_path = Path(db_path or DB_PATH)
    if not db_path.exists():
        return None
    try:
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            row = connection.execute("SELECT value FROM meta WHERE key = 'version'").fetchone()
        finally:
            connection.close()
    except sqlite3.Error:
        return None
    return row[0] if row else None


def index_is_ready(db_path: Path | None = None) -> bool:
    return index_version(db_path) == INDEX_VERSION


_build_thread: threading.Thread | None = None


def ensure_index_async(db_path: Path | None = None) -> bool:
    """Start building the index in the background if it is missing or old.

    Returns True when the index is already usable. Only one process
    builds at a time (a lock file next to the database); the others
    simply wait for the finished file to appear.
    """
    global _build_thread

    db_path = Path(db_path or DB_PATH)
    if index_is_ready(db_path):
        return True

    if _build_thread is not None and _build_thread.is_alive():
        return False

    lock_path = db_path.with_name(".build.lock")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if lock_path.exists() and time.time() - lock_path.stat().st_mtime > LOCK_STALE_SECONDS:
        lock_path.unlink(missing_ok=True)

    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(descriptor)
    except FileExistsError:
        return False

    def run():
        try:
            build_fts_index(db_path=db_path, verbose=False)
            print(f"[rag] knowledge index ready: {db_path}", file=sys.stderr)
        except Exception as error:  # keep the server alive; report the reason
            print(f"[rag] knowledge index build failed: {error!r}", file=sys.stderr)
        finally:
            lock_path.unlink(missing_ok=True)

    _build_thread = threading.Thread(target=run, name="rag-index-build", daemon=True)
    _build_thread.start()
    print("[rag] building the knowledge index in the background...", file=sys.stderr)
    return False


if __name__ == "__main__":
    build_fts_index(workers=min(os.cpu_count() or 1, 8))
