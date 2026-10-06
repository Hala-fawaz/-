import json
import re
import urllib.parse
import urllib.request


BASE_URL = "https://quranenc.com/api/v1"

TAFSIR_KEY = "arabic_mokhtasar"
WORDS_KEY = "arabic_seraj"

QURANENC_SOURCE = (
    "\u0645\u0648\u0633\u0648\u0639\u0629 "
    "\u0627\u0644\u0642\u0631\u0622\u0646 "
    "\u0627\u0644\u0643\u0631\u064a\u0645 - QuranEnc"
)

SURA_NAMES = {
    "\u0627\u0644\u0641\u0627\u062a\u062d\u0629": 1,
    "\u0627\u0644\u0628\u0642\u0631\u0629": 2,
    "\u0622\u0644 \u0639\u0645\u0631\u0627\u0646": 3,
    "\u0627\u0644\u0646\u0633\u0627\u0621": 4,
    "\u0627\u0644\u0645\u0627\u0626\u062f\u0629": 5,
    "\u0627\u0644\u0623\u0646\u0639\u0627\u0645": 6,
    "\u0627\u0644\u0623\u0639\u0631\u0627\u0641": 7,
    "\u0627\u0644\u0623\u0646\u0641\u0627\u0644": 8,
    "\u0627\u0644\u062a\u0648\u0628\u0629": 9,
    "\u064a\u0648\u0646\u0633": 10,
    "\u0647\u0648\u062f": 11,
    "\u064a\u0648\u0633\u0641": 12,
    "\u0627\u0644\u0631\u0639\u062f": 13,
    "\u0625\u0628\u0631\u0627\u0647\u064a\u0645": 14,
    "\u0627\u0644\u062d\u062c\u0631": 15,
    "\u0627\u0644\u0646\u062d\u0644": 16,
    "\u0627\u0644\u0625\u0633\u0631\u0627\u0621": 17,
    "\u0627\u0644\u0643\u0647\u0641": 18,
    "\u0645\u0631\u064a\u0645": 19,
    "\u0637\u0647": 20,
    "\u0627\u0644\u0623\u0646\u0628\u064a\u0627\u0621": 21,
    "\u0627\u0644\u062d\u062c": 22,
    "\u0627\u0644\u0645\u0624\u0645\u0646\u0648\u0646": 23,
    "\u0627\u0644\u0646\u0648\u0631": 24,
    "\u0627\u0644\u0641\u0631\u0642\u0627\u0646": 25,
    "\u0627\u0644\u0634\u0639\u0631\u0627\u0621": 26,
    "\u0627\u0644\u0646\u0645\u0644": 27,
    "\u0627\u0644\u0642\u0635\u0635": 28,
    "\u0627\u0644\u0639\u0646\u0643\u0628\u0648\u062a": 29,
    "\u0627\u0644\u0631\u0648\u0645": 30,
    "\u0644\u0642\u0645\u0627\u0646": 31,
    "\u0627\u0644\u0633\u062c\u062f\u0629": 32,
    "\u0627\u0644\u0623\u062d\u0632\u0627\u0628": 33,
    "\u0633\u0628\u0623": 34,
    "\u0641\u0627\u0637\u0631": 35,
    "\u064a\u0633": 36,
    "\u0627\u0644\u0635\u0627\u0641\u0627\u062a": 37,
    "\u0635": 38,
    "\u0627\u0644\u0632\u0645\u0631": 39,
    "\u063a\u0627\u0641\u0631": 40,
    "\u0641\u0635\u0644\u062a": 41,
    "\u0627\u0644\u0634\u0648\u0631\u0649": 42,
    "\u0627\u0644\u0632\u062e\u0631\u0641": 43,
    "\u0627\u0644\u062f\u062e\u0627\u0646": 44,
    "\u0627\u0644\u062c\u0627\u062b\u064a\u0629": 45,
    "\u0627\u0644\u0623\u062d\u0642\u0627\u0641": 46,
    "\u0645\u062d\u0645\u062f": 47,
    "\u0627\u0644\u0641\u062a\u062d": 48,
    "\u0627\u0644\u062d\u062c\u0631\u0627\u062a": 49,
    "\u0642": 50,
    "\u0627\u0644\u0630\u0627\u0631\u064a\u0627\u062a": 51,
    "\u0627\u0644\u0637\u0648\u0631": 52,
    "\u0627\u0644\u0646\u062c\u0645": 53,
    "\u0627\u0644\u0642\u0645\u0631": 54,
    "\u0627\u0644\u0631\u062d\u0645\u0646": 55,
    "\u0627\u0644\u0648\u0627\u0642\u0639\u0629": 56,
    "\u0627\u0644\u062d\u062f\u064a\u062f": 57,
    "\u0627\u0644\u0645\u062c\u0627\u062f\u0644\u0629": 58,
    "\u0627\u0644\u062d\u0634\u0631": 59,
    "\u0627\u0644\u0645\u0645\u062a\u062d\u0646\u0629": 60,
    "\u0627\u0644\u0635\u0641": 61,
    "\u0627\u0644\u062c\u0645\u0639\u0629": 62,
    "\u0627\u0644\u0645\u0646\u0627\u0641\u0642\u0648\u0646": 63,
    "\u0627\u0644\u062a\u063a\u0627\u0628\u0646": 64,
    "\u0627\u0644\u0637\u0644\u0627\u0642": 65,
    "\u0627\u0644\u062a\u062d\u0631\u064a\u0645": 66,
    "\u0627\u0644\u0645\u0644\u0643": 67,
    "\u0627\u0644\u0642\u0644\u0645": 68,
    "\u0627\u0644\u062d\u0627\u0642\u0629": 69,
    "\u0627\u0644\u0645\u0639\u0627\u0631\u062c": 70,
    "\u0646\u0648\u062d": 71,
    "\u0627\u0644\u062c\u0646": 72,
    "\u0627\u0644\u0645\u0632\u0645\u0644": 73,
    "\u0627\u0644\u0645\u062f\u062b\u0631": 74,
    "\u0627\u0644\u0642\u064a\u0627\u0645\u0629": 75,
    "\u0627\u0644\u0625\u0646\u0633\u0627\u0646": 76,
    "\u0627\u0644\u0645\u0631\u0633\u0644\u0627\u062a": 77,
    "\u0627\u0644\u0646\u0628\u0623": 78,
    "\u0627\u0644\u0646\u0627\u0632\u0639\u0627\u062a": 79,
    "\u0639\u0628\u0633": 80,
    "\u0627\u0644\u062a\u0643\u0648\u064a\u0631": 81,
    "\u0627\u0644\u0627\u0646\u0641\u0637\u0627\u0631": 82,
    "\u0627\u0644\u0645\u0637\u0641\u0641\u064a\u0646": 83,
    "\u0627\u0644\u0627\u0646\u0634\u0642\u0627\u0642": 84,
    "\u0627\u0644\u0628\u0631\u0648\u062c": 85,
    "\u0627\u0644\u0637\u0627\u0631\u0642": 86,
    "\u0627\u0644\u0623\u0639\u0644\u0649": 87,
    "\u0627\u0644\u063a\u0627\u0634\u064a\u0629": 88,
    "\u0627\u0644\u0641\u062c\u0631": 89,
    "\u0627\u0644\u0628\u0644\u062f": 90,
    "\u0627\u0644\u0634\u0645\u0633": 91,
    "\u0627\u0644\u0644\u064a\u0644": 92,
    "\u0627\u0644\u0636\u062d\u0649": 93,
    "\u0627\u0644\u0634\u0631\u062d": 94,
    "\u0627\u0644\u062a\u064a\u0646": 95,
    "\u0627\u0644\u0639\u0644\u0642": 96,
    "\u0627\u0644\u0642\u062f\u0631": 97,
    "\u0627\u0644\u0628\u064a\u0646\u0629": 98,
    "\u0627\u0644\u0632\u0644\u0632\u0644\u0629": 99,
    "\u0627\u0644\u0639\u0627\u062f\u064a\u0627\u062a": 100,
    "\u0627\u0644\u0642\u0627\u0631\u0639\u0629": 101,
    "\u0627\u0644\u062a\u0643\u0627\u062b\u0631": 102,
    "\u0627\u0644\u0639\u0635\u0631": 103,
    "\u0627\u0644\u0647\u0645\u0632\u0629": 104,
    "\u0627\u0644\u0641\u064a\u0644": 105,
    "\u0642\u0631\u064a\u0634": 106,
    "\u0627\u0644\u0645\u0627\u0639\u0648\u0646": 107,
    "\u0627\u0644\u0643\u0648\u062b\u0631": 108,
    "\u0627\u0644\u0643\u0627\u0641\u0631\u0648\u0646": 109,
    "\u0627\u0644\u0646\u0635\u0631": 110,
    "\u0627\u0644\u0645\u0633\u062f": 111,
    "\u0627\u0644\u0625\u062e\u0644\u0627\u0635": 112,
    "\u0627\u0644\u0641\u0644\u0642": 113,
    "\u0627\u0644\u0646\u0627\u0633": 114,
}


def _get_json(url: str, timeout: int = 15):
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


def _arabic_number_to_int(value: str):
    table = str.maketrans(
        "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669",
        "0123456789",
    )

    value = (value or "").translate(table)

    try:
        return int(value)
    except ValueError:
        return None


def extract_quran_reference(
    question: str,
):
    text = " ".join(
        (question or "").split()
    )

    sura_number = None

    for name, number in sorted(
        SURA_NAMES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if name in text:
            sura_number = number
            break

    if sura_number is None:
        match = re.search(
            r"\u0633\u0648\u0631\u0629\s+(\d{1,3})",
            text,
        )

        if match:
            sura_number = _arabic_number_to_int(
                match.group(1)
            )

    aya_patterns = (
        r"(?:\u0627\u0644\u0622\u064a\u0629|\u0622\u064a\u0629)"
        r"\s*(?:\u0631\u0642\u0645\s*)?(\d{1,3})",
        r"(?:\u0627\u0644\u0622\u064a\u0629|\u0622\u064a\u0629)"
        r"\s*(?:\u0631\u0642\u0645\s*)?([\u0660-\u0669]{1,3})",
    )

    aya_number = None

    for pattern in aya_patterns:
        match = re.search(
            pattern,
            text,
        )

        if match:
            aya_number = _arabic_number_to_int(
                match.group(1)
            )
            break

    if (
        sura_number is None
        or aya_number is None
    ):
        return None

    if not 1 <= sura_number <= 114:
        return None

    if aya_number < 1:
        return None

    return sura_number, aya_number


def get_ayah(
    sura_number: int,
    aya_number: int,
    translation_key: str = TAFSIR_KEY,
) -> dict:
    url = (
        BASE_URL
        + "/translation/aya/"
        + urllib.parse.quote(translation_key)
        + f"/{sura_number}/{aya_number}"
    )

    data = _get_json(url)

    result = (
        data.get("result", {})
        if isinstance(data, dict)
        else {}
    )

    if not isinstance(result, dict):
        return {}

    if not result.get("arabic_text"):
        return {}

    return {
        "sura": int(result.get("sura", sura_number)),
        "aya": int(result.get("aya", aya_number)),
        "arabic_text": (
            result.get("arabic_text")
            or ""
        ).strip(),
        "translation": (
            result.get("translation")
            or ""
        ).strip(),
        "footnotes": result.get("footnotes"),
        "translation_key": translation_key,
        "source": QURANENC_SOURCE,
        "page": (
            "\u0633\u0648\u0631\u0629 "
            + str(sura_number)
            + " - "
            + "\u0627\u0644\u0622\u064a\u0629 "
            + str(aya_number)
        ),
        "url": (
            "https://quranenc.com/api/v1/translation/aya/"
            + urllib.parse.quote(translation_key)
            + f"/{sura_number}/{aya_number}"
        ),
        "source_type": "quranenc",
    }


def get_quran_evidence(
    question: str,
) -> list[dict]:
    reference = extract_quran_reference(
        question
    )

    if not reference:
        return []

    sura_number, aya_number = reference

    wants_words = any(
        marker in question
        for marker in (
            "\u0645\u0639\u0646\u0649 \u0643\u0644\u0645\u0629",
            "\u0645\u0639\u0646\u0649 \u0643\u0644\u0645\u0627\u062a",
            "\u0645\u0639\u0627\u0646\u064a \u0627\u0644\u0643\u0644\u0645\u0627\u062a",
            "\u063a\u0631\u064a\u0628 \u0627\u0644\u0642\u0631\u0622\u0646",
        )
    )

    key = (
        WORDS_KEY
        if wants_words
        else TAFSIR_KEY
    )

    item = get_ayah(
        sura_number,
        aya_number,
        translation_key=key,
    )

    if not item:
        return []

    item["text"] = item["translation"]

    item["snippet"] = (
        item["arabic_text"]
        + " | "
        + item["translation"]
    )

    item["source"] = (
        QURANENC_SOURCE
        + (
            " - "
            + (
                "\u0628\u064a\u0627\u0646 \u0645\u0639\u0627\u0646\u064a "
                "\u0627\u0644\u0643\u0644\u0645\u0627\u062a"
                if key == WORDS_KEY
                else "\u0627\u0644\u0645\u062e\u062a\u0635\u0631 "
                "\u0641\u064a \u0627\u0644\u062a\u0641\u0633\u064a\u0631"
            )
        )
    )

    return [item]


def format_quran_answer(
    evidence: list[dict],
) -> str:
    if not evidence:
        return ""

    item = evidence[0]

    arabic_text = (
        item.get("arabic_text")
        or ""
    ).strip()

    explanation = (
        item.get("translation")
        or ""
    ).strip()

    parts = []

    if arabic_text:
        parts.append(
            "\u0646\u0635 \u0627\u0644\u0622\u064a\u0629: "
            + arabic_text
        )

    if explanation:
        parts.append(
            "\u0627\u0644\u0628\u064a\u0627\u0646: "
            + explanation
        )

    return "\n\n".join(parts)
