import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

MODEL_NAME = "allam-2-7b"

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def _clean_answer(answer: str) -> str:
    answer = re.split(
        r"\n\s*(?:المصادر|المراجع|المصادر المستخدمة)\s*:?",
        answer,
        maxsplit=1,
    )[0]

    answer = re.sub(r"\s+", " ", answer).strip()

    sentences = re.split(r"(?<=[.!؟])\s+", answer)

    unique = []
    seen = set()

    for sentence in sentences:
        normalized = re.sub(r"\W+", "", sentence)

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        unique.append(sentence.strip())

        if len(unique) >= 3:
            break

    return " ".join(unique).strip()


def _extract_when_answer(question: str, sources: list[dict]):
    if "\u0645\u062a\u0649" not in question:
        return None

    birth_pattern = re.compile(r"(?:\u0648\u0644\u062f|\u0645\u064a\u0644\u0627\u062f|\u0648\u0644\u0627\u062f)")
    time_pattern = re.compile(r"(?:\u0639\u0627\u0645|\u0633\u0646\u0629|\u064a\u0648\u0645|\u0627\u0644\u0627\u062b\u0646\u064a\u0646|\u0631\u0628\u064a\u0639|\d{2,4}|[\u0660-\u0669]{2,4})")
    picks = []

    for source in sources[:3]:
        text = (source.get("snippet") or source.get("text", "")).replace("[", "").replace("]", "")
        for part in re.split(r"(?<=[.!?\u061f])\s+|\n+", text):
            part = " ".join(part.split()).strip(" .")
            if part and birth_pattern.search(part) and time_pattern.search(part):
                picks.append(part)
                break

    unique = []
    for part in picks:
        if part not in unique:
            unique.append(part)

    if not unique:
        return None

    cleaned_unique = []
    for part in unique:
        part = re.split(
            r"(?:\u0648\u0642\u062f\s+\u0631\u062c\u0651?\u062d|\u062b\u0645\s+\u0647\u0627\u062c\u0631|\u0648\u062a\u0648\u0641\u064a|\u0648\u0639\u0627\u0634|\u0648\u0628\u0642\u0649)",
            part,
            maxsplit=1,
        )[0].strip(" ,.")

        if part:
            cleaned_unique.append(part)

    return ". ".join(cleaned_unique[:1]) + "."

def generate_answer(question: str, sources: list[dict]) -> str:
    if not sources:
        return "لا توجد معلومات كافية في المصادر المتاحة للإجابة عن هذا السؤال."

    strict_answer = _extract_when_answer(question, sources)
    if strict_answer:
        return strict_answer

    context_parts = []

    for i, source in enumerate(sources[:10], 1):
        text = source.get("snippet") or source.get("text", "")
        text = text.replace("[", "").replace("]", "").strip()

        context_parts.append(
            f"""المصدر {i}
النص: {text}"""
        )

    context = "\n\n".join(context_parts)

    system_prompt = """
أنت المرشد المعرفي لمنصة رسالة.
أجب باللغة العربية اعتمادًا فقط على النصوص المقدمة.
اكتب فقرة واحدة طبيعية ومباشرة من جملتين إلى 3 جمل.
لا تكرر أي معلومة.
ركز على المطلوب في السؤال فقط، وتجاهل التفاصيل الجانبية التي لا تجيب عنه مباشرة.
إذا كان السؤال عن الأهمية أو السبب، لخّص الدور العام ولا تذكر أمثلة جزئية أو أسماء أشخاص أو قبائل إلا إذا طلبها السؤال.
لا تحول الإجابة إلى تسلسل أحداث إذا كان السؤال يطلب أهمية أو سببًا.
لا تستنتج معلومات غير واضحة من النصوص.
لا تكتب قائمة مصادر أو مراجع.
لا تخترع معلومات غير موجودة في النصوص.
إذا لم تكفِ المعلومات، قل بوضوح إن المعلومات المتاحة لا تكفي.
لا تصدر فتاوى أو أحكامًا شرعية شخصية.

في الأسئلة الواقعية مثل: متى، أين، من، كم، التزم بالمعلومة الواردة نصًا في المصادر ولا تستنتج تاريخًا أو رقمًا من عندك.
لا تذكر أي سنة أو رقم أو مدة زمنية إلا إذا وردت صراحة في النصوص المقدمة.
إذا اختلفت المصادر في التاريخ أو الرقم، اذكر بوضوح أن هناك اختلافًا واعرض الأقوال الموجودة في النصوص دون ترجيح من عندك.
إذا ورد في النص عام الفيل فلا تحوله إلى سنة ميلادية إلا إذا ذكرت السنة الميلادية صراحة في أحد النصوص.
لا تقم بأي عملية حسابية أو تحويل زمني اعتمادًا على النصوص.
إذا كان السؤال يطلب تاريخًا دقيقًا ولم تتفق النصوص عليه، اذكر أشهر قول موجود في المصادر ثم وضح وجود الخلاف.
ابدأ مباشرة بالإجابة.
""".strip()

    user_prompt = f"""السؤال:
{question}

النصوص الموثقة:
{context}

الإجابة فقط:
""".strip()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        max_tokens=110,
    )

    answer = response.choices[0].message.content

    if not answer:
        return "تعذر إنشاء إجابة من المصادر المتاحة."

    return _clean_answer(answer)

