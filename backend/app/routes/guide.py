import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..rag.fts_retriever import search_fts, extract_terms
from ..rag.semantic_reranker import (
    semantic_rerank,
    sentence_rerank,
    has_sufficient_evidence,
    _question_type,
)
from ..rag.evidence_verifier import verify_evidence
from ..rag.generator import generate_answer
from ..rag.answer_verifier import verify_generated_answer
from ..rag.dorar_client import search_dorar, format_dorar_answer
from ..rag.hadeethenc_client import search_hadeethenc
from ..rag.quranenc_client import get_quran_evidence, format_quran_answer


router = APIRouter(prefix="/api/guide", tags=["guide"])

INSUFFICIENT_ANSWER = "\u0644\u0645 \u0623\u062c\u062f \u0641\u064a \u0627\u0644\u0645\u0635\u0627\u062f\u0631 \u0627\u0644\u0645\u062a\u0627\u062d\u0629 \u062f\u0644\u064a\u0644\u064b\u0627 \u0643\u0627\u0641\u064a\u064b\u0627 \u0644\u0644\u0625\u062c\u0627\u0628\u0629 \u0639\u0646 \u0647\u0630\u0627 \u0627\u0644\u0633\u0624\u0627\u0644."


_HADITH_WORD = "\u062d\u062f\u064a\u062b"

_HADITH_LOOKUP_MARKERS = (
    "\u0635\u062d\u0629",
    "\u0635\u062d\u064a\u062d",
    "\u0636\u0639\u064a\u0641",
    "\u062d\u0633\u0646",
    "\u0645\u0648\u0636\u0648\u0639",
    "\u062a\u062e\u0631\u064a\u062c",
    "\u0627\u0644\u0631\u0627\u0648\u064a",
    "\u0627\u0644\u0645\u062d\u062f\u062b",
    "\u0631\u0648\u0627\u0647",
    "\u0623\u062e\u0631\u062c\u0647",
    "\u0625\u0633\u0646\u0627\u062f",
)

_HADITH_DISCOVERY_MARKERS = (
    "\u0623\u0639\u0637\u0646\u064a \u062d\u062f\u064a\u062b",
    "\u0627\u0639\u0637\u0646\u064a \u062d\u062f\u064a\u062b",
    "\u0627\u0630\u0643\u0631 \u062d\u062f\u064a\u062b",
    "\u062d\u062f\u064a\u062b \u0639\u0646",
    "\u0627\u0628\u062d\u062b \u0639\u0646 \u062d\u062f\u064a\u062b",
)


def _is_hadith_lookup(question: str) -> bool:
    normalized = " ".join((question or "").split())

    if _HADITH_WORD not in normalized:
        return False

    return (
        any(
            marker in normalized
            for marker in _HADITH_LOOKUP_MARKERS
        )
        or any(
            marker in normalized
            for marker in _HADITH_DISCOVERY_MARKERS
        )
    )


def _dorar_search_query(question: str) -> str:
    query = " ".join((question or "").split())

    phrases = (
        "\u0645\u0627 \u0635\u062d\u0629 \u0627\u0644\u062d\u062f\u064a\u062b",
        "\u0645\u0627 \u0635\u062d\u0629 \u062d\u062f\u064a\u062b",
        "\u0647\u0644 \u0647\u0630\u0627 \u0627\u0644\u062d\u062f\u064a\u062b",
        "\u0647\u0644 \u0627\u0644\u062d\u062f\u064a\u062b",
        "\u0647\u0644 \u062d\u062f\u064a\u062b",
        "\u0647\u0644 \u064a\u0635\u062d \u062d\u062f\u064a\u062b",
        "\u062a\u062e\u0631\u064a\u062c \u062d\u062f\u064a\u062b",
        "\u0623\u0639\u0637\u0646\u064a \u062d\u062f\u064a\u062b \u0639\u0646",
        "\u0627\u0639\u0637\u0646\u064a \u062d\u062f\u064a\u062b \u0639\u0646",
        "\u0627\u0630\u0643\u0631 \u062d\u062f\u064a\u062b \u0639\u0646",
        "\u0627\u0628\u062d\u062b \u0639\u0646 \u062d\u062f\u064a\u062b \u0639\u0646",
        "\u062d\u062f\u064a\u062b \u0639\u0646",
    )

    for phrase in phrases:
        query = query.replace(phrase, " ")

    query = re.sub(
        r'[??!"\'??():?,.]',
        " ",
        query,
    )

    removable_words = (
        "\u0635\u062d\u064a\u062d",
        "\u0636\u0639\u064a\u0641",
        "\u0635\u062d\u0629",
        "\u062a\u062e\u0631\u064a\u062c",
    )

    for word in removable_words:
        query = re.sub(
            rf"(?<!\S){re.escape(word)}(?!\S)",
            " ",
            query,
        )

    query = " ".join(query.split())

    return query or question


def _dorar_references(evidence: list[dict]) -> list[dict]:
    references = []
    seen = set()

    for item in evidence:
        key = (
            item.get("source"),
            item.get("page"),
        )

        if key in seen:
            continue

        seen.add(key)

        references.append({
            "source": item.get("source"),
            "page": item.get("page"),
            "url": item.get("url"),
        })

    return references


def _build_hadith_answer(
    hadeeth_results: list[dict],
    dorar_results: list[dict],
) -> str:
    parts = []

    if hadeeth_results:
        item = hadeeth_results[0]

        title = (
            item.get("title")
            or item.get("text")
            or ""
        ).strip()

        grade = (
            item.get("grade")
            or ""
        ).strip()

        attribution = (
            item.get("attribution")
            or ""
        ).strip()

        if title:
            parts.append(title.rstrip(".") + ".")

        status_parts = []

        if grade:
            status_parts.append(
                "\u0627\u0644\u062f\u0631\u062c\u0629: " + grade
            )

        if attribution:
            status_parts.append(
                "\u0627\u0644\u0646\u0633\u0628\u0629: " + attribution
            )

        if status_parts:
            parts.append(
                "\u0641\u064a HadeethEnc: "
                + "\u060c ".join(status_parts)
                + "."
            )

    if dorar_results:
        dorar_text = format_dorar_answer(
            dorar_results,
            max_items=4,
            include_text=not bool(hadeeth_results),
        ).strip()

        if dorar_text:
            parts.append(dorar_text)

    return " ".join(parts).strip()


def _hadith_references(
    hadeeth_results: list[dict],
    dorar_results: list[dict],
) -> list[dict]:
    references = []
    seen = set()

    for item in hadeeth_results[:2]:
        reference_text = (
            item.get("reference")
            or ""
        ).strip()

        key = (
            item.get("source"),
            item.get("page"),
        )

        if key in seen:
            continue

        seen.add(key)

        references.append({
            "source": item.get("source"),
            "page": item.get("page"),
            "url": item.get("url"),
            "reference": reference_text or None,
        })

    for item in _dorar_references(
        dorar_results
    ):
        key = (
            item.get("source"),
            item.get("page"),
        )

        if key in seen:
            continue

        seen.add(key)
        references.append(item)

    return references


class GuideRequest(BaseModel):
    question: str


@router.post("")
def ask_guide(request: GuideRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # Trusted Quran text and Arabic explanation from QuranEnc
    # when the question contains a clear surah + ayah reference.
    try:
        quran_evidence = get_quran_evidence(
            question
        )
    except Exception:
        quran_evidence = []

    if quran_evidence:
        answer = format_quran_answer(
            quran_evidence
        )

        sources = []

        for item in quran_evidence:
            sources.append({
                "source": item.get("source"),
                "page": item.get("page"),
                "url": item.get("url"),
            })

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
        }

    # Trusted live hadith lookup through Dorar when the
    # question explicitly asks for a hadith, grading, narrator,
    # authentication, or takhrij.
    if _is_hadith_lookup(question):
        dorar_query = _dorar_search_query(question)

        try:
            dorar_evidence = search_dorar(
                dorar_query,
                max_results=6,
            )
        except Exception:
            dorar_evidence = []

        try:
            hadeeth_evidence = search_hadeethenc(
                dorar_query,
                max_results=2,
                language="ar",
            )
        except Exception:
            hadeeth_evidence = []

        if dorar_evidence or hadeeth_evidence:
            selected_dorar = dorar_evidence[:4]
            selected_hadeeth = hadeeth_evidence[:2]

            answer = _build_hadith_answer(
                selected_hadeeth,
                selected_dorar,
            )

            return {
                "question": question,
                "answer": answer,
                "sources": _hadith_references(
                    selected_hadeeth,
                    selected_dorar,
                ),
            }

    # 1) Keyword retrieval from the full knowledge base.
    candidates = search_fts(
        question,
        top_k=80,
    )

    if not candidates:
        return {
            "question": question,
            "answer": INSUFFICIENT_ANSWER,
            "sources": [],
        }

    # 2) Semantic reranking over overlapping chunks.
    chunk_results = semantic_rerank(
        question,
        candidates,
        top_k=10,
        max_chunks=160,
    )

    question_terms = extract_terms(question)

    # 3) General evidence gate before deeper processing.
    trusted_chunks = [
        item
        for item in chunk_results
        if has_sufficient_evidence([item], question_terms)
    ]

    if not trusted_chunks:
        return {
            "question": question,
            "answer": INSUFFICIENT_ANSWER,
            "sources": [],
        }

    # 4) Rerank individual sentences, not just large chunks.
    sentence_results = sentence_rerank(
        question,
        trusted_chunks,
        top_k=10,
    )

    if not sentence_results:
        return {
            "question": question,
            "answer": INSUFFICIENT_ANSWER,
            "sources": [],
        }

    # 5) Typed factual questions use the strongest deterministic
    # retrieval result directly. This prevents an LLM verifier from
    # replacing a better grounded fact with a weaker sentence.
    question_kind = _question_type(question)

    if question_kind != "general":
        verified = sentence_results[:1]
    else:
        verified = verify_evidence(
            question,
            sentence_results,
            max_items=8,
        )

    if not verified:
        return {
            "question": question,
            "answer": INSUFFICIENT_ANSWER,
            "sources": [],
        }

    # Keep strongest verified evidence while preventing factual
    # questions from mixing unrelated entities across different sources.
    verified = sorted(
        verified,
        key=lambda item: float(item.get("sentence_score", 0) or 0),
        reverse=True,
    )

    evidence = []
    seen_texts = set()
    question_kind = _question_type(question)

    strongest_group = None
    if verified and question_kind != "general":
        strongest_group = (
            verified[0].get("source"),
            verified[0].get("page"),
        )

    for item in verified:
        if strongest_group is not None:
            item_group = (
                item.get("source"),
                item.get("page"),
            )
            if item_group != strongest_group:
                continue

        text = " ".join(
            (item.get("snippet") or "").split()
        )

        if not text or text in seen_texts:
            continue

        seen_texts.add(text)
        evidence.append(item)

        if len(evidence) >= 4:
            break

    if not evidence:
        return {
            "question": question,
            "answer": INSUFFICIENT_ANSWER,
            "sources": [],
        }

    # 6) Generate only from verified evidence.
    answer = generate_answer(
        question,
        evidence,
    )

    # 7) Verify every generated sentence against the trusted evidence.
    if question_kind == "general":
        answer = verify_generated_answer(
            question,
            answer,
            evidence,
        )

    # References come only from evidence that passed verification.
    references = []
    seen_references = set()

    for source in evidence:
        key = (
            source.get("source"),
            source.get("page"),
        )

        if key in seen_references:
            continue

        seen_references.add(key)

        references.append({
            "source": source.get("source"),
            "page": source.get("page"),
        })

    return {
        "question": question,
        "answer": answer,
        "sources": references,
    }
