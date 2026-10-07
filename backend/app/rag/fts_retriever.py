"""Turn a question into a search plan and fetch candidate passages.

Words in a question play different roles:
- stop words and question words («ما»، «ماذا»، «متى»، «وش») are dropped;
- the question's own verb («حدث»، «حصل»، «جرى»، «صار»، «فعل») is dropped
  too: the old retriever required «حدث» to appear in the answer text,
  so it returned sentences that merely contained «حدث في غزوة بدر»;
- "soft" words («النبي»، «غزوة»، «يوم»، «عدد»...) help ranking but are
  not required, because a narration of Badr may never say «غزوة»;
- every other word is "hard": each candidate passage must contain all
  hard words (in its text or in its section heading).

The station the visitor is reading (when the page sends it) adds its
own words: required when the question points at it («ما الأماكن
المهمة في المحطة؟»), otherwise used only to break ties.
"""

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from .arabic_text import normalize, strip_prefix, term_alternatives, tokenize


BACKEND_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BACKEND_DIR / "knowledge" / "index" / "knowledge_fts.db"

# bm25 weights for the two indexed columns: (heading, body).
HEADING_WEIGHT = 3.0
BODY_WEIGHT = 1.0

# Small, hand-written sources that are always considered (and get a
# ranking bonus): the team's station summaries from knowledge-base.
CURATED_SOURCES = ("journey-events.txt",)


class KnowledgeIndexNotReady(RuntimeError):
    """The search index is missing, outdated, or still being built."""


def _normalized_set(words: str) -> frozenset[str]:
    return frozenset(normalize(word) for word in words.split())


STOP_WORDS = _normalized_set("""
    ما ماذا مين متى متي اين أين وين فين كيف كيفية لماذا ليش ليه لم هل كم أي اي ايش إيش وش شو شنو
    في فى من الى إلى على عن مع عند لدى حتى منذ بين ثم او أو أن إن ان لن لا قد لقد كل بعض غير سوى
    إذا اذا لو كي لكي حيث بل لكن لأن لان أيضا ايضا جدا فقط
    هو هي هم هما هن انا أنا انت أنت نحن هذا هذه هذي ذلك تلك هؤلاء أولئك الذي التي الذين اللذين
    اللتين اللاتي هناك هنالك
    كان كانت كانوا يكون تكون يكونوا صار صارت صاروا أصبح اصبح يوجد توجد ليس ليست
    صلى عليه وسلم سلم رضي عنه عنها عنهم تعالى
""")

# The question's own verb or request wording: never a search word.
QUESTION_VERBS = _normalized_set("""
    حدث حدثت يحدث حصل حصلت يحصل جرى جرت يجري وقع وقعت يقع تم فعل فعلت يفعل صنع
    أهمية اهمية أهم اهم اشرح اشرحي وضح وضحي اذكر اذكري حدثني حدثيني أخبرني اخبرني احك احكي احكيلي
    قصة تفاصيل معلومات نبذة عرفني تكلم تحدث كلمني ابغى ابغي أريد اريد ممكن رجاء أعطني اعطني اعطيني
    بالتفصيل باختصار مختصر ملخص سؤال
""")

# Pointers to the page the visitor is on.
STATION_POINTERS = _normalized_set("محطة المحطة المحطات هنا")

# Words that help ranking but are too common (or too optional) to require.
SOFT_WORDS = _normalized_set("""
    النبي نبي الرسول رسول محمد المصطفى الله
    غزوة معركة وقعة حادثة يوم عام سنة شهر عدد اسم أسماء سبب أسباب نتيجة نتائج دروس عبر فوائد
    مكان موقع أماكن مهمة مهم دور موقف صفات صفة بداية بدء أول آخر نهاية مرحلة مراحل مرة مرات
    المسلمين المسلمون مسلمين الصحابة الصحابي أصحاب الناس
    بن ابن بنت أم أبو أبي أبا
""")

# Word families: a question word also searches its close relatives,
# e.g. «متى ولد» must find «مولده» and «ميلاده».
WORD_FAMILIES = {
    normalize(word): related
    for word, related in {
        "ولد": ["مولد*", "ميلاد*", "ولاد*"],
        "مولد": ["ولد", "ميلاد*"],
        "توفي": ["وفا*", "مات"],
        "وفاة": ["توفي", "مات"],
        "هاجر": ["هجر*"],
        "هجرة": ["هاجر*"],
        "أسلم": ["إسلام*"],
        "إسلام": ["أسلم*"],
        "تزوج": ["زواج*", "زوج*"],
        "زواج": ["تزوج*"],
        "بعث": ["مبعث*", "بعث*"],
        "بعثة": ["مبعث*", "بعث"],
        "نزل": ["نزول*", "أنزل*"],
        "قتل": ["مقتل*", "قتل*"],
        "استشهد": ["استشهاد*", "شهيد*"],
        "فتح": ["فتح*"],
        "حفر": ["حفر*"],
    }.items()
}

# Question words that ask for a particular kind of answer, and the
# words that signal such an answer in a passage.
ANSWER_TYPES = {
    "when": _normalized_set("متى متي"),
    "how_many": _normalized_set("كم"),
    "where": _normalized_set("أين اين وين فين"),
}

# Kunya words: the books write «أبو بكر»، «أبي بكر» or «أبا بكر».
KUNYA_FORMS = ("ابو", "ابي", "ابا")

NARRATIVE_MARKERS = _normalized_set("""
    حدث حصل جرى وقع صار فعل صنع قصة احك احكي احكيلي اشرح حدثني اخبرني أخبرني تفاصيل أحداث
    كيف أسباب نتائج دروس عبر
""")
BRIEF_MARKERS = _normalized_set("متى متي أين اين وين فين كم")


# Words that signal the kind of answer a brief question asks for.
ANSWER_SIGNALS = {
    "when": _normalized_set("""
        محرم صفر ربيع جمادى جمادي رجب شعبان رمضان شوال القعدة الحجة
        سنة السنة سنين عام العام هجري الهجرة للهجرة ميلادي يوم ليلة
        الاثنين الثلاثاء الأربعاء الخميس الجمعة السبت
    """),
    "how_many": _normalized_set("""
        اثنان اثنين ثلاث ثلاثة أربع أربعة خمس خمسة ست ستة سبع سبعة ثمان ثمانية تسع تسعة
        عشر عشرة عشرون عشرين ثلاثون ثلاثين أربعون أربعين خمسون خمسين ستون ستين
        سبعون سبعين ثمانون ثمانين تسعون تسعين مائة مئة مائتان مائتين ثلاثمائة ثلاثمئة
        أربعمائة خمسمائة ألف ألفا ألفين آلاف بضع بضعة نيف
    """),
    "where": _normalized_set("""
        مكان موضع موقع جبل وادي غار بئر قرية مدينة شعب دار بيت مسجد طريق ناحية قرب
        شمال جنوب شرق غرب ميل أميال
    """),
}


@dataclass
class TermGroup:
    word: str
    alternatives: list[str]

    def fts(self, column: str | None = None) -> str:
        """FTS5 expression matching any alternative (optionally in one column)."""
        prefix = f"{column} : " if column else ""
        parts = []
        for alternative in self.alternatives:
            if alternative.endswith("*"):
                parts.append(f'{prefix}"{alternative[:-1]}"*')
            else:
                parts.append(f'{prefix}"{alternative}"')
        return "(" + " OR ".join(parts) + ")"


@dataclass
class QueryPlan:
    question: str
    hard: list[TermGroup] = field(default_factory=list)
    soft: list[TermGroup] = field(default_factory=list)
    station: list[TermGroup] = field(default_factory=list)
    station_required: bool = False
    mode: str = "general"           # "narrative" | "brief" | "general"
    answer_type: str | None = None  # "when" | "how_many" | "where"
    sequence: list[str] = field(default_factory=list)  # content words in order

    @property
    def required(self) -> list[TermGroup]:
        groups = list(self.hard)
        if self.station_required:
            groups += self.station
        if not groups:
            groups = list(self.soft) or list(self.station)
        return groups

    @property
    def is_empty(self) -> bool:
        return not (self.hard or self.soft or self.station)


def _group(word: str) -> TermGroup:
    if word in KUNYA_FORMS:
        return TermGroup(word, list(KUNYA_FORMS))

    alternatives = term_alternatives(word)
    family = WORD_FAMILIES.get(word) or WORD_FAMILIES.get(strip_prefix(word)) or []
    for related in family:
        star = related.endswith("*")
        form = normalize(related.rstrip("*"))
        alternatives.append(form + ("*" if star else ""))

    return TermGroup(word, list(dict.fromkeys(alternatives)))


def _in(word: str, vocabulary: frozenset[str]) -> bool:
    """Is the word (or the word without «ال»/«و»...) in the vocabulary?"""
    return word in vocabulary or strip_prefix(word) in vocabulary


def _content_words(text: str) -> list[str]:
    words = []
    for token in tokenize(text):
        if len(token) < 2 or (token.isdigit() and len(token) < 3):
            continue
        if token in STOP_WORDS or _in(token, QUESTION_VERBS):
            continue
        words.append(token)
    return words


def plan_query(question: str, station: str | None = None) -> QueryPlan:
    plan = QueryPlan(question=question)
    tokens = tokenize(question)
    token_set = set(tokens)

    if any(_in(token, NARRATIVE_MARKERS) for token in tokens):
        plan.mode = "narrative"
    elif token_set & BRIEF_MARKERS or (tokens[:1] == ["من"] and len(tokens) <= 5):
        plan.mode = "brief"

    for kind, markers in ANSWER_TYPES.items():
        if token_set & markers:
            plan.answer_type = kind
            break

    points_at_station = any(_in(token, STATION_POINTERS) for token in tokens)

    for word in _content_words(question):
        if _in(word, STATION_POINTERS):
            continue
        plan.sequence.append(word)
        group = _group(word)
        if _in(word, SOFT_WORDS) or word in KUNYA_FORMS:
            plan.soft.append(group)
        else:
            plan.hard.append(group)

    if station:
        seen = {group.word for group in plan.hard + plan.soft}
        for word in _content_words(station):
            if word in seen or _in(word, STATION_POINTERS):
                continue
            seen.add(word)
            if _in(word, SOFT_WORDS) or word in KUNYA_FORMS:
                continue
            plan.station.append(_group(word))
        plan.station_required = bool(plan.station) and (points_at_station or not plan.hard)

    return plan


def answer_signal_group(answer_type: str) -> TermGroup:
    """FTS alternatives for "a passage containing this kind of answer"."""
    alternatives = sorted(ANSWER_SIGNALS[answer_type])
    if answer_type in ("when", "how_many"):
        alternatives += [f"{digit}*" for digit in "123456789"]
    return TermGroup(answer_type, alternatives)


def extract_terms(question: str) -> list[str]:
    """Content words of a question (kept for older callers)."""
    return plan_query(question).sequence


def _connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise KnowledgeIndexNotReady(f"Knowledge index not found: {db_path}")
    try:
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("SELECT 1 FROM passages LIMIT 1")
    except sqlite3.Error as error:
        raise KnowledgeIndexNotReady(
            f"Knowledge index at {db_path} is outdated or unreadable ({error}). "
            "Rebuild it with: python -m app.rag.fts_builder"
        ) from error
    return connection


def search_passages(plan: QueryPlan, limit: int = 200, db_path: Path | None = None) -> list[dict]:
    """Candidate passages for a plan (at most a few hundred).

    1. Every required group must match (AND), best bm25 first, plus
       the matches whose section heading names the subject, plus the
       curated station summaries.
    2. Brief questions also pull passages that contain the kind of
       answer asked for (a date, a number, a place), and questions with
       one or two required words pull passages that also contain the
       soft words or the station's words.
    3. If that is still thin, or there are three or more required
       words, passages matching any of them (OR) are added, marked as
       non-strict; the ranker decides whether they are good enough.
    """
    required = plan.required
    if not required:
        return []

    db_path = db_path or DB_PATH
    connection = _connect(db_path)
    rank = f"bm25(passages_fts, {HEADING_WEIGHT}, {BODY_WEIGHT})"
    sql = (
        f"SELECT rowid, {rank} AS score FROM passages_fts "
        f"WHERE passages_fts MATCH ? ORDER BY score LIMIT ?"
    )

    try:
        found: dict[int, tuple[float, bool]] = {}
        strict = " AND ".join(group.fts() for group in required)

        def run(query: str, is_strict: bool):
            for row in connection.execute(sql, (query, limit)):
                found.setdefault(row["rowid"], (row["score"], is_strict))

        run(strict, True)

        # Passages under a section heading that names the subject: the
        # chapter that narrates the event, not passing mentions.
        run(f"{strict} AND (" + " OR ".join(g.fts("heading") for g in required) + ")", True)

        # When one word is required (e.g. «بدر»), thousands of passages
        # match it; bm25 alone cannot tell which of them answer the
        # question. Pull in the passages that ALSO contain the kind of
        # answer asked for, or the question's other words.
        if plan.answer_type:
            run(f"{strict} AND {answer_signal_group(plan.answer_type).fts()}", True)
        optional = [g for g in plan.soft + plan.station if g not in required]
        if optional and len(required) <= 2:
            run(f"{strict} AND (" + " OR ".join(g.fts() for g in optional) + ")", True)

        # Also take passages that miss one of the words: with three or
        # more required words a good passage often lacks one of them.
        if len(found) < min(limit, 40) or len(required) >= 3:
            loose_groups = required + [g for g in plan.station + plan.hard if g not in required]
            run(" OR ".join(group.fts() for group in loose_groups), False)

        placeholders = ",".join("?" * len(CURATED_SOURCES))
        for row in connection.execute(
            f"SELECT id FROM passages WHERE source IN ({placeholders})", CURATED_SOURCES
        ):
            found.setdefault(row["id"], (0.0, True))

        if not found:
            return []

        ids = list(found)
        placeholders = ",".join("?" * len(ids))
        rows = connection.execute(
            f"SELECT id, source, title, page, heading, text FROM passages WHERE id IN ({placeholders})",
            ids,
        ).fetchall()
    finally:
        connection.close()

    candidates = []
    for row in rows:
        score, strict_match = found[row["id"]]
        candidates.append({
            "id": row["id"],
            "source": row["source"],
            "title": row["title"],
            "page": row["page"],
            "heading": row["heading"],
            "text": row["text"],
            "bm25": float(score),
            "strict": strict_match,
        })

    candidates.sort(key=lambda item: (not item["strict"], item["bm25"]))
    return candidates


def neighbours(passage_id: int, db_path: Path | None = None) -> dict[int, dict]:
    """The passages just before and after one passage (for more context)."""
    connection = _connect(db_path or DB_PATH)
    try:
        rows = connection.execute(
            "SELECT id, source, title, page, heading, text FROM passages WHERE id IN (?, ?)",
            (passage_id - 1, passage_id + 1),
        ).fetchall()
    finally:
        connection.close()
    return {row["id"]: dict(row) for row in rows}


def search_fts(question: str, top_k: int = 30):
    """Older interface: plain candidate list in the previous shape."""
    plan = plan_query(question)
    return [
        {
            "rowid": item["id"],
            "source": item["title"],
            "page": item["page"],
            "text": item["text"],
            "snippet": item["text"],
            "bm25_score": item["bm25"],
        }
        for item in search_passages(plan, limit=top_k)
    ][:top_k]
