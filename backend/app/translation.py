import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from .language_codes import LANGUAGE_CODES


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

MODEL_NAME = os.getenv(
    "GROQ_TRANSLATION_MODEL",
    "allam-2-7b",
)

MAX_CHUNK_CHARS = 1200

_TRANSLATION_CACHE = {}
NLLB_TO_SHORT = {
    value: key
    for key, value in LANGUAGE_CODES.items()
}

LANGUAGE_NAMES = {
    "ar": "Arabic",
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "tr": "Turkish",
    "ur": "Urdu",
    "fa": "Persian",
    "id": "Indonesian",
    "ms": "Malay",
    "bn": "Bengali",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "gu": "Gujarati",
    "mr": "Marathi",
    "ru": "Russian",
    "uk": "Ukrainian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "th": "Thai",
    "vi": "Vietnamese",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "el": "Greek",
    "he": "Hebrew",
}


def _short_code(code: str) -> str:
    return NLLB_TO_SHORT.get(code, code)


def _language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    return Groq(api_key=api_key)


def _split_text(
    text: str,
    max_chars: int = MAX_CHUNK_CHARS,
) -> list[str]:
    text = (text or "").strip()

    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    chunks = []
    remaining = text

    while len(remaining) > max_chars:
        cut = remaining.rfind(
            " ",
            0,
            max_chars + 1,
        )

        if cut < max_chars // 2:
            cut = max_chars

        chunks.append(
            remaining[:cut].strip()
        )

        remaining = remaining[cut:].strip()

    if remaining:
        chunks.append(remaining)

    return chunks


def _clean_translation(text: str) -> str:
    text = (text or "").strip()

    text = re.sub(
        r"^(?:translation|translated text)\s*:\s*",
        "",
        text,
        flags=re.I,
    ).strip()

    if (
        len(text) >= 2
        and text[0] == text[-1]
        and text[0] in {'"', "'"}
    ):
        text = text[1:-1].strip()

    return text


def _translate_chunk(
    text: str,
    source_language: str,
    target_language: str,
) -> str:
    if source_language == target_language:
        return text

    source_name = _language_name(
        source_language
    )

    target_name = _language_name(
        target_language
    )

    system_prompt = f"""
You are a precise translation engine.

Translate from {source_name} ({source_language})
to {target_name} ({target_language}).

Rules:
- Return ONLY the translated text.
- Do not explain the translation.
- Do not add facts or commentary.
- Preserve names, numbers, punctuation and meaning.
- Preserve HTML tags, placeholders, URLs and code-like tokens.
- Keep the natural style of the target language.
""".strip()

    response = _get_client().chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        temperature=0,
        max_tokens=1200,
    )

    translated = _clean_translation(
        response.choices[0].message.content
    )

    if not translated:
        raise RuntimeError(
            "Translation model returned no translation."
        )

    return translated


def translate_text(
    text: str,
    source_language: str,
    target_language: str,
):
    source_language = _short_code(
        source_language
    )

    target_language = _short_code(
        target_language
    )

    text = (text or "").strip()

    if not text:
        return {
            "translation": "",
            "source_language": source_language,
            "target_language": target_language,
            "model": f"groq:{MODEL_NAME}",
        }

    cache_key = (
        source_language,
        target_language,
        text,
    )

    if cache_key not in _TRANSLATION_CACHE:
        chunks = _split_text(text)

        translated_chunks = [
            _translate_chunk(
                chunk,
                source_language,
                target_language,
            )
            for chunk in chunks
        ]

        _TRANSLATION_CACHE[cache_key] = " ".join(
            translated_chunks
        )

    return {
        "translation": _TRANSLATION_CACHE[
            cache_key
        ],
        "source_language": source_language,
        "target_language": target_language,
        "model": f"groq:{MODEL_NAME}",
    }


def translate_texts(
    texts: list[str],
    source_language: str,
    target_language: str,
    batch_size: int = 8,
):
    source_language = _short_code(
        source_language
    )

    target_language = _short_code(
        target_language
    )

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
        "source_language": source_language,
        "target_language": target_language,
        "model": f"groq:{MODEL_NAME}",
    }
