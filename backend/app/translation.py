import os
import json
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from .language_codes import LANGUAGE_CODES


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

MODEL_NAME = os.getenv(
    "GROQ_TRANSLATION_MODEL",
    "openai/gpt-oss-120b",
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


def _translate_batch_once(
    texts: list[str],
    source_language: str,
    target_language: str,
) -> list[str]:
    if source_language == target_language:
        return texts

    source_name = _language_name(source_language)
    target_name = _language_name(target_language)

    system_prompt = f"""
You are a precise translation engine.

Translate every item from {source_name} ({source_language})
to {target_name} ({target_language}).

Rules:
- Return ONLY valid JSON.
- Use exactly this shape: {{"translations": ["...", "..."]}}
- Keep exactly the same number of items and the same order.
- Do not omit, merge, explain, number, or comment on any item.
- Preserve names, numbers, punctuation, URLs, placeholders and code-like tokens.
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
                "content": json.dumps(texts, ensure_ascii=False),
            },
        ],
        temperature=0,
        max_tokens=4000,
    )

    raw = (response.choices[0].message.content or "").strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, flags=re.S)
        if not match:
            raise RuntimeError("Translation model returned invalid batch JSON.")
        data = json.loads(match.group(0))

    translations = data.get("translations")

    if not isinstance(translations, list) or len(translations) != len(texts):
        raise RuntimeError(
            "Translation model returned an invalid number of translations."
        )

    return [_clean_translation(str(item)) for item in translations]


def translate_texts(
    texts: list[str],
    source_language: str,
    target_language: str,
    batch_size: int = 20,
):
    source_language = _short_code(source_language)
    target_language = _short_code(target_language)

    cleaned_texts = [(text or "").strip() for text in texts]
    translations = [""] * len(cleaned_texts)

    pending_indices = []

    for index, text in enumerate(cleaned_texts):
        if not text:
            continue

        cache_key = (
            source_language,
            target_language,
            text,
        )

        if cache_key in _TRANSLATION_CACHE:
            translations[index] = _TRANSLATION_CACHE[cache_key]
        else:
            pending_indices.append(index)

    for offset in range(0, len(pending_indices), batch_size):
        batch_indices = pending_indices[offset:offset + batch_size]
        batch_texts = [cleaned_texts[index] for index in batch_indices]

        batch_translations = _translate_batch_once(
            batch_texts,
            source_language,
            target_language,
        )

        for index, translated in zip(batch_indices, batch_translations):
            translations[index] = translated

            cache_key = (
                source_language,
                target_language,
                cleaned_texts[index],
            )
            _TRANSLATION_CACHE[cache_key] = translated

    return {
        "translations": translations,
        "source_language": source_language,
        "target_language": target_language,
        "model": f"groq:{MODEL_NAME}",
    }

