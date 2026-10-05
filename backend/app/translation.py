from functools import lru_cache
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "facebook/nllb-200-distilled-600M"

# In-memory cache:
# (source_language, target_language, text) -> translation
_TRANSLATION_CACHE = {}


@lru_cache(maxsize=1)
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    model.eval()
    return tokenizer, model


def translate_text(text: str, source_language: str, target_language: str):
    cache_key = (source_language, target_language, text)

    if cache_key in _TRANSLATION_CACHE:
        result = _TRANSLATION_CACHE[cache_key]
    else:
        tokenizer, model = load_model()
        tokenizer.src_lang = source_language

        encoded = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        with torch.inference_mode():
            generated_tokens = model.generate(
                **encoded,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_language),
                max_length=200,
                num_beams=1,
            )

        result = tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True,
        )[0]

        _TRANSLATION_CACHE[cache_key] = result

    return {
        "translation": result,
        "source_language": source_language,
        "target_language": target_language,
        "model": MODEL_NAME,
    }


def translate_texts(
    texts: list[str],
    source_language: str,
    target_language: str,
    batch_size: int = 8,
):
    tokenizer, model = load_model()
    tokenizer.src_lang = source_language

    # Translate each unique missing text only once.
    missing = []
    seen = set()

    for text in texts:
        key = (source_language, target_language, text)
        if key not in _TRANSLATION_CACHE and text not in seen:
            missing.append(text)
            seen.add(text)

    for start in range(0, len(missing), batch_size):
        batch = missing[start:start + batch_size]

        encoded = tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )

        with torch.inference_mode():
            generated_tokens = model.generate(
                **encoded,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_language),
                max_length=200,
                num_beams=1,
            )

        results = tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True,
        )

        for original, translated in zip(batch, results):
            _TRANSLATION_CACHE[
                (source_language, target_language, original)
            ] = translated

    translations = [
        _TRANSLATION_CACHE[(source_language, target_language, text)]
        for text in texts
    ]

    return {
        "translations": translations,
        "source_language": source_language,
        "target_language": target_language,
        "model": MODEL_NAME,
    }
