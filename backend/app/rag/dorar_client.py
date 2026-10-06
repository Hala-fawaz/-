import html
import json
import re
import urllib.parse
import urllib.request


DORAR_API_URL = "https://dorar.net/dorar_api.json"

LABEL_NARRATOR = "\u0627\u0644\u0631\u0627\u0648\u064a"
LABEL_SCHOLAR = "\u0627\u0644\u0645\u062d\u062f\u062b"
LABEL_SOURCE = "\u0627\u0644\u0645\u0635\u062f\u0631"
LABEL_PAGE = "\u0627\u0644\u0635\u0641\u062d\u0629 \u0623\u0648 \u0627\u0644\u0631\u0642\u0645"
LABEL_GRADE = "\u062e\u0644\u0627\u0635\u0629 \u062d\u0643\u0645 \u0627\u0644\u0645\u062d\u062f\u062b"

DORAR_SOURCE_NAME = (
    "\u0627\u0644\u062f\u0631\u0631 \u0627\u0644\u0633\u0646\u064a\u0629"
    " - "
    "\u0627\u0644\u0645\u0648\u0633\u0648\u0639\u0629 "
    "\u0627\u0644\u062d\u062f\u064a\u062b\u064a\u0629"
)


def _strip_html(value: str) -> str:
    value = value or ""

    value = re.sub(
        r"<br\s*/?>",
        "\n",
        value,
        flags=re.I,
    )

    value = re.sub(
        r"<[^>]+>",
        " ",
        value,
    )

    value = html.unescape(value)

    value = re.sub(
        r"[ \t]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s*\n\s*",
        "\n",
        value,
    )

    return value.strip()


def _normalize_label(value: str) -> str:
    value = _strip_html(value)

    value = value.strip(
        " \t\r\n:?"
    )

    return value


def _extract_info_fields(info_html: str) -> dict:
    pattern = re.compile(
        r'<span[^>]*class=["\']info-subtitle["\'][^>]*>'
        r'(.*?)'
        r'</span>',
        flags=re.I | re.S,
    )

    matches = list(
        pattern.finditer(info_html)
    )

    fields = {}

    for index, match in enumerate(matches):
        label = _normalize_label(
            match.group(1)
        )

        value_start = match.end()

        if index + 1 < len(matches):
            value_end = matches[index + 1].start()
        else:
            value_end = len(info_html)

        raw_value = info_html[
            value_start:value_end
        ]

        value = _strip_html(
            raw_value
        )

        if label:
            fields[label] = value

    return fields


def search_dorar(
    query: str,
    max_results: int = 5,
) -> list[dict]:
    query = (query or "").strip()

    if not query:
        return []

    url = (
        DORAR_API_URL
        + "?"
        + urllib.parse.urlencode({
            "skey": query
        })
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Risalah/1.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=20,
    ) as response:
        data = json.loads(
            response.read().decode("utf-8")
        )

    ahadith = data.get("ahadith", {})

    if not isinstance(ahadith, dict):
        return []

    result_html = ahadith.get(
        "result",
        "",
    )

    if not result_html:
        return []

    result_pattern = re.compile(
        r'<div[^>]*class=["\']hadith["\'][^>]*>'
        r'(.*?)'
        r'</div>\s*'
        r'<div[^>]*class=["\']hadith-info["\'][^>]*>'
        r'(.*?)'
        r'</div>',
        flags=re.I | re.S,
    )

    results = []

    for hadith_html, info_html in result_pattern.findall(
        result_html
    ):
        hadith_text = _strip_html(
            hadith_html
        )

        hadith_text = re.sub(
            r"^\s*\d+\s*-\s*",
            "",
            hadith_text,
        ).strip()

        if not hadith_text:
            continue

        fields = _extract_info_fields(
            info_html
        )

        narrator = fields.get(
            LABEL_NARRATOR,
            "",
        )

        scholar = fields.get(
            LABEL_SCHOLAR,
            "",
        )

        source_name = fields.get(
            LABEL_SOURCE,
            "",
        )

        page_number = fields.get(
            LABEL_PAGE,
            "",
        )

        grade = fields.get(
            LABEL_GRADE,
            "",
        )

        snippet_parts = [
            hadith_text
        ]

        if narrator:
            snippet_parts.append(
                f"{LABEL_NARRATOR}: {narrator}"
            )

        if scholar:
            snippet_parts.append(
                f"{LABEL_SCHOLAR}: {scholar}"
            )

        if source_name:
            snippet_parts.append(
                f"{LABEL_SOURCE}: {source_name}"
            )

        if page_number:
            snippet_parts.append(
                f"{LABEL_PAGE}: {page_number}"
            )

        if grade:
            snippet_parts.append(
                f"{LABEL_GRADE}: {grade}"
            )

        full_source = DORAR_SOURCE_NAME

        if source_name:
            full_source += (
                " - " + source_name
            )

        results.append({
            "snippet": " | ".join(
                snippet_parts
            ),
            "text": hadith_text,
            "source": full_source,
            "page": page_number or None,
            "narrator": narrator,
            "scholar": scholar,
            "grade": grade,
            "url": url,
            "source_type": "dorar",
        })

        if len(results) >= max_results:
            break

    return results


def format_dorar_answer(
    results: list[dict],
    max_items: int = 4,
    include_text: bool = True,
) -> str:
    if not results:
        return ""

    first_text = (
        results[0].get("text")
        or ""
    ).strip()

    first_text = first_text.rstrip(
        " .\u2026"
    )

    statements = []
    seen = set()

    for item in results[:max_items]:
        narrator = (
            item.get("narrator")
            or ""
        ).strip()

        scholar = (
            item.get("scholar")
            or ""
        ).strip()

        grade = (
            item.get("grade")
            or ""
        ).strip()

        if not grade:
            continue

        key = (
            narrator,
            scholar,
            grade,
        )

        if key in seen:
            continue

        seen.add(key)

        parts = []

        if narrator:
            parts.append(
                "\u0639\u0646 "
                + narrator
            )

        if scholar:
            parts.append(
                "\u062d\u0643\u0645 "
                + scholar
            )

        parts.append(
            grade
        )

        statements.append(
            "\u060c ".join(parts)
        )

    if not statements:
        return first_text or ""

    prefix = (
        "\u0648\u0631\u062f\u062a \u0641\u064a "
        "\u0646\u062a\u0627\u0626\u062c "
        "\u0627\u0644\u062f\u0631\u0631 "
        "\u0627\u0644\u0633\u0646\u064a\u0629 "
        "\u0623\u062d\u0643\u0627\u0645 "
        "\u0628\u062d\u0633\u0628 "
        "\u0627\u0644\u0631\u0648\u0627\u064a\u0629 "
        "\u0648\u0627\u0644\u0625\u0633\u0646\u0627\u062f: "
    )

    details = "\u061b ".join(
        statements
    )

    if include_text and first_text:
        return (
            first_text
            + ". "
            + prefix
            + details
            + "."
        )

    return prefix + details + "."
