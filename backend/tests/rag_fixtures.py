"""Small fixture library and a fake Groq client for the RAG tests.

The tests never call the real model and never need the 600 MB index:
they build a tiny index from the texts below in a temporary folder.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

ZWNJ = "\N{ZERO WIDTH NON-JOINER}"

# A miniature Shamela export: book card, running title above each page
# marker, headings marked with U+200C, footnotes at the bottom of pages.
SEERAH_BOOK = f"""السيرة المختصرة
(مؤلف تجريبي)
الكتاب
:
السيرة المختصرة
السيرة المختصرة
(ص: 1)
{ZWNJ}
{ZWNJ}الهجرة إلى المدينة
هاجر النبي صلى الله عليه وسلم من مكة إلى المدينة مع صاحبه أبي بكر الصديق، فاختبأ في غار ثور ثلاث ليال، ثم سلكا طريق الساحل حتى بلغا قباء، واستقبله الأنصار بالفرح والتكبير.
السيرة المختصرة
(ص: 2)
{ZWNJ}
{ZWNJ}غزوة بدر الكبرى
خرج رسول الله صلى الله عليه وسلم في رمضان من السنة الثانية للهجرة لاعتراض عير قريش التي يقودها أبو سفيان «1» ، فنجت العير وأصرت قريش على القتال.
{ZWNJ}
{ZWNJ}عدد الجيشين
وكان مع النبي صلى الله عليه وسلم ثلاثمائة وبضعة عشر رجلا، وكان المشركون نحو ألف مقاتل، والتقى الجمعان يوم الجمعة السابع عشر من رمضان.
(1) انظر سيرة ابن هشام 1/ 606.
السيرة المختصرة
(ص: 3)
واستشار النبي صلى الله عليه وسلم أصحابه، فقام سعد بن معاذ فقال: امض لما أمرك الله فنحن معك. ثم دارت المعركة فنصر الله المؤمنين، وقُتل من المشركين سبعون وأُسر سبعون، وكان ذلك يوم الفرقان.
السيرة المختصرة
(ص: 4)
{ZWNJ}
{ZWNJ}غزوة أحد
وفي شوال من السنة الثالثة خرجت قريش للثأر، فجعل النبي صلى الله عليه وسلم الرماة على الجبل وأمرهم ألا يبرحوا مكانهم، فلما نزل أكثرهم يطلبون الغنيمة التف خالد بن الوليد بالخيل، واستشهد حمزة رضي الله عنه.
"""

# Fully vocalized text: the old index split «بَدْرٍ» into single letters.
VOCALIZED_VOLUME = f"""كتاب مشكول
كتاب مشكول - جـ 1
(ص: 10)
{ZWNJ}
{ZWNJ}ذِكْرُ وَقْعَةِ بَدْرٍ
قَالَ ابْنُ إسْحَاقَ: وَكَانَتْ وَقْعَةُ بَدْرٍ يَوْمَ الْجُمُعَةِ صَبِيحَةَ سَبْعَ عَشْرَةَ مِنْ رَمَضَانَ، وَنَزَلَ الْمُسْلِمُونَ عِنْدَ الْمَاءِ بِالْعُدْوَةِ الدُّنْيَا.
كتاب مشكول - جـ 1
(ص: 11)
وَبَنَى الْمُسْلِمُونَ لِرَسُولِ اللَّهِ صلى الله عليه وسلم عَرِيشًا يَكُونُ فِيهِ.
"""

JOURNEY_EVENTS = """رحلة الإسلام: من ما قبل البعثة إلى عهد الخلفاء الراشدين
الإصدار التجريبي
============================================================

• ملاحظة عن الملف.

============================================================
العهد المدني (1 – 11 هـ) — 2 محطة
وصف المرحلة.
============================================================

36) غزوة بدر الكبرى
------------------------------------------------------------
المكان: بدر | التاريخ: 624م — 17 رمضان، 2 هـ | التصنيف: الأحداث المهمة

الملخص: التقى نحو ثلاثمئة وبضعة عشر مسلمًا بنحو ألف من قريش عند ماء بدر.

أبرز الأماكن:
  - بئر بدر والعدوة الدنيا والعريش الذي بُني للنبي ﷺ.

المصادر:
  - السيرة المختصرة، ص 2


37) غزوة أحد
------------------------------------------------------------
المكان: جبل أحد | التاريخ: 625م — شوال، 3 هـ

الملخص: خالف الرماة أمر النبي ﷺ فتحول النصر إلى ابتلاء.
"""


def write_fixture_sources(folder: Path) -> Path:
    sources = folder / "sources"
    (sources / "كتاب مشكول").mkdir(parents=True)
    (sources / "السيرة المختصرة.txt").write_text(SEERAH_BOOK, encoding="utf-8")
    (sources / "كتاب مشكول" / "001.txt").write_text(VOCALIZED_VOLUME, encoding="utf-8")
    (sources / "journey-events.txt").write_text(JOURNEY_EVENTS, encoding="utf-8")
    # An exact duplicate, like the "copy" folder in the real sources.
    (sources / "كتاب مشكول copy").mkdir()
    (sources / "كتاب مشكول copy" / "001.txt").write_text(VOCALIZED_VOLUME, encoding="utf-8")
    return sources


class FakeGroq:
    """Mimics groq.Groq().chat.completions.create().

    `replies` maps a model name to a reply string, a list of replies
    (consumed in order), or an Exception to raise.
    """

    def __init__(self, replies: dict):
        self.replies = {key: (list(value) if isinstance(value, list) else value) for key, value in replies.items()}
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        reply = self.replies.get(kwargs["model"], self.replies.get("*"))
        if isinstance(reply, list):
            reply = reply.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if reply is None:
            raise RuntimeError(f"no fake reply for {kwargs['model']}")
        message = SimpleNamespace(content=reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")])

    def prompt(self, index: int = -1) -> str:
        return self.calls[index]["messages"][-1]["content"]
