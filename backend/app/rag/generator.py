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


def generate_answer(question: str, sources: list[dict]) -> str:
    if not sources:
        return "لا توجد معلومات كافية في المصادر المتاحة للإجابة عن هذا السؤال."

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

