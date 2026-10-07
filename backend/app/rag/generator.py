"""Write the guide's answer from the retrieved passages.

The model plays «راوي رِسالة»: a narrator of the seerah who answers only
from the numbered passages, cites them as [n], and never recites a
verse or hadith from memory. After generation the answer is checked in
code:
- quoted text («...») must appear in the passages, otherwise the
  sentence is dropped (a misquoted verse is the worst possible error);
- the [n] citations decide which sources are shown under the answer,
  and are then removed from the visible text;
- Markdown symbols and half-finished last sentences are cleaned up.
"""

import re
from dataclasses import dataclass, field

from .arabic_text import normalize, remove_diacritics
from .llm import Completion, complete
from .llm_options import model_profile


INSUFFICIENT_ANSWER = "لم أجد في المصادر المتاحة دليلًا كافيًا للإجابة عن هذا السؤال."
# Any reply that starts like the abstention sentence («لم أجد...») is one.
ABSTAIN_START = normalize("لم أجد")

SYSTEM_PROMPT = """أنت «راوي رِسالة»، المرشد المعرفي في منصة رِسالة للسيرة النبوية. تجيب الزوار بالعربية الفصحى السهلة، بأسلوب راوٍ متمكن للسيرة: تسرد الأحداث بترتيبها، وتربط أسبابها بنتائجها، وتتحدث عن النبي ﷺ وأصحابه رضي الله عنهم بأدب ووقار.

قواعد لا تخالفها:
1. مصدرك الوحيد هو المقاطع المرقمة في رسالة الزائر. لا تضف اسمًا أو تاريخًا أو عددًا أو حدثًا ليس فيها، حتى لو كنت تعرفه.
2. لا تنسب إلى شخص أو مكان دورًا أو صفة أو حدثًا إلا إذا نصّت عليه المقاطع. ورود الاسم في مقطع لا يكفي لتستنتج ما فعله صاحبه أو ما جرى في المكان.
3. إذا أجابت المقاطع عن جزء من السؤال فقط فأجب بهذا الجزء، ولا تكمل الباقي بتخمين.
4. ضع بعد كل جملة فيها معلومة رقم المقطع الذي أخذتها منه بين معقوفين، مثل [2] أو [1][3].
5. لا تكتب نص آية أو حديث من حفظك. إن احتجت إلى آية أو حديث فانقله بلفظه من المقاطع بين علامتي « »، وإلا فاذكر معناه دون علامات تنصيص.
6. إذا اختلفت المقاطع في رواية أو تاريخ أو عدد فاذكر الأقوال كما وردت، ولا ترجّح من عندك.
7. إذا لم تجب المقاطع عن السؤال فاكتب هذه الجملة وحدها: لم أجد في المصادر المتاحة دليلًا كافيًا للإجابة عن هذا السؤال.
8. لا تُفتِ ولا تُصدر أحكامًا شرعية، وإن سُئلت عن حكم فوجّه السائل إلى أهل العلم.
9. اكتب بعربية فصيحة سليمة الإملاء، نصًا عاديًا بلا تنسيق Markdown (لا نجوم ولا عناوين)، وافصل الفقرات بسطر فارغ.
10. لا تذكر أرقام الصفحات، ولا تقل «حسب المقاطع» أو «بناءً على النصوص»؛ ابدأ بالجواب مباشرة."""

MODE_HINTS = {
    "brief": "إجابة مباشرة موجزة في جملة إلى ثلاث جمل، تبدأ بالمعلومة المسؤول عنها، بلا مقدمة ولا عبرة.",
    "narrative": (
        "سرد قصصي مترابط في فقرتين إلى أربع فقرات قصيرة: السياق أولًا، ثم الأحداث بترتيبها، "
        "ثم جملة أخيرة قصيرة بالعبرة إن دلّت عليها المقاطع."
    ),
    "general": "إجابة واضحة في فقرة أو فقرتين، بلا عبرة أو موعظة في آخرها.",
}

_CITATION_RE = re.compile(r"\s*\[(\d{1,2}(?:\s*[,،و]\s*\d{1,2})*)\]")
_QUOTE_RE = re.compile(r"«([^»]{8,})»|\"([^\"]{8,})\"|“([^”]{8,})”|﴿([^﴾]{8,})﴾|\{([^}]{8,})\}")
_SENTENCE_RE = re.compile(r"(?<=[.!?؟])\s+")
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_PUNCT_RE = re.compile(r"[^\w\s]")


@dataclass
class ComposedAnswer:
    text: str
    cited: list[int] = field(default_factory=list)  # 1-based evidence numbers, in order of use
    model: str | None = None
    insufficient: bool = False


def _evidence_block(index: int, item: dict) -> str:
    label = item.get("title") or item.get("source") or "مصدر"
    if item.get("page"):
        label += f"، ص {item['page']}"
    if item.get("heading"):
        label += f" \N{EM DASH} {item['heading']}"
    text = remove_diacritics(item.get("text") or item.get("snippet") or "").strip()
    return f"[{index}] {label}\n{text}"


def fit_evidence(evidence: list[dict], model: str) -> list[dict]:
    """The passages that fit this model's context window, best first."""
    profile = model_profile(model)
    chosen, used = [], 0
    for item in evidence[: profile.max_passages]:
        size = len(item.get("text") or "")
        if chosen and used + size > profile.evidence_chars:
            break
        chosen.append(item)
        used += size
    return chosen


def build_messages(question: str, evidence: list[dict], mode: str, station: str | None) -> list[dict]:
    lines = [f"سؤال الزائر: {question.strip()}"]
    if station:
        lines.append(f"الزائر يتصفح الآن صفحة محطة: {station.strip()} (إذا قال «المحطة» أو «هنا» فهذه هي المقصودة).")
    lines.append(f"المطلوب: {MODE_HINTS.get(mode, MODE_HINTS['general'])}")
    lines.append("")
    lines.append("المقاطع:")
    lines.append("\n\n".join(_evidence_block(i, item) for i, item in enumerate(evidence, 1)))
    lines.append("")
    lines.append("اكتب الإجابة الآن مع أرقام المقاطع بين معقوفين بعد كل معلومة.")
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(lines)},
    ]


def _comparable(text: str) -> str:
    return " ".join(_PUNCT_RE.sub(" ", normalize(text)).split())


def _quotes_are_grounded(sentence: str, evidence_text: str) -> bool:
    for match in _QUOTE_RE.finditer(sentence):
        quoted = next(group for group in match.groups() if group)
        if len(quoted.split()) < 4:
            continue
        if _comparable(quoted) not in evidence_text:
            return False
    return True


def _strip_markdown(text: str) -> str:
    text = _THINK_RE.sub("", text)
    text = re.sub(r"\*\*|__|`", "", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*[\*•]\s+", "- ", text)
    return text.strip()


def _trim_incomplete(text: str) -> str:
    last = max(text.rfind(mark) for mark in (".", "!", "؟", "?"))
    return text[: last + 1] if last != -1 else text


def finalize_answer(raw: str, evidence: list[dict], finish_reason: str | None = None) -> ComposedAnswer:
    text = _strip_markdown(raw or "")

    if finish_reason == "length":
        text = _trim_incomplete(text)

    if not text or normalize(text).startswith(ABSTAIN_START):
        return ComposedAnswer(INSUFFICIENT_ANSWER, insufficient=True)

    evidence_text = _comparable(" ".join(item.get("text") or "" for item in evidence))
    cited: list[int] = []
    paragraphs = []

    for paragraph in re.split(r"\n\s*\n", text):
        lines = []
        # Lines inside a paragraph (e.g. a list of places) stay on their own line.
        for line in paragraph.strip().splitlines():
            kept = []
            for sentence in _SENTENCE_RE.split(line.strip()):
                sentence = sentence.strip()
                if not sentence:
                    continue
                # The abstention sentence appended after a real answer.
                if normalize(sentence).startswith(ABSTAIN_START):
                    continue
                if not _quotes_are_grounded(sentence, evidence_text):
                    continue
                for group in _CITATION_RE.findall(sentence):
                    for number in re.findall(r"\d+", group):
                        number = int(number)
                        if 1 <= number <= len(evidence) and number not in cited:
                            cited.append(number)
                clean = _CITATION_RE.sub("", sentence)
                clean = re.sub(r"\s+([.،,!?؟:؛])", r"\1", clean).strip()
                if clean and clean not in ("-", "•"):
                    kept.append(clean)
            if kept:
                lines.append(" ".join(kept))
        if lines:
            paragraphs.append("\n".join(lines))

    if not paragraphs:
        return ComposedAnswer(INSUFFICIENT_ANSWER, insufficient=True)

    return ComposedAnswer("\n\n".join(paragraphs), cited=cited)


def compose_answer(
    question: str,
    evidence: list[dict],
    mode: str = "general",
    station: str | None = None,
) -> ComposedAnswer:
    """Ask the model, then clean and check its answer.

    Raises llm.LLMUnavailable when no model can be reached.
    """
    if not evidence:
        return ComposedAnswer(INSUFFICIENT_ANSWER, insufficient=True)

    used: dict[str, list[dict]] = {}

    def messages_for(model: str) -> list[dict]:
        used[model] = fit_evidence(evidence, model)
        return build_messages(question, used[model], mode, station)

    def answer_tokens(model: str) -> int:
        profile = model_profile(model)
        return profile.brief_tokens if mode == "brief" else profile.narrative_tokens

    # Temperature 0: the same passages give the same, most careful wording.
    completion: Completion = complete(messages_for, answer_tokens=answer_tokens, temperature=0.0)
    result = finalize_answer(completion.text, used[completion.model], completion.finish_reason)
    result.model = completion.model
    return result


def generate_answer(question: str, sources: list[dict]) -> str:
    """Older interface: the answer text only."""
    return compose_answer(question, sources).text
