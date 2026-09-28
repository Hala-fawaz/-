from functools import lru_cache
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "facebook/nllb-200-distilled-600M"


@lru_cache(maxsize=1)
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return tokenizer, model


def translate_text(text: str, source_language: str, target_language: str):
    # Research adapter. Keep this isolated so the team can replace it
    # with an approved production translation provider later.
    tokenizer, model = load_model()

    tokenizer.src_lang = source_language
    encoded = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

    generated_tokens = model.generate(
        **encoded,
        forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_language),
        max_length=200,
        num_beams=4,
    )

    result = tokenizer.batch_decode(
        generated_tokens,
        skip_special_tokens=True
    )[0]

    return {
        "translation": result,
        "source_language": source_language,
        "target_language": target_language,
        "model": MODEL_NAME,
    }
