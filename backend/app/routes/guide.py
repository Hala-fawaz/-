from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..rag.hybrid_retriever import hybrid_retrieve
from ..rag.generator import generate_answer


router = APIRouter(prefix="/api/guide", tags=["guide"])


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

    sources = hybrid_retrieve(
        question,
        top_k=2,
        candidate_k=200,
    )

    answer = generate_answer(
        question,
        sources,
    )

    references = [
        {
            "source": source["source"],
            "page": source["page"],
        }
        for source in sources
    ]

    return {
        "question": question,
        "answer": answer,
        "sources": references,
    }
