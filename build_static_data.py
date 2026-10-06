"""Build the static `details` HTML for each journey event.

Reads the 52 events from the journey-events text file, pulls a verbatim
passage for each one from the local copy of Sirat Ibn Hisham under
backend/knowledge/sources, and writes the result into the `details` field
of every event in frontend/data.js.

Passages are copied from the book text as-is (never generated). Events the
book does not cover get the summary only, with no quote block.

Usage:
    python build_static_data.py [--events PATH] [--report PATH] [--dry-run]
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_JS = ROOT / "frontend" / "data.js"
BOOK_DIR = ROOT / "backend" / "knowledge" / "sources" / "سيرة ابن هشام - ت السقا ورفاقه"
BOOK_LABEL = "سيرة ابن هشام، ت السقا ورفاقه"
EVENT_FILE_NAMES = ("journey-events_3.txt", "journey-events.txt")

ZWNJ = "\u200c"
DIACRITICS = re.compile("[\u064b-\u0652\u0670\u0640]")
PAGE_HEADER = re.compile(r"^سيرة ابن هشام - .* - جـ \d+$")
PAGE_NUMBER = re.compile(r"^\(ص: (\d+)\)$")
FOOTNOTE_START = re.compile(rf"^{ZWNJ}?\[\d+\]")
INLINE_NOTE = re.compile(r"\s*\[\d+\]")

MIN_CHARS = 320
MAX_CHARS = 620
MAX_BODY_LINES = 400
MAX_HEMISTICH = 90

# Event number -> where its passage lives in the book.
#   heading: text of the chapter heading (diacritics ignored); a leading "="
#            means the heading must match exactly, otherwise "contains".
#   anchor:  optional phrase; the passage starts at the sentence containing it.
#   vol:     optional volume (1 or 2) to disambiguate repeated headings.
# Events with no entry are outside the scope of the book and get no quote.
PASSAGES: dict[int, dict] = {
    1: {"heading": "أمر الفيل، وقصة النسأة"},
    2: {"heading": "ولادة رسول الله صلى الله عليه وسلم ورضاعته"},
    3: {"heading": "حديث الملكين اللذين شقا بطنه"},
    4: {"heading": "=وفاة آمنة", "anchor": "بالأبواء"},
    5: {"heading": "كفالة أبي طالب لرسول الله"},
    6: {"heading": "نزول أبي طالب ورسول الله صلى الله عليه وسلم ببحيرى"},
    7: {"heading": "=حلف الفضول"},
    8: {"heading": "خروجه صلى الله عليه وسلم إلى الشام في تجارة خديجة"},
    9: {"heading": "زواجه صلى الله عليه وسلم من خديجة", "anchor": "وأصدقها"},
    10: {"heading": "إشارة أبي أمية بتحكيم أول داخل"},
    11: {"heading": "ابتداء نزول جبريل", "anchor": "يجاور"},
    12: {"heading": "ابتداء نزول جبريل", "anchor": "اقرأ"},
    13: {"heading": "خديجة بين يدي ورقة"},
    14: {"heading": "فترة الوحي ونزول سورة الضحى"},
    15: {"heading": "ذكر من أسلم من الصحابة بدعوة أبي بكر"},
    16: {"heading": "إسلام حمزة"},
    17: {"heading": "أمر الله له صلى الله عليه وسلم بمباداة قومه"},
    18: {"heading": "وفد قريش مع أبي طالب في شأن الرسول", "anchor": "يا أبا طالب"},
    19: {"heading": "ما كان يلقاه بلال بعد إسلامه"},
    20: {"heading": "ذكر الهجرة الأولى إلى أرض الحبشة"},
    21: {"heading": "إحضار النجاشي للمهاجرين"},
    22: {"heading": "=إسلام عمر بن الخطاب رضي الله عنه"},
    23: {"heading": "أرسلت قريش النضر وابن أبي معيط إلى أحبار يهود"},
    24: {"heading": "قصة إسلام الطفيل بن عمرو الدوسي"},
    25: {"heading": "=خبر الصحيفة"},
    26: {"heading": "=وفاة أبي طالب وخديجة"},
    27: {"heading": "سعي الرسول إلى ثقيف يطلب النصرة"},
    28: {"heading": "أمر الجن الذين استمعوا له وآمنوا به"},
    29: {"heading": "عرض رسول الله صلى الله عليه وسلم نفسه على القبائل"},
    30: {"heading": "=ذكر الإسراء والمعراج"},
    31: {"heading": "=العقبة الأولى ومصعب بن عمير"},
    32: {"heading": "عهد الرسول عليه الصلاة والسلام على الأنصار"},
    33: {"heading": "خروج النبي صلى الله عليه وسلم واستخلافه عليا على فراشه"},
    34: {"heading": "بناء مسجد المدينة ومساكنه"},
    35: {"heading": "=صرف القبلة إلى الكعبة"},
    36: {"heading": "=غزوة بدر الكبرى"},
    37: {"heading": "=غزوة أحد", "vol": 2, "anchor": "لما أصيب يوم بدر"},
    38: {"heading": "غزوة الخندق", "vol": 2, "anchor": "نفرا من اليهود"},
    39: {"heading": "أمر الحديبية في آخر سنة ست"},
    40: {"heading": "=خروج رسول الله إلى الملوك"},
    41: {"heading": "ذكر المسير إلى خيبر في المحرم سنة سبع"},
    42: {"heading": "بعث الرسول إلى مؤتة واختياره الأمراء"},
    43: {"heading": "ذكر الأسباب الموجبة المسير إلى مكة"},
    44: {"heading": "غزوة حنين في سنة ثمان بعد الفتح"},
    45: {"heading": "أمر الرسول الناس بالتهيؤ لتبوك"},
    46: {"heading": "ذكر سنة تسع وتسميتها سنة الوفود"},
    47: {"heading": "خطبة الرسول في حجة الوداع"},
    48: {"heading": "=ابتداء شكوى رسول الله صلى الله عليه وسلم"},
}


def normalize(text: str) -> str:
    """Fold Arabic text for matching: no diacritics, unified letter forms."""
    text = DIACRITICS.sub("", text.replace(ZWNJ, ""))
    text = re.sub("[أإآٱ]", "ا", text).replace("ى", "ي").replace("ة", "ه")
    text = re.sub(r"\[\d+\]", "", text)
    return re.sub(r"\s+", " ", text).strip(" :()")


# --------------------------------------------------------------------------
# Events file
# --------------------------------------------------------------------------

def find_events_file(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            sys.exit(f"Events file not found: {path}")
        return path
    for folder in (ROOT, ROOT / "docs", Path.home() / "Downloads"):
        for name in EVENT_FILE_NAMES:
            if (folder / name).is_file():
                return folder / name
    sys.exit("No journey-events file found; pass one with --events PATH")


def parse_events(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    starts = [i for i, line in enumerate(lines) if re.match(r"^\d+\) ", line)]
    events = []
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        block = lines[start:end]
        num, title = re.match(r"^(\d+)\) (.+)$", block[0]).groups()
        event = {"num": int(num), "title": title.strip()}
        for line in block[1:]:
            if line.startswith("المكان:"):
                for part in line.split(" | "):
                    key, _, value = part.partition(":")
                    field = {"المكان": "location", "التاريخ": "date", "التصنيف": "category"}.get(key.strip())
                    if field:
                        event[field] = value.strip()
            elif line.startswith("الملخص:"):
                event["summary"] = line.partition(":")[2].strip()
        missing = [k for k in ("location", "date", "category", "summary") if not event.get(k)]
        if missing:
            sys.exit(f"Event {num} in {path.name} is missing: {', '.join(missing)}")
        events.append(event)
    return events


# --------------------------------------------------------------------------
# Book
# --------------------------------------------------------------------------

def load_book() -> list[dict]:
    """Return the book as a flat list of items: headings and body lines."""
    if not BOOK_DIR.is_dir():
        sys.exit(f"Book folder not found: {BOOK_DIR}")
    items = []
    for vol in (1, 2):
        page = None
        in_notes = False
        for raw in (BOOK_DIR / f"{vol:03d}.txt").read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if PAGE_HEADER.match(line):
                in_notes = False
                continue
            number = PAGE_NUMBER.match(line)
            if number:
                page = int(number.group(1))
                continue
            if page is None or FOOTNOTE_START.match(raw):
                in_notes = in_notes or page is not None
                continue
            if in_notes:
                continue
            if raw.startswith(ZWNJ):
                text = raw.replace(ZWNJ, "").strip()
                if text:
                    items.append({"kind": "heading", "vol": vol, "page": page, "text": text, "norm": normalize(text)})
            elif line:
                items.append({"kind": "body", "vol": vol, "page": page, "text": line})
    return items


def find_heading(items: list[dict], spec: dict) -> int | None:
    wanted = spec["heading"]
    exact = wanted.startswith("=")
    wanted = normalize(wanted.lstrip("="))
    for index, item in enumerate(items):
        if item["kind"] != "heading" or ("vol" in spec and item["vol"] != spec["vol"]):
            continue
        if item["norm"] == wanted if exact else wanted in item["norm"]:
            return index
    return None


def is_main_heading(item: dict) -> bool:
    return item["kind"] == "heading" and not item["text"].startswith("(")


def extract_passage(items: list[dict], spec: dict) -> dict | None:
    start = find_heading(items, spec)
    if start is None:
        return None

    # Body lines of this chapter, up to the next chapter heading.
    body = []
    for item in items[start + 1:]:
        if is_main_heading(item) and body:
            break
        if item["kind"] == "body":
            body.append(item)
        if len(body) >= MAX_BODY_LINES:
            break

    # Verse is printed as hemistich / "…" / hemistich; prose runs stop there.
    verse = set()
    for index, item in enumerate(body):
        if item["text"] == "…":
            verse.add(index)
            for neighbor in (index - 1, index + 1):
                if 0 <= neighbor < len(body) and len(body[neighbor]["text"]) < MAX_HEMISTICH:
                    verse.add(neighbor)

    # Split each prose run into sentences. Sentences may span lines and pages.
    runs, current = [], []
    for index, item in enumerate(body + [None]):
        if item is None or index in verse:
            if current:
                runs.append(current)
            current = []
            continue
        text = INLINE_NOTE.sub("", item["text"])
        parts = [p for p in re.split(r"(?<=[.؟!])\s+", text) if p.strip()]
        for position, part in enumerate(parts):
            continues = position == 0 and current and not re.search(r"[.؟!:]$", current[-1][0])
            if continues:
                current[-1] = (f"{current[-1][0]} {part.strip()}", current[-1][1])
            else:
                current.append((part.strip(), item["page"]))

    anchor = normalize(spec["anchor"]) if spec.get("anchor") else None
    for run in runs:
        first = next((i for i, (s, _) in enumerate(run) if not anchor or anchor in normalize(s)), None)
        if first is not None:
            break
    else:
        return None

    chosen = []
    for sentence, _ in run[first:]:
        chosen.append(sentence)
        if len(" ".join(chosen)) >= MIN_CHARS:
            break
    text = " ".join(chosen)
    if len(text) > MAX_CHARS:  # cut at a word boundary and mark the omission
        text = text[:MAX_CHARS].rsplit(" ", 1)[0].rstrip("،؛:,-( ") + " …"
    elif text.endswith(":"):  # dangling lead-in to verse or a list: drop it
        complete = re.match(r"^(.*[.؟!])\s", text, re.S)
        if complete and len(complete.group(1)) >= 0.6 * len(text):
            text = complete.group(1)
        else:
            text = text.rsplit("،", 1)[0] + " …"

    heading = items[start]
    return {
        "text": text,
        "vol": heading["vol"],
        "page": run[first][1],
        "heading": DIACRITICS.sub("", heading["text"]).strip(" :"),
    }


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def build_details(summary: str, passage: dict | None) -> str:
    details = f'<p class="summary-text">{html.escape(summary, quote=False)}</p>'
    if passage is None:
        return details
    source = f"المصدر: {BOOK_LABEL}، جـ{passage['vol']} ص{passage['page']} — المكتبة الشاملة"
    return (
        f"{details}\n"
        "<br>\n"
        "<p><strong>مقتطف من المصادر (سيرة ابن هشام):</strong></p>\n"
        '<blockquote style="border-right: 3px solid var(--gold); padding-right: 15px; background: #fdfaf3; '
        'padding-top: 10px; padding-bottom: 10px; border-radius: 8px; line-height: 1.8;">\n'
        f"  {html.escape(passage['text'], quote=False)}\n"
        f'  <br><br><small style="color: var(--muted);">{source}</small>\n'
        "</blockquote>"
    )


def js_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    return f"'{escaped}'"


def update_data_js(details_by_num: dict[int, str]) -> tuple[str, int]:
    """Set the `details` field on each event line of data.js, keeping the rest."""
    with DATA_JS.open(encoding="utf-8", newline="") as handle:  # keep line endings
        source = handle.read()
    newline = "\r\n" if "\r\n" in source else "\n"
    updated = 0
    out = []
    for line in source.splitlines():
        match = re.search(r"\bnum:\s*(\d+)\b", line)
        if match and int(match.group(1)) in details_by_num and re.search(r"\}\s*,?\s*$", line):
            line = re.sub(r",\s*details:\s*'(?:[^'\\]|\\.)*'", "", line)
            tail = re.search(r"\s*\}\s*,?\s*$", line)
            value = js_string(details_by_num[int(match.group(1))])
            line = f"{line[:tail.start()]}, details: {value}{tail.group(0)}"
            updated += 1
        out.append(line)
    return newline.join(out) + newline, updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--events", help="path to the journey-events text file")
    parser.add_argument("--report", help="write a per-event report of the passages to this file")
    parser.add_argument("--dry-run", action="store_true", help="do not modify frontend/data.js")
    args = parser.parse_args()

    events_path = find_events_file(args.events)
    events = parse_events(events_path)
    items = load_book()

    details_by_num, report = {}, []
    for event in events:
        spec = PASSAGES.get(event["num"])
        passage = extract_passage(items, spec) if spec else None
        details_by_num[event["num"]] = build_details(event["summary"], passage)
        if passage:
            status = f"جـ{passage['vol']} ص{passage['page']} | {passage['heading']}"
        else:
            status = "NOT FOUND" if spec else "no passage (outside the book)"
        report.append(f"{event['num']:>2}) {event['title']}\n    {status}\n    {passage['text'] if passage else ''}\n")

    content, updated = update_data_js(details_by_num)
    if not args.dry_run:
        DATA_JS.write_text(content, encoding="utf-8", newline="")
    if args.report:
        Path(args.report).write_text("\n".join(report), encoding="utf-8")

    quoted = sum("<blockquote" in d for d in details_by_num.values())
    not_found = [n for n in PASSAGES if "<blockquote" not in details_by_num.get(n, "")]
    print(f"events file : {events_path}")
    print(f"events      : {len(events)} parsed, {updated} updated in {DATA_JS.relative_to(ROOT)}"
          f"{' (dry run, not written)' if args.dry_run else ''}")
    print(f"passages    : {quoted} with a quote, {len(events) - quoted} summary only")
    if not_found:
        print(f"not found   : events {', '.join(map(str, sorted(not_found)))}")


if __name__ == "__main__":
    main()
