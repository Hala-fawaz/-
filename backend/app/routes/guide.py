import os
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..rag.dorar_client import search_dorar, format_dorar_answer
from ..rag.hadeethenc_client import search_hadeethenc
from ..rag.quranenc_client import get_quran_evidence, format_quran_answer
from ..rag.fts_builder import ensure_index_async
from ..rag.fts_retriever import KnowledgeIndexNotReady
from ..rag.pipeline import answer_question


# Build (or rebuild) the knowledge index in the background when the
# server starts without an up-to-date one. Set RAG_AUTO_BUILD_INDEX=0
# to disable, e.g. when the deploy build step already ran fts_builder.
if os.getenv("RAG_AUTO_BUILD_INDEX", "1").strip() != "0":
    ensure_index_async()


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
        r'[؟?!"\'«»():،,.]',
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
    # Title of the station page the visitor is reading, e.g. «غزوة بدر — بدر».
    # Lets «ما الأماكن المهمة في المحطة؟» know which station is meant.
    station: str | None = Field(default=None, max_length=200)
    # Adds the chosen passages and model to the response (for testing).
    debug: bool = False


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

    # Everything else is answered from the seerah books in
    # knowledge/sources (see rag/pipeline.py).
    try:
        return answer_question(
            question,
            station=request.station,
            debug=request.debug,
        )
    except KnowledgeIndexNotReady as error:
        # The index is being built (first start after a deploy): answer
        # with a short notice instead of an error page.
        return {
            "question": question,
            "answer": str(error),
            "sources": [],
            "status": "index_building",
        }
