"""Rank candidate passages and choose the evidence for the language model.

This replaces the old "semantic" reranker, which in fact only counted
shared words inside isolated sentences. Here whole passages are scored
on several signals that matter for seerah questions:

- coverage: how many required words the passage contains, counting
  the section heading (a page in the middle of «غزوة بدر الكبرى» counts
  as being about Badr even if that page never repeats the word);
- proximity and phrase: the question's words close together, or in
  the same order («عام الحزن», «بيعة العقبة»);
- soft words and the current station, as tie-breakers;
- penalties for very short passages and table-of-contents pages.

The chosen evidence is diverse (at most two passages per book, no
near-duplicates) and fits a character budget set by the model.
"""

import re

from .arabic_text import forms_match, normalize, strip_prefix, token_forms, tokenize
from .fts_retriever import ANSWER_SIGNALS, CURATED_SOURCES, QueryPlan, TermGroup, neighbours


CURATED_BONUS = 0.08
MIN_SCORE = 0.30
SHORT_PASSAGE_CHARS = 450
MAX_EXPANDED_CHARS = 1500

_DIGIT_RE = re.compile(r"\d")


def _book_key(passage: dict) -> str:
    source = passage.get("source") or ""
    return source.rsplit("/", 1)[0] if "/" in source else source


def _positions(forms: list[tuple[str, ...]], group: TermGroup) -> list[int]:
    return [
        index for index, token in enumerate(forms)
        if any(forms_match(token, alternative) for alternative in group.alternatives)
    ]


def _matches(forms: list[tuple[str, ...]], group: TermGroup) -> bool:
    return any(
        forms_match(token, alternative)
        for token in forms
        for alternative in group.alternatives
    )


def _min_span(position_lists: list[list[int]]) -> int | None:
    """Smallest token window that contains one position from every list."""
    if not position_lists or any(not positions for positions in position_lists):
        return None

    events = sorted(
        (position, which)
        for which, positions in enumerate(position_lists)
        for position in positions
    )
    need = len(position_lists)
    counts: dict[int, int] = {}
    best = None
    left = 0

    for right in range(len(events)):
        counts[events[right][1]] = counts.get(events[right][1], 0) + 1
        while len(counts) == need:
            span = events[right][0] - events[left][0]
            best = span if best is None else min(best, span)
            which = events[left][1]
            counts[which] -= 1
            if counts[which] == 0:
                del counts[which]
            left += 1

    return best


_DOT_LEADER_RE = re.compile(r"(?:\.\s*){6,}")

# Well-known names shared by several events. Unless the question says
# otherwise, «غزوة بدر» means the great battle, not the later «بدر
# الصغرى» (the appointment of Badr) or «بدر الأولى» (Safwan).
AMBIGUOUS_NAMES = {
    normalize("بدر"): {
        "prefer": {normalize(w) for w in ("الكبرى", "العظمى", "القتال")},
        "avoid": {normalize(w) for w in (
            "الصغرى", "الأولى", "الموعد", "الآخرة", "الثالثة", "الثانية", "سفوان",
        )},
    },
}

# Nouns that start entries in lists of expeditions.
_EVENT_NOUNS = {normalize(w) for w in ("غزوة", "غزاة", "سرية", "غزوات", "سرايا")}


def _looks_like_contents_page(passage: dict) -> bool:
    text = passage["text"]
    if "فهرس" in (passage.get("heading") or ""):
        return True
    if len(_DOT_LEADER_RE.findall(text)) >= 3:
        return True
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 6:
        return False
    short = sum(1 for line in lines if len(line) < 45)
    with_digits = sum(1 for line in lines if _DIGIT_RE.search(line))
    return short / len(lines) > 0.7 and with_digits / len(lines) > 0.4


def _name_adjustment(plan: QueryPlan, passage: dict) -> float:
    """Multiplier for passages about a namesake of the asked event."""
    question_words = set(plan.sequence) | {group.word for group in plan.station}
    factor = 1.0

    for name, rules in AMBIGUOUS_NAMES.items():
        if name not in question_words or question_words & (rules["prefer"] | rules["avoid"]):
            continue
        words = [forms[0] for forms in map(token_forms, tokenize(
            (passage.get("heading") or "") + " " + passage["text"][:400]
        ))]
        following = {words[i + 1] for i, word in enumerate(words[:-1]) if strip_prefix(word) == name}
        if following & rules["avoid"] and not following & rules["prefer"]:
            factor *= 0.7
        elif following & rules["prefer"]:
            factor *= 1.05

    return factor


def score_passage(plan: QueryPlan, passage: dict, prior: float) -> dict:
    core = plan.required
    extra = list(plan.soft) + ([] if plan.station_required else list(plan.station))

    body = [token_forms(token) for token in tokenize(passage["text"])]
    heading = [token_forms(token) for token in tokenize(passage.get("heading") or "")]
    title = [token_forms(token) for token in tokenize(passage.get("title") or "")]

    body_positions = [_positions(body, group) for group in core]
    in_body = [bool(positions) for positions in body_positions]
    in_heading = [_matches(heading, group) for group in core]
    in_title = [_matches(title, group) for group in core]
    anywhere = [b or h or t for b, h, t in zip(in_body, in_heading, in_title)]

    n = max(len(core), 1)
    coverage = sum(anywhere) / n
    body_coverage = sum(in_body) / n
    heading_coverage = sum(in_heading) / n
    title_coverage = sum(in_title) / n

    extra_coverage = (
        sum(1 for group in extra if _matches(body, group) or _matches(heading, group)) / len(extra)
        if extra else 0.0
    )

    matched_lists = [positions for positions in body_positions if positions]
    if len(matched_lists) >= 2:
        span = _min_span(matched_lists)
        proximity = 1.0 if span <= 8 else 0.75 if span <= 20 else 0.45 if span <= 50 else 0.2
    elif matched_lists:
        proximity = 0.6
    else:
        proximity = 0.0

    # Question words appearing in the same order, side by side.
    flat = [forms[0] for forms in body]
    pairs = list(zip(plan.sequence, plan.sequence[1:]))
    phrase_hits = 0
    for first, second in pairs:
        first_group, second_group = TermGroup(first, [first]), TermGroup(second, [second])
        first_at = set(_positions(body, first_group))
        if first_at and any(index - 1 in first_at for index in _positions(body, second_group)):
            phrase_hits += 1
    phrase = phrase_hits / len(pairs) if pairs else 0.0

    occurrences = sum(len(positions) for positions in body_positions)
    density = min(1.0, occurrences / 6)

    # Brief questions («متى»، «كم»، «أين»): does the passage contain the
    # kind of answer asked for, close to the subject?
    answer = 0.0
    if plan.answer_type:
        signal = ANSWER_SIGNALS[plan.answer_type]
        digits_count = plan.answer_type != "where"
        hits = [
            index for index, forms in enumerate(body)
            if any(form in signal for form in forms) or (digits_count and forms[0].isdigit())
        ]
        if hits:
            anchors = [position for positions in body_positions for position in positions]
            near = any(abs(hit - anchor) <= 25 for hit in hits for anchor in anchors)
            answer = 1.0 if near else 0.4

    # With a single required word, everything in its chapter matches it;
    # the remaining words decide.
    extra_weight = 0.14 if len(core) <= 1 else 0.08

    score = (
        0.30 * coverage
        + 0.10 * body_coverage
        + 0.14 * heading_coverage
        + 0.04 * title_coverage
        + extra_weight * extra_coverage
        + 0.12 * proximity
        + 0.06 * phrase
        + 0.04 * density
        + 0.04 * prior
        + 0.15 * answer
    )

    if passage.get("source") in CURATED_SOURCES:
        score += CURATED_BONUS

    chars = len(passage["text"])
    if chars < 300:
        score *= 0.6 + 0.4 * chars / 300
    if _looks_like_contents_page(passage):
        score *= 0.4

    # A list of expeditions that mentions the subject only in passing.
    event_mentions = sum(1 for forms in body if forms[0] in _EVENT_NOUNS)
    if (occurrences <= 1 and event_mentions >= 4) or (
        event_mentions >= 8 and event_mentions >= 2 * occurrences
    ):
        score *= 0.75

    score *= _name_adjustment(plan, passage)

    return {
        **passage,
        "score": round(score, 4),
        "coverage": coverage,
        "body_or_heading": any(b or h for b, h in zip(in_body, in_heading)),
        "_tokens": set(flat),
    }


def rank_passages(plan: QueryPlan, candidates: list[dict]) -> list[dict]:
    total = max(len(candidates), 1)
    scored = [
        score_passage(plan, passage, prior=1 - index / total)
        for index, passage in enumerate(candidates)
    ]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored


def has_enough_evidence(plan: QueryPlan, ranked: list[dict]) -> bool:
    if not ranked:
        return False
    best = ranked[0]
    needed = 1.0 if len(plan.required) == 1 else 0.5
    return best["score"] >= MIN_SCORE and best["coverage"] >= needed and best["body_or_heading"]


def _too_similar(tokens: set[str], chosen: list[dict]) -> bool:
    for item in chosen:
        other = item["_tokens"]
        if tokens and other and len(tokens & other) / len(tokens | other) > 0.7:
            return True
    return False


def select_evidence(ranked: list[dict], max_items: int, char_budget: int, per_book: int = 2) -> list[dict]:
    chosen: list[dict] = []
    per_book_count: dict[str, int] = {}
    used_chars = 0

    for item in ranked:
        if len(chosen) >= max_items:
            break
        if item["score"] < MIN_SCORE * 0.8 and chosen:
            break

        book = _book_key(item)
        if per_book_count.get(book, 0) >= per_book:
            continue
        if _too_similar(item["_tokens"], chosen):
            continue
        if chosen and used_chars + len(item["text"]) > char_budget:
            continue

        chosen.append(item)
        per_book_count[book] = per_book_count.get(book, 0) + 1
        used_chars += len(item["text"])

    return chosen


def expand_short_passages(evidence: list[dict], char_budget: int, db_path=None) -> list[dict]:
    """Give short passages their neighbouring text from the same page.

    A 200-character passage is often the first lines of a section whose
    story continues in the next passage; the model needs both.
    """
    total = sum(len(item["text"]) for item in evidence)
    expanded = []

    for item in evidence:
        if len(item["text"]) >= SHORT_PASSAGE_CHARS:
            expanded.append(item)
            continue

        try:
            around = neighbours(item["id"], db_path=db_path)
        except Exception:
            expanded.append(item)
            continue

        text = item["text"]
        for neighbour_id, before in ((item["id"] + 1, False), (item["id"] - 1, True)):
            other = around.get(neighbour_id)
            if not other or other["source"] != item["source"] or other["page"] != item["page"]:
                continue
            if len(text) + len(other["text"]) > MAX_EXPANDED_CHARS:
                continue
            if total + len(other["text"]) > char_budget:
                continue
            text = f"{other['text']}\n{text}" if before else f"{text}\n{other['text']}"
            total += len(other["text"])

        expanded.append({**item, "text": text})

    return expanded


def public_view(item: dict) -> dict:
    """Drop internal scoring fields before returning a passage."""
    return {key: value for key, value in item.items() if not key.startswith("_")}
