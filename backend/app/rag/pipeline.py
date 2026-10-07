"""Answer a question from the seerah knowledge base.

    plan_query        -> which words to require, which only help ranking
    search_passages   -> candidate passages from the SQLite FTS5 index
    rank_passages     -> score them; stop here if nothing is relevant
    select_evidence   -> a diverse handful that fits the model's budget
    compose_answer    -> the narrator writes, citing passages as [n]
    verify            -> second check by the same model (RAG_VERIFY_ANSWERS)

The Quran and hadith lookups (QuranEnc, Dorar, HadeethEnc) stay in
routes/guide.py and run before this.
"""

import re
import sys

from .answer_verifier import should_verify, verify_generated_answer
from .arabic_text import normalize, tokenize
from .fts_builder import ensure_index_async, index_is_ready
from . import fts_retriever
from .fts_retriever import KnowledgeIndexNotReady, plan_query, search_passages
from .generator import INSUFFICIENT_ANSWER, compose_answer
from .llm import LLMUnavailable, primary_model
from .llm_options import model_profile
from .passage_ranker import (
    expand_short_passages,
    has_enough_evidence,
    public_view,
    rank_passages,
    select_evidence,
)


BUSY_ANSWER = (
    "وجدتُ في المصادر ما يتعلق بسؤالك، لكن خدمة صياغة الإجابة مشغولة الآن. "
    "حاول بعد دقيقة، ويمكنك الرجوع إلى المصادر المذكورة أدناه."
)
INDEX_BUILDING_MESSAGE = "جاري تجهيز فهرس المصادر لأول مرة، حاول مرة أخرى بعد دقيقة أو دقيقتين."

GREETING_ANSWER = (
    "وعليكم السلام ورحمة الله وبركاته. أنا راوي رِسالة، أحدّثك عن سيرة النبي ﷺ من كتب السيرة "
    "المعتمدة في المنصة. اسألني مثلًا: ماذا حدث في غزوة بدر؟ أو: متى كانت الهجرة إلى المدينة؟"
)
INTRO_ANSWER = (
    "أنا راوي رِسالة، مرشدك في رحلة السيرة النبوية. أجيبك من كتب السيرة الموجودة في المنصة، "
    "وأذكر لك المصادر تحت كل إجابة. جرّب أن تسألني عن حدث أو شخصية، مثل: من هي خديجة بنت خويلد؟"
)
THANKS_ANSWER = "وإياك، بارك الله فيك. يسعدني أن أكمل معك رحلة السيرة متى شئت."

_GREETINGS = {normalize(w) for w in ("السلام", "سلام", "مرحبا", "مرحبًا", "اهلا", "أهلا", "هلا", "hi", "hello", "صباح", "مساء")}
_THANKS = {normalize(w) for w in ("شكرا", "شكرًا", "مشكور", "جزاك", "يعطيك")}
_WHO_ARE_YOU = (normalize("من انت"), normalize("من أنت"), normalize("ما اسمك"), normalize("وش انت"),
                normalize("ماذا تستطيع"), normalize("كيف تساعدني"), normalize("وش تقدر"))


def _small_talk(question: str) -> str | None:
    tokens = tokenize(question)
    if not tokens or len(tokens) > 6:
        return None
    text = " ".join(tokens)
    if any(phrase in text for phrase in _WHO_ARE_YOU):
        return INTRO_ANSWER
    if tokens[0] in _GREETINGS and len(tokens) <= 4:
        return GREETING_ANSWER
    if tokens[0] in _THANKS:
        return THANKS_ANSWER
    return None


def _source_entry(item: dict) -> dict:
    return {
        "source": item.get("title") or item.get("source"),
        "page": item.get("page"),
        "section": item.get("heading") or None,
        "file": item.get("source"),
    }


def _sources(evidence: list[dict], cited: list[int], limit: int = 5) -> list[dict]:
    """Sources the answer actually used (by citation), without repeats."""
    ordered = [evidence[n - 1] for n in cited if 1 <= n <= len(evidence)] or evidence[:3]
    seen, out = set(), []
    for item in ordered:
        key = (item.get("title"), item.get("page"))
        if key in seen:
            continue
        seen.add(key)
        out.append(_source_entry(item))
        if len(out) >= limit:
            break
    return out


def answer_question(question: str, station: str | None = None, debug: bool = False) -> dict:
    question = re.sub(r"\s+", " ", question or "").strip()
    station = (station or "").strip()[:200] or None
    response = {"question": question, "answer": INSUFFICIENT_ANSWER, "sources": []}

    reply = _small_talk(question)
    if reply:
        return {**response, "answer": reply}

    if not index_is_ready(fts_retriever.DB_PATH):
        ensure_index_async(fts_retriever.DB_PATH)
        raise KnowledgeIndexNotReady(INDEX_BUILDING_MESSAGE)

    plan = plan_query(question, station)
    if plan.is_empty:
        return response

    ranked = rank_passages(plan, search_passages(plan))
    if not has_enough_evidence(plan, ranked):
        return response

    profile = model_profile(primary_model())
    evidence = select_evidence(ranked, profile.max_passages, profile.evidence_chars)
    evidence = expand_short_passages(evidence, profile.evidence_chars)

    try:
        composed = compose_answer(question, evidence, mode=plan.mode, station=station)
    except LLMUnavailable as error:
        print(f"[rag] no model available: {error}", file=sys.stderr)
        return {**response, "answer": BUSY_ANSWER, "sources": _sources(evidence, []), "status": "llm_unavailable"}

    if composed.insufficient:
        return response

    answer = composed.text
    if should_verify(composed.model):
        answer = verify_generated_answer(question, answer, evidence, model=composed.model)
        if answer == INSUFFICIENT_ANSWER:
            return response

    result = {**response, "answer": answer, "sources": _sources(evidence, composed.cited)}

    if debug:
        result["debug"] = {
            "mode": plan.mode,
            "model": composed.model,
            "required": [group.word for group in plan.required],
            "evidence": [
                {k: v for k, v in public_view(item).items() if k != "text"} | {"chars": len(item["text"])}
                for item in evidence
            ],
        }

    return result
