from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import models
from .database import Base, engine
from .translation import translate_text, translate_texts
from .language_codes import LANGUAGE_CODES
from .routes.stations import router as stations_router
from .routes.auth import router as auth_router
from .routes.guide import router as guide_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Risalah AI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://risalah-2.netlify.app", "http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stations_router)
app.include_router(auth_router)
app.include_router(guide_router)


class TranslationRequest(BaseModel):
    text: str
    source_language: str = "ar"
    target_language: str = "en"


class TranslationBatchRequest(BaseModel):
    texts: list[str]
    source_language: str = "ar"
    target_language: str = "en"


@app.get("/health")
def health():
    return {"status": "ok", "service": "risalah-ai"}


@app.post("/api/translate")
def translate(request: TranslationRequest):
    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty."
        )

    supported_nllb_codes = set(LANGUAGE_CODES.values())

    if request.source_language in LANGUAGE_CODES:
        source_language = LANGUAGE_CODES[request.source_language]
    elif request.source_language in supported_nllb_codes:
        source_language = request.source_language
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported source language: {request.source_language}"
        )

    if request.target_language in LANGUAGE_CODES:
        target_language = LANGUAGE_CODES[request.target_language]
    elif request.target_language in supported_nllb_codes:
        target_language = request.target_language
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported target language: {request.target_language}"
        )

    return translate_text(
        text=request.text,
        source_language=source_language,
        target_language=target_language,
    )


@app.post("/api/translate-batch")
def translate_batch(request: TranslationBatchRequest):
    texts = [item.strip() for item in request.texts if item and item.strip()]

    if not texts:
        raise HTTPException(
            status_code=400,
            detail="Texts cannot be empty."
        )

    if len(texts) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 texts per request."
        )

    supported_nllb_codes = set(LANGUAGE_CODES.values())

    if request.source_language in LANGUAGE_CODES:
        source_language = LANGUAGE_CODES[request.source_language]
    elif request.source_language in supported_nllb_codes:
        source_language = request.source_language
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported source language: {request.source_language}"
        )

    if request.target_language in LANGUAGE_CODES:
        target_language = LANGUAGE_CODES[request.target_language]
    elif request.target_language in supported_nllb_codes:
        target_language = request.target_language
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported target language: {request.target_language}"
        )

    return translate_texts(
        texts=texts,
        source_language=source_language,
        target_language=target_language,
    )
