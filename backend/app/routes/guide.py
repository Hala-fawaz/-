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


router = APIRouter(prefix="/api/guide", tags=["guide"])

INSUFFICIENT_ANSWER = "\u0644\u0645 \u0623\u062c\u062f \u0641\u064a \u0627\u0644\u0645\u0635\u0627\u062f\u0631 \u0627\u0644\u0645\u062a\u0627\u062d\u0629 \u062f\u0644\u064a\u0644\u064b\u0627 \u0643\u0627\u0641\u064a\u064b\u0627 \u0644\u0644\u0625\u062c\u0627\u0628\u0629 \u0639\u0646 \u0647\u0630\u0627 \u0627\u0644\u0633\u0624\u0627\u0644."


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
        max_chunks=400,
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
