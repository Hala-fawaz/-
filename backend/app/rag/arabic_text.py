"""Arabic text normalization shared by the index builder and the retriever.

The index and the questions must go through the SAME normalization,
otherwise a word in the question and the same word in a book stop
matching. Everything here is deterministic and dependency-free.

What normalization does (in order):
1. NFKC: folds Arabic presentation forms into normal letters and
   expands the ligature ﷺ into «صلى الله عليه وسلم».
2. Removes invisible direction/joiner marks (the Shamela exports put
   U+200C before every heading).
3. Removes harakat, tanween, shadda, sukun, Quranic marks and tatweel,
   so «بَدْرٍ» and «بدر» become the same word. (The old index kept the
   harakat, and the SQLite tokenizer then split «بَدْرٍ» into ب / د / ر.)
4. Unifies alef forms (أ إ آ ٱ -> ا) and ta marbuta (ة -> ه),
   because people type «غزوه» and «اسلام» without hamza.
5. Converts Arabic-Indic digits to ASCII digits.

Alef maqsura (ى) is kept as written: folding it into ي would merge the
preposition «على» with the name «علي». Query expansion handles users
who type «موسي» for «موسى» instead (see term_alternatives).

Invisible and combining characters are written as \\U escapes in this
file on purpose, so no editor can silently drop them.
"""

import re
import unicodedata
from functools import lru_cache


# Zero-width spaces/joiners, direction marks and embeddings, BOM, soft hyphen.
_INVISIBLE_RE = re.compile(
    r"[\U0000200B-\U0000200F\U0000202A-\U0000202E\U00002066-\U00002069\U0000FEFF\U000000AD]"
)
# Quranic annotation signs, harakat/tanween/shadda/sukun, superscript alef,
# small high Quranic marks, and tatweel (ـ).
_DIACRITICS_RE = re.compile(
    r"[\U00000610-\U0000061A\U0000064B-\U0000065F\U00000670\U000006D6-\U000006ED\U00000640]"
)
_ALEF_FORMS_RE = re.compile(r"[أإآٱ]")
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_HAS_EASTERN_DIGITS = re.compile(r"[٠-٩۰-۹]")

# A token is a run of Arabic letters (ء..غ, ف..ي), or of Latin letters/digits.
_TOKEN_RE = re.compile(r"[ء-غف-ي]+|[a-z0-9]+")

# Attached particles that can precede a word: و ف ب ك ل and the
# article ال, alone or combined («وبالمدينة», «للهجرة»).
# Longest first so «وال» is tried before «و».
_PREFIXES = (
    "وبال", "فبال", "وكال", "فكال", "ولل", "فلل",
    "وال", "فال", "بال", "كال", "لل", "ال",
    "و", "ف", "ب", "ك", "ل",
)
_PREFIX_FIRST_LETTERS = frozenset(prefix[0] for prefix in _PREFIXES)

# A stripped word must keep at least this many letters; this protects
# short names such as «بدر» or «كعب» from being cut to «در» / «عب».
MIN_STEM = 3

# Feminine and plural endings (after normalization ة is ه). A query word
# ending in one of these is also searched as a prefix of its stem, so
# «غزوة» finds «غزوات» and «غزوته».
_STAR_SUFFIXES = ("ات", "ين", "ون", "ه")

_YA = "ي"
_ALEF_MAQSURA = "ى"
_ALEF = "ا"


def normalize(text: str) -> str:
    """Normalize Arabic text for searching (not for display)."""
    text = unicodedata.normalize("NFKC", text or "")
    text = _INVISIBLE_RE.sub("", text)
    text = _DIACRITICS_RE.sub("", text)
    text = _ALEF_FORMS_RE.sub(_ALEF, text)
    text = text.replace("ة", "ه")
    if _HAS_EASTERN_DIGITS.search(text):
        text = text.translate(_DIGITS)
    return text.lower()


def remove_diacritics(text: str) -> str:
    """Strip harakat and tatweel but keep the letters as written.

    Used for the text sent to the language model: fully vocalized
    books cost almost twice the tokens otherwise.
    """
    return _DIACRITICS_RE.sub("", text or "")


def tokenize(text: str) -> list[str]:
    """Split text into normalized word tokens."""
    return _TOKEN_RE.findall(normalize(text))


def strip_prefix(token: str) -> str:
    """Remove one attached particle/article if a real stem remains.

    «والمسلمين» -> «مسلمين», «ببدر» -> «بدر», «الله» stays «الله».
    """
    if not token or token[0] not in _PREFIX_FIRST_LETTERS:
        return token

    for prefix in _PREFIXES:
        if token.startswith(prefix) and len(token) - len(prefix) >= MIN_STEM:
            return token[len(prefix):]

    return token


@lru_cache(maxsize=400_000)
def index_variants(token: str) -> tuple[str, ...]:
    """Extra forms stored in the index next to the original token.

    The original token is always kept, so exact matches still work;
    the variants only add recall for attached particles («ببدر») and
    the accusative alef («بدرًا» -> «بدرا» -> «بدر»).
    """
    variants = []
    stripped = strip_prefix(token)

    if stripped != token:
        variants.append(stripped)

    for form in (token, stripped):
        if len(form) >= 4 and form.endswith(_ALEF):
            variants.append(form[:-1])

    return tuple(dict.fromkeys(variants))


@lru_cache(maxsize=400_000)
def _indexed_form(token: str) -> str:
    return " ".join((token, *index_variants(token)))


def index_text(text: str) -> str:
    """Normalized text plus variants, ready to insert into the FTS index."""
    return " ".join(map(_indexed_form, tokenize(text)))


def term_alternatives(token: str) -> list[str]:
    """Search forms for one query word.

    Returns plain words and prefix patterns ending in "*". The index
    already stores particle-stripped variants, so the bare stem of the
    query word is enough to reach «بالهجرة», «للهجرة», «والهجرة».
    """
    token = normalize(token)
    alternatives = [token]
    stem = strip_prefix(token)

    if stem != token:
        alternatives.append(stem)

    for form in (token, stem):
        # The user typed ي where the books write ى (or the reverse).
        if len(form) >= 4 and form.endswith(_YA):
            alternatives.append(form[:-1] + _ALEF_MAQSURA)
        elif len(form) >= 3 and form.endswith(_ALEF_MAQSURA):
            alternatives.append(form[:-1] + _YA)

    for suffix in _STAR_SUFFIXES:
        if stem.endswith(suffix) and len(stem) - len(suffix) >= MIN_STEM:
            alternatives.append(stem[: -len(suffix)] + "*")
            break

    return list(dict.fromkeys(alternatives))


def token_forms(token: str) -> tuple[str, ...]:
    """The token plus the variants the index stores for it."""
    return (token, *index_variants(token))


def forms_match(forms: tuple[str, ...], alternative: str) -> bool:
    """Does a token (given as its forms) satisfy one search alternative?

    Mirrors what the FTS index does, so the reranker and SQLite agree
    on what counts as a match.
    """
    if alternative.endswith("*"):
        prefix = alternative[:-1]
        return any(form.startswith(prefix) for form in forms)
    return alternative in forms
