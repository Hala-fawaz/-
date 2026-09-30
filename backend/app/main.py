from fastapi import FastAPI
from pydantic import BaseModel
from .translation import translate_text
from .language_codes import LANGUAGE_CODES

app = FastAPI(title="Risalah AI API", version="0.1.0")


class TranslationRequest(BaseModel):
    text: str
    source_language: str = "arb_Arab"
    target_language: str = "eng_Latn"


@app.get("/health")
def health():
    return {"status": "ok", "service": "risalah-ai"}


@app.post("/api/translate")
def translate(request: TranslationRequest):
    source_language = LANGUAGE_CODES.get(
        request.source_language,
        request.source_language
    )
    target_language = LANGUAGE_CODES.get(
        request.target_language,
        request.target_language
    )

    return translate_text(
        text=request.text,
        source_language=source_language,
        target_language=target_language,
    )
