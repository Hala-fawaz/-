"""Check the guide on a fixed set of seerah questions (not a unit test).

From the backend folder, after building the index:

    python tests/eval_guide_questions.py                 # retrieval only, no API key needed
    python tests/eval_guide_questions.py --llm           # also write answers with the model
    python tests/eval_guide_questions.py -q "ماذا حدث في غزوة بدر؟" --llm
    python tests/eval_guide_questions.py -q "ما الأماكن المهمة في المحطة؟" -s "غزوة بدر — بدر" --llm

For each question it prints which passages would be sent to the model
and whether they look relevant (every word group of the question's
"judge" must appear in the passage). Run it before and after changing
the retriever to see whether a change helps.
"""

import argparse
import re
import sys
import time
import unicodedata
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.rag.fts_retriever import plan_query, search_passages  # noqa: E402
from app.rag.llm_options import model_profile  # noqa: E402
from app.rag.llm import primary_model  # noqa: E402
from app.rag.passage_ranker import (  # noqa: E402
    expand_short_passages, has_enough_evidence, rank_passages, select_evidence,
)

# (question, station, judge): a passage is relevant when it contains at
# least one word from EACH group of the judge.
QUESTIONS = [
    ("ماذا حدث في غزوة بدر؟", None, [["بدر"], ["قريش", "المشركين", "العير", "أبو سفيان", "أبي سفيان", "القتال", "النصر", "المسلمين"]]),
    ("متى كانت غزوة بدر؟", None, [["بدر"], ["رمضان", "الثانية", "سنة اثنتين", "624", "السابع عشر"]]),
    ("كم كان عدد المسلمين في غزوة بدر؟", None, [["بدر"], ["ثلاثمائة", "ثلاث مائة", "ثلاثمئة", "313", "314", "317", "بضعة عشر"]]),
    ("متى ولد النبي محمد؟", None, [["ولد", "مولد"], ["عام الفيل", "571", "الاثنين", "ربيع الأول"]]),
    ("من هي خديجة بنت خويلد؟", None, [["خديجة"], ["خويلد", "تزوج", "زوج", "أم المؤمنين", "تاجرة", "مال"]]),
    ("كيف هاجر النبي إلى المدينة؟", None, [["هجرة", "هاجر"], ["أبو بكر", "أبي بكر", "غار ثور", "ثور", "سراقة", "يثرب"]]),
    ("ما هي بيعة العقبة الأولى؟", None, [["العقبة"], ["بيعة", "بايع", "بايعوا"]]),
    ("ماذا حدث في غزوة أحد؟", None, [["أحد"], ["الرماة", "حمزة", "المشركين", "قريش", "خالد", "جبل"]]),
    ("من أشار بحفر الخندق؟", None, [["خندق"], ["سلمان"]]),
    ("ما شروط صلح الحديبية؟", None, [["الحديبية"], ["صلح", "شروط", "سهيل", "الشروط"]]),
    ("ماذا فعل النبي يوم فتح مكة؟", None, [["فتح"], ["مكة"], ["الكعبة", "الأصنام", "عفا", "الطلقاء", "اذهبوا", "دخل"]]),
    ("ما قصة الإسراء والمعراج؟", None, [["الإسراء", "أسري"], ["المعراج", "الأقصى", "البراق", "السماء"]]),
    ("من أول من أسلم من الرجال؟", None, [["أسلم", "الإسلام"], ["أبو بكر", "أبي بكر", "علي", "زيد"]]),
    ("أين نزل الوحي أول مرة؟", None, [["حراء"], ["الوحي", "جبريل", "اقرأ", "نزل"]]),
    ("ما عام الحزن؟", None, [["الحزن"], ["خديجة", "أبو طالب", "أبي طالب"]]),
    ("ماذا حدث في رحلة الطائف؟", None, [["الطائف"], ["ثقيف", "عداس", "الحجارة", "زيد بن حارثة", "سفهاء", "أغروا"]]),
    ("ما موقف أبي طالب من النبي؟", None, [["طالب"], ["حمى", "نصر", "دافع", "منع", "يحميه", "حماية", "عمه"]]),
    ("ماذا قال النبي في خطبة الوداع؟", None, [["الوداع"], ["دماءكم", "أموالكم", "الربا", "النساء", "حرام", "خطب"]]),
    ("متى توفي النبي؟", None, [["توفي", "وفاة", "وفاته"], ["ربيع", "الاثنين", "الحادية عشرة", "632", "11"]]),
    ("ما أهمية مكة في بداية الدعوة؟", None, [["مكة"], ["الدعوة"], ["الكعبة", "مركز", "قريش", "دين العرب"]]),
    ("من هو بلال بن رباح؟", None, [["بلال"], ["مؤذن", "أذن", "حبشي", "أمية", "عذب", "رباح"]]),
    ("ما قصة عام الفيل؟", None, [["الفيل"], ["أبرهة", "الكعبة", "أبابيل", "الحبشة"]]),
    ("ماذا حدث في غزوة تبوك؟", None, [["تبوك"], ["الروم", "العسرة", "المتخلفين", "الثلاثة", "كعب بن مالك", "خلفوا"]]),
    ("وش صار في بدر؟", None, [["بدر"], ["قريش", "المشركين", "العير", "أبو سفيان", "أبي سفيان", "القتال", "النصر", "المسلمين"]]),
    ("غزوه احد", None, [["أحد"], ["الرماة", "حمزة", "المشركين", "قريش", "خالد", "جبل"]]),
    ("ما الأماكن المهمة في المحطة؟", "غزوة بدر — بدر", [["بدر"], ["العدوة", "القليب", "العريش", "الماء", "بئر", "وادي", "ماء"]]),
]

_DIACRITICS = re.compile(r"[\U00000610-\U0000061A\U0000064B-\U0000065F\U00000670\U000006D6-\U000006ED\U00000640]")


def _simple(text: str) -> str:
    text = _DIACRITICS.sub("", unicodedata.normalize("NFKC", text or ""))
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
        text = text.replace(a, b)
    return text


def relevant(text: str, judge) -> bool:
    text = _simple(text)
    return all(any(_simple(word) in text for word in group) for group in judge)


def retrieve(question: str, station: str | None):
    plan = plan_query(question, station)
    ranked = rank_passages(plan, search_passages(plan))
    if not has_enough_evidence(plan, ranked):
        return plan, []
    profile = model_profile(primary_model())
    evidence = select_evidence(ranked, profile.max_passages, profile.evidence_chars)
    return plan, expand_short_passages(evidence, profile.evidence_chars)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--question")
    parser.add_argument("-s", "--station")
    parser.add_argument("--llm", action="store_true", help="also generate answers (needs GROQ_API_KEY)")
    args = parser.parse_args()

    if args.question:
        questions = [(args.question, args.station, None)]
    else:
        questions = QUESTIONS

    totals = {"hit1": 0, "any": 0, "precision": []}

    for question, station, judge in questions:
        started = time.time()
        plan, evidence = retrieve(question, station)
        flags = [relevant(f"{e['heading']} {e['text']}", judge) for e in evidence] if judge else []
        marks = "".join("✓" if f else "✗" for f in flags) or ("—" if judge else "")
        print(f"\n{question}  [{plan.mode}] {marks}  ({(time.time() - started) * 1000:.0f} ms)")

        for item in evidence:
            page = f" ص {item['page']}" if item.get("page") else ""
            print(f"   {item['score']:.2f}  {item['title']}{page}  ‹{item['heading']}›")

        if judge:
            totals["hit1"] += 1 if flags[:1] == [True] else 0
            totals["any"] += 1 if any(flags) else 0
            if flags:
                totals["precision"].append(sum(flags) / len(flags))

        if args.llm:
            from app.rag.pipeline import answer_question
            result = answer_question(question, station=station, debug=True)
            print("\n" + result["answer"])
            for source in result["sources"]:
                print("   •", source["source"], f"ص {source['page']}" if source.get("page") else "")
            print("   model:", result.get("debug", {}).get("model"))

    if len(questions) > 1:
        n = len(questions)
        precision = sum(totals["precision"]) / max(len(totals["precision"]), 1)
        print(f"\nTop passage relevant: {totals['hit1']}/{n} | at least one relevant: {totals['any']}/{n} | "
              f"precision of passages sent to the model: {precision:.2f}")


if __name__ == "__main__":
    main()
