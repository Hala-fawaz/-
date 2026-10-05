import json
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from fastapi import HTTPException


MODEL_NAME = "MyMemory Translation API"

# هذا المثال يدعم العربية والإنجليزية فقط.
LANGUAGE_CODES = {
    "arb_Arab": "ar",
    "eng_Latn": "en",
    "ar": "ar",
    "en": "en",
}


def translate_text(text: str, source_language: str, target_language: str):
    source = LANGUAGE_CODES.get(source_language)
    target = LANGUAGE_CODES.get(target_language)

    if not source or not target:
        raise HTTPException(
            status_code=400,
            detail="رمز اللغة غير مضاف إلى خدمة الترجمة",
        )

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="اكتبي النص المراد ترجمته")

    # حد MyMemory في الطلب الواحد 500 بايت؛ النص العربي يستهلك بايتات أكثر.
    if len(text.encode("utf-8")) > 500:
        raise HTTPException(
            status_code=413,
            detail="النص أطول من الحد التجريبي لخدمة الترجمة",
        )

    query = urlencode({
        "q": text,
        "langpair": f"{source}|{target}",
    })
    url = f"https://api.mymemory.translated.net/get?{query}"

    try:
        with urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
    details = error.read().decode("utf-8", errors="replace")
    raise HTTPException(
        status_code=502,
        detail=f"MyMemory HTTP {error.code}: {details[:300]}",
    ) from error

except URLError as error:
    raise HTTPException(
        status_code=502,
        detail=f"MyMemory network error: {error.reason}",
    ) from error

except (TimeoutError, json.JSONDecodeError) as error:
    raise HTTPException(
        status_code=502,
        detail=f"تعذر إكمال طلب الترجمة: {error}",
    ) from error

    if data.get("responseStatus") != 200:
        raise HTTPException(
            status_code=502,
            detail=data.get("responseDetails") or "خدمة الترجمة لم تُرجع نتيجة",
        )

    result = data.get("responseData", {}).get("translatedText")
    if not result:
        raise HTTPException(status_code=502, detail="لم تصل ترجمة من الخدمة")

    return {
        "translation": result,
        "source_language": source_language,
        "target_language": target_language,
        "model": MODEL_NAME,
    }


