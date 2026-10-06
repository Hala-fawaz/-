import json
import re
import urllib.parse
import urllib.request


BASE_URL = "https://hadeethenc.com/api/v1"

SOURCE_NAME = (
    "\u0645\u0648\u0633\u0648\u0639\u0629 "
    "\u0627\u0644\u0623\u062d\u0627\u062f\u064a\u062b "
    "\u0627\u0644\u0646\u0628\u0648\u064a\u0629 - HadeethEnc"
)

_ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]"
)


def _normalize(text: str) -> str:
    text = (text or "").strip().lower()

    text = _ARABIC_DIACRITICS.sub(
        "",
        text,
    )

    replacements = {
        "\u0623": "\u0627",
        "\u0625": "\u0627",
        "\u0622": "\u0627",
        "\u0649": "\u064a",
        "\u0624": "\u0648",
        "\u0626": "\u064a",
        "\u0629": "\u0647",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(
        r"[^\w\u0600-\u06ff]+",
        " ",
        text,
    )

    return " ".join(
        text.split()
    )


def _score_result(
    query: str,
    item: dict,
) -> float:
    q = _normalize(query)

    title = _normalize(
        item.get("title", "")
    )

    text = _normalize(
        item.get("hadith_text", "")
    )

    if not q:
        return 0.0

    q_terms = {
        term
        for term in q.split()
        if len(term) > 1
    }

    if not q_terms:
        return 0.0

    combined = title + " " + text

    matched = sum(
        1
        for term in q_terms
        if term in combined
    )

    score = matched / len(q_terms)

    if q in title:
        score += 2.0
    elif q in text:
        score += 1.5

    title_terms = set(
        title.split()
    )

    if title_terms:
        overlap = len(
            q_terms & title_terms
        ) / len(q_terms)

        score += overlap

    return score


def _get_json(
    url: str,
    timeout: int = 15,
):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Risalah/1.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout,
    ) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


def _get_details(
    hadeeth_id: str,
    language: str = "ar",
) -> dict:
    url = (
        BASE_URL
        + "/hadeeths/one/?"
        + urllib.parse.urlencode({
            "language": language,
            "id": hadeeth_id,
        })
    )

    data = _get_json(url)

    if not isinstance(data, dict):
        return {}

    return data


def search_hadeethenc(
    query: str,
    max_results: int = 3,
    language: str = "ar",
) -> list[dict]:
    query = (query or "").strip()

    if not query:
        return []

    search_url = (
        BASE_URL
        + "/hadeeths/search/?"
        + urllib.parse.urlencode({
            "phrase": query,
            "language": language,
        })
    )

    search_data = _get_json(
        search_url
    )

    if not isinstance(
        search_data,
        list,
    ):
        return []

    ranked = sorted(
        search_data,
        key=lambda item: _score_result(
            query,
            item,
        ),
        reverse=True,
    )

    results = []
    seen_titles = set()

    best_score = (
        _score_result(query, ranked[0])
        if ranked
        else 0.0
    )

    minimum_score = max(
        1.0,
        best_score * 0.55,
    )

    for item in ranked:
        item_score = _score_result(
            query,
            item,
        )

        if item_score < minimum_score:
            continue

        canonical_title = _normalize(
            item.get("title")
            or item.get("hadith_text")
            or ""
        )

        if canonical_title in seen_titles:
            continue

        if canonical_title:
            seen_titles.add(
                canonical_title
            )

        hadeeth_id = str(
            item.get("id", "")
        ).strip()

        if not hadeeth_id:
            continue

        try:
            details = _get_details(
                hadeeth_id,
                language=language,
            )
        except Exception:
            details = item

        hadeeth_text = (
            details.get("hadeeth")
            or item.get("hadith_text")
            or ""
        ).strip()

        title = (
            details.get("title")
            or item.get("title")
            or ""
        ).strip()

        grade = (
            details.get("grade")
            or ""
        ).strip()

        attribution = (
            details.get("attribution")
            or ""
        ).strip()

        explanation = (
            details.get("explanation")
            or ""
        ).strip()

        reference = (
            details.get("reference")
            or ""
        ).strip()

        if not hadeeth_text:
            continue

        snippet_parts = [
            hadeeth_text
        ]

        if grade:
            snippet_parts.append(
                "\u0627\u0644\u062f\u0631\u062c\u0629: "
                + grade
            )

        if attribution:
            snippet_parts.append(
                "\u0627\u0644\u0646\u0633\u0628\u0629: "
                + attribution
            )

        if reference:
            snippet_parts.append(
                "\u0627\u0644\u0645\u0631\u0627\u062c\u0639: "
                + reference
            )

        details_url = (
            BASE_URL
            + "/hadeeths/one/?"
            + urllib.parse.urlencode({
                "language": language,
                "id": hadeeth_id,
            })
        )

        results.append({
            "id": hadeeth_id,
            "title": title,
            "text": hadeeth_text,
            "snippet": " | ".join(
                snippet_parts
            ),
            "grade": grade,
            "attribution": attribution,
            "explanation": explanation,
            "reference": reference,
            "source": SOURCE_NAME,
            "page": (
                "\u062d\u062f\u064a\u062b "
                "\u0631\u0642\u0645 "
                + hadeeth_id
            ),
            "url": details_url,
            "source_type": "hadeethenc",
            "match_score": item_score,
        })

        if len(results) >= max_results:
            break

    return results
