"""Turn knowledge source files into clean, searchable passages.

Two layouts are supported:

1. Shamela book exports (almost every file in knowledge/sources):
   a book card, then pages that each start with a running title line
   followed by a "(ص: N)" marker. Headings are lines that start with
   the invisible character U+200C, and footnotes sit at the bottom of
   each page.

2. Structured files without page markers, such as journey-events.txt
   from the knowledge-base branch: numbered stations ("12) title"
   followed by a dashed line), grouped under "=====" era banners.
   Any other file without page markers falls back to plain paragraphs.

Each passage keeps the page it came from and the section heading it
sits under (e.g. «غزوة بدر الكبرى › النذير في مكة»), because most
pages in the middle of a chapter never repeat the chapter's name.
"""

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .arabic_text import normalize


ZWNJ = "\N{ZERO WIDTH NON-JOINER}"
BREADCRUMB_SEPARATOR = " \N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK} "

PAGE_MARKER_RE = re.compile(r"^\s*\(ص:\s*(\d+)\s*\)\s*$")       # (ص: 12)
FOOTNOTE_LINE_RE = re.compile(r"^[\(\[]\s*(\d{1,3})\s*[\)\]]")    # "(1) ..." / "[1] ..."
INLINE_REF_RE = re.compile(r"[«\[\(]\s*(\d{1,3})\s*[»\]\)]")       # «1»  [1]  (1)
FOOTNOTE_MARK_RE = re.compile(r"«\s*\d{1,3}\s*»|\[\s*\d{1,3}\s*\]")
UNDERSCORE_RULE_RE = re.compile(r"^_{5,}\s*$")
NUMBER_ONLY_RE = re.compile(r"^[\(\[]?\s*[\d٠-٩]+\s*[\)\]\-\.:]?\s*$")
INVISIBLE_RE = re.compile(r"[\U0000200B-\U0000200F\U0000FEFF]")
SENTENCE_END_RE = re.compile(r"(?<=[.!?؟])\s+")

STATION_RE = re.compile(r"^\s*(\d{1,3})\)\s+(.+?)\s*$")
DASH_RULE_RE = re.compile(r"^\s*-{5,}\s*$")
EQUALS_RULE_RE = re.compile(r"^\s*={5,}\s*$")

# A heading that starts with one of these words opens a chapter-level
# section (an expedition, a battle, the hijra, a pledge, a year...).
# Sub-headings under it keep it in their breadcrumb.
MAJOR_HEADING_WORDS = tuple(normalize(word) for word in (
    "غزوة", "غزاة", "سرية", "سرايا", "بعث", "فتح", "حجة", "عمرة", "هجرة",
    "بيعة", "وفاة", "صلح", "وقعة", "الإسراء", "المعراج", "مولد",
    "حصار", "وفود", "الوفود", "عام",
))

TARGET_CHARS = 900
MAX_CHARS = 1400
MIN_CHARS = 25


@dataclass
class Passage:
    source: str        # path relative to knowledge/sources, with "/" separators
    title: str         # human-friendly book (and volume) name
    page: str | None   # printed page number, when the source has pages
    heading: str       # section breadcrumb, may be empty
    text: str          # cleaned text for display and for the language model


def display_title(relative_path: str) -> str:
    """«سيرة ابن هشام - ت السقا ورفاقه/001.txt» -> «سيرة ابن هشام - ت السقا ورفاقه - ج1»."""
    path = Path(relative_path)
    stem = path.stem

    if len(path.parts) > 1:
        book = path.parts[-2]
        if stem.isdigit():
            return f"{book} - ج{int(stem)}"
        return f"{book} - {stem}"

    return stem


def _clean_line(line: str) -> str:
    line = INVISIBLE_RE.sub("", line)
    line = FOOTNOTE_MARK_RE.sub("", line)
    return re.sub(r"[ \t]+", " ", line).strip()


def _is_heading_text(text: str) -> bool:
    if not text or NUMBER_ONLY_RE.match(text) or len(text) > 120:
        return False
    return len(text.split()) >= 2 or len(text) >= 6


def _is_major(heading: str) -> bool:
    words = normalize(heading).split()
    return any(
        word == marker or word.startswith(marker)
        for word in words[:3]
        for marker in MAJOR_HEADING_WORDS
    )


class _Sections:
    """Tracks the heading breadcrumb while walking through a book."""

    def __init__(self):
        self.major = ""
        self.minor = ""

    def push(self, heading: str):
        if _is_major(heading):
            self.major, self.minor = heading, ""
        else:
            self.minor = heading

    def breadcrumb(self) -> str:
        parts = [part for part in (self.major, self.minor) if part]
        return BREADCRUMB_SEPARATOR.join(dict.fromkeys(parts))


def _split_long(text: str) -> list[str]:
    """Split one long paragraph at sentence ends, about MAX_CHARS each."""
    if len(text) <= MAX_CHARS:
        return [text]

    pieces, current = [], ""

    for sentence in SENTENCE_END_RE.split(text):
        if current and len(current) + len(sentence) + 1 > MAX_CHARS:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()

        while len(current) > MAX_CHARS * 1.5:
            cut = current.rfind(" ", 0, MAX_CHARS)
            cut = cut if cut > 0 else MAX_CHARS
            pieces.append(current[:cut])
            current = current[cut:].strip()

    if current:
        pieces.append(current)

    return pieces


class _PassageBuffer:
    """Groups consecutive paragraphs into passages of a useful size.

    flush() marks a hard boundary (a new heading or the end of a page):
    nothing is merged across it. Between boundaries, paragraphs are
    packed into passages of about TARGET_CHARS, and a short leftover
    tail is glued to the passage before it instead of standing alone.
    """

    TAIL_CHARS = 250

    def __init__(self, emit):
        self.emit = emit
        self.lines: list[str] = []
        self.size = 0
        self.ready: list[str] = []

    def add(self, line: str):
        for piece in _split_long(line):
            if self.lines and self.size + len(piece) > MAX_CHARS:
                self._close()
            self.lines.append(piece)
            self.size += len(piece) + 1
            if self.size >= TARGET_CHARS:
                self._close()

    def _close(self):
        text = "\n".join(self.lines).strip()
        self.lines, self.size = [], 0
        if text:
            self.ready.append(text)

    def flush(self):
        self._close()

        if (
            len(self.ready) >= 2
            and len(self.ready[-1]) < self.TAIL_CHARS
            and len(self.ready[-2]) + len(self.ready[-1]) <= MAX_CHARS + self.TAIL_CHARS
        ):
            tail = self.ready.pop()
            self.ready[-1] = f"{self.ready[-1]}\n{tail}"

        for text in self.ready:
            if len(text) >= MIN_CHARS:
                self.emit(text)

        self.ready = []


def _strip_footnotes(lines: list[str]) -> list[str]:
    """Drop the footnote block at the bottom of a Shamela page.

    The block starts at the first line that opens with the smallest
    footnote number referenced in the text above it, e.g. a page whose
    text contains «1» and «2» loses everything from the line "(1) ...".
    """
    for index, line in enumerate(lines):
        if UNDERSCORE_RULE_RE.match(line):
            return lines[:index]

    body_refs: set[int] = set()

    for index, line in enumerate(lines):
        stripped = INVISIBLE_RE.sub("", line).strip()
        note = FOOTNOTE_LINE_RE.match(stripped)

        if note:
            if index > 0 and body_refs and int(note.group(1)) == min(body_refs):
                return lines[:index]
            continue

        body_refs.update(int(n) for n in INLINE_REF_RE.findall(stripped))

    return lines


def _running_titles(lines: list[str]) -> set[str]:
    """Lines printed right above the page markers (the book's running title)."""
    counts = Counter()

    for index in range(1, len(lines)):
        if PAGE_MARKER_RE.match(lines[index]):
            previous = lines[index - 1].strip()
            if previous and len(previous) <= 150:
                counts[previous] += 1

    pages = sum(1 for line in lines if PAGE_MARKER_RE.match(line))
    return {title for title, n in counts.items() if n >= max(2, pages * 0.2)}


def parse_shamela(text: str, relative_path: str) -> list[Passage]:
    lines = text.splitlines()
    running = _running_titles(lines)
    title = display_title(relative_path)
    sections = _Sections()
    passages: list[Passage] = []

    # Split into (page number, lines). The book card before the first
    # marker (title, author, publisher) is skipped.
    pages: list[tuple[str, list[str]]] = []
    current_page, current_lines = None, []

    for line in lines:
        marker = PAGE_MARKER_RE.match(line)
        if marker:
            if current_page is not None:
                pages.append((current_page, current_lines))
            current_page, current_lines = marker.group(1), []
        elif current_page is not None:
            current_lines.append(line)

    if current_page is not None:
        pages.append((current_page, current_lines))

    for page, page_lines in pages:
        # The running title of the NEXT page sits at the end of this one.
        while page_lines and (not page_lines[-1].strip() or page_lines[-1].strip() in running):
            page_lines = page_lines[:-1]

        page_lines = _strip_footnotes(page_lines)

        def emit(passage_text: str, page: str = page):
            passages.append(Passage(
                source=relative_path,
                title=title,
                page=page,
                heading=sections.breadcrumb(),
                text=passage_text,
            ))

        buffer = _PassageBuffer(emit)

        for raw in page_lines:
            is_marked = raw.startswith(ZWNJ)
            line = _clean_line(raw)

            if not line:
                continue

            if is_marked and _is_heading_text(line):
                buffer.flush()
                sections.push(line)
                continue

            buffer.add(line)

        buffer.flush()

    return passages


def parse_structured(text: str, relative_path: str) -> list[Passage]:
    """Files without page markers: stations if present, else paragraphs."""
    lines = [_clean_line(line) for line in text.splitlines()]
    file_title = next((line for line in lines if line), Path(relative_path).stem)
    short_title = file_title.split(":")[0].strip() or file_title
    passages: list[Passage] = []

    station_starts = [
        index for index in range(len(lines) - 1)
        if STATION_RE.match(lines[index]) and DASH_RULE_RE.match(lines[index + 1])
    ]

    if not station_starts:
        buffer = _PassageBuffer(lambda t: passages.append(Passage(
            source=relative_path, title=file_title, page=None, heading="", text=t,
        )))
        for line in lines[1:]:
            if line and not EQUALS_RULE_RE.match(line) and not DASH_RULE_RE.match(line):
                buffer.add(line)
        buffer.flush()
        return passages

    # Era banners: the line right after a "=====" rule, e.g.
    # «العهد المدني (1 – 11 هـ) — 15 محطة».
    era_banners = {
        index + 1: lines[index + 1]
        for index in range(len(lines) - 1)
        if EQUALS_RULE_RE.match(lines[index])
        and lines[index + 1]
        and not EQUALS_RULE_RE.match(lines[index + 1])
        and not STATION_RE.match(lines[index + 1])
    }
    bounds = station_starts + [len(lines)]

    for position, start in enumerate(station_starts):
        era = ""
        for banner_index, banner in era_banners.items():
            if banner_index < start:
                era = banner
        era_name = era.split("(")[0].strip()

        number, name = STATION_RE.match(lines[start]).groups()
        end = bounds[position + 1]

        # A station ends at the next station or at the next era banner.
        for index in range(start + 2, end):
            if EQUALS_RULE_RE.match(lines[index]):
                end = index
                break

        body = [line for line in lines[start + 2:end] if line and not DASH_RULE_RE.match(line)]
        heading = f"المحطة {number}: {name}"
        title = f"{short_title} \N{EM DASH} {heading}"
        breadcrumb = BREADCRUMB_SEPARATOR.join(part for part in (era_name, heading) if part)

        def emit(passage_text: str, title: str = title, breadcrumb: str = breadcrumb):
            passages.append(Passage(
                source=relative_path, title=title, page=None,
                heading=breadcrumb, text=passage_text,
            ))

        buffer = _PassageBuffer(emit)
        buffer.add(name)
        for line in body:
            buffer.add(line)
        buffer.flush()

    return passages


def parse_file(path: Path, sources_dir: Path) -> list[Passage]:
    relative_path = path.relative_to(sources_dir).as_posix()
    text = path.read_text(encoding="utf-8-sig", errors="replace")

    if any(PAGE_MARKER_RE.match(line) for line in text.splitlines()[:400]):
        return parse_shamela(text, relative_path)

    return parse_structured(text, relative_path)
