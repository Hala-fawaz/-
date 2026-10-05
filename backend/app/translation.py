import json
import os
from html import unescape
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .language_codes import LANGUAGE_CODES


API_URL = "https://api.mymemory.translated.net/get"
MAX_CHUNK_CHARS = 450

_TRANSLATION_CACHE = {}
NLLB_TO_SHORT = {value: key for key, value in LANGUAGE_CODES.items()}


def _short_code(code: str) -> str:
    return NLLB_TO_SHORT.get(code, code)


def _split_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    text = (text or "").strip()

    if len(text) <= max_chars:
        return [text] if text else []

    chunks = []
    remaining = text

    while len(remaining) > max_chars:
        cut = remaining.rfind(" ", 0, max_chars + 1)

        if cut < max_chars // 2:
            cut = max_chars

        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()

    if remaining:
        chunks.append(remaining)

    return chunks


def _translate_chunk(text: str, source_language: str, target_language: str) -> str:
    if source_language == target_language:
        return text

    params = {
        "q": text,
        "langpair": f"{source_language}|{target_language}",
    }

    email = os.getenv("MYMEMORY_EMAIL", "").strip()
    if email:
        params["de"] = email

    url = f"{API_URL}?{urlencode(params)}"

    request = Request(
        url,
        headers={"User-Agent": "Risalah/1.0"},
    )

    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))

    translated = (
        payload.get("responseData", {})
        .get("translatedText", "")
    )

    if not translated:
        raise RuntimeError("Translation service returned no translation.")

    return unescape(translated).strip()


def translate_text(text: str, source_language: str, target_language: str):
    source_language = _short_code(source_language)
    target_language = _short_code(target_language)

    cache_key = (source_language, target_language, text)

    if cache_key not in _TRANSLATION_CACHE:
        chunks = _split_text(text)

        translated_chunks = [
            _translate_chunk(chunk, source_language, target_language)
            for chunk in chunks
        ]

        _TRANSLATION_CACHE[cache_key] = " ".join(translated_chunks)

    return {
        "translation": _TRANSLATION_CACHE[cache_key],
        "source_language": source_language,
        "target_language": target_language,
        "model": "mymemory-api",
    }


def translate_texts(
    texts: list[str],
    source_language: str,
    target_language: str,
    batch_size: int = 8,
):
    translations = [
        translate_text(
            text=text,
            source_language=source_language,
            target_language=target_language,
        )["translation"]
        for text in texts
    ]

    return {
        "translations": translations,
        "source_language": _short_code(source_language),
        "target_language": _short_code(target_language),
        "model": "mymemory-api",
    }
