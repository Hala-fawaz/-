import re
import unicodedata


EVIDENCE_THRESHOLD = 0.12

STOP_WORDS = {
    "\u0645\u0646",
    "\u0641\u064a",
    "\u0639\u0644\u0649",
    "\u0627\u0644\u0649",
    "\u0639\u0646",
    "\u0645\u0627",
    "\u0645\u0627\u0630\u0627",
    "\u0647\u0648",
    "\u0647\u064a",
    "\u0643\u0627\u0646",
    "\u0643\u0627\u0646\u062a",
    "\u0643\u0645",
    "\u0645\u062a\u0649",
    "\u0627\u064a\u0646",
    "\u0643\u064a\u0641",
    "\u0644\u0645\u0627\u0630\u0627",
    "\u0647\u0644",
    "the",
    "a",
    "an",
    "of",
    "in",
    "on",
    "to",
    "is",
    "was",
    "were",
    "who",
    "what",
    "where",
    "when",
    "how",
    "why",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", text)

    replacements = {
        "\u0623": "\u0627",
        "\u0625": "\u0627",
        "\u0622": "\u0627",
        "\u0649": "\u064a",
        "\u0624": "\u0648",
        "\u0626": "\u064a",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text).strip().lower()
    return text

def _tokens(text: str) -> list[str]:
    text = _normalize(text)

    tokens = re.findall(
        r"[a-z0-9]+|[\u0621-\u063A\u0641-\u064A]+",
        text,
    )

    normalized_stop_words = {
        _normalize(word)
        for word in STOP_WORDS
    }

    return [
        token
        for token in tokens
        if len(token) > 1
        and token not in normalized_stop_words
    ]

def _minimum_term_span_tokens(doc_tokens: list[str], query_terms: list[str]) -> int:
    if not doc_tokens or not query_terms:
        return 99999

    positions = []

    for term in set(query_terms):
        for index, token in enumerate(doc_tokens):
            if token == term:
                positions.append((index, term))

    if not positions:
        return 99999

    positions.sort()
    required = set(query_terms)
    counts = {}
    left = 0
    best = 99999

    for right, (position, term) in enumerate(positions):
        counts[term] = counts.get(term, 0) + 1

        while required.issubset(counts.keys()):
            best = min(best, positions[right][0] - positions[left][0])

            left_term = positions[left][1]
            counts[left_term] -= 1

            if counts[left_term] == 0:
                del counts[left_term]

            left += 1

    return best



def _question_type(question: str) -> str:
    q = _normalize(question)
    words = set(re.findall(r"[a-z0-9\u0600-\u06FF]+", q))

    if {"\u0627\u064a\u0646", "\u0645\u0643\u0627\u0646", "\u0645\u0648\u0636\u0639"} & words:
        return "where"

    if {"\u0645\u062a\u0649", "\u0639\u0627\u0645", "\u0633\u0646\u0629", "\u064a\u0648\u0645", "\u0634\u0647\u0631"} & words:
        return "when"

    if "\u0643\u0645" in words:
        return "how_many"

    if {"\u0644\u0645\u0627\u0630\u0627", "\u0633\u0628\u0628"} & words:
        return "why"

    if "\u0645\u0646" in words:
        return "who"

    return "general"

def _intent_bonus(question: str, text: str) -> float:
    kind = _question_type(question)

    if kind == "general":
        return 0.0

    normalized_text = _normalize(text)
    query_tokens = _tokens(question)

    if not query_tokens:
        return 0.0

    # In Arabic WH questions the first content token is usually
    # the relation/predicate: ??? ???... / ??? ???... / ??? ???...
    anchor = query_tokens[0]

    positions = [
        match.start()
        for match in re.finditer(
            rf"(?<!\w){re.escape(anchor)}(?!\w)",
            normalized_text,
        )
    ]

    if not positions:
        return 0.0

    windows = [
        normalized_text[
            max(0, position - 25):
            min(len(normalized_text), position + 125)
        ]
        for position in positions
    ]

    if kind == "where":
        temporal_or_nonplace = {
            "\u0639\u0627\u0645",
            "\u0633\u0646\u0629",
            "\u0633\u0646",
            "\u064a\u0648\u0645",
            "\u0634\u0647\u0631",
            "\u0646\u0635\u0641",
            "\u0631\u0645\u0636\u0627\u0646",
            "\u0647\u062c\u0631\u0629",
            "\u0627\u0644\u0647\u062c\u0631\u0629",
            "\u0627\u0633\u0644\u0627\u0645",
            "\u0627\u0644\u0627\u0633\u0644\u0627\u0645",
            "\u0639\u0647\u062f",
            "\u0627\u0644\u0639\u0647\u062f",
            "\u062d\u064a\u0627\u0629",
            "\u0632\u0645\u0646",
            "\u0648\u0642\u062a",
            "\u062d\u064a\u0646",
            "\u0642\u0628\u0644",
            "\u0628\u0639\u062f",
            "\u0645\u062f\u0629",
        }

        bad_b_targets = {
            "\u0639\u062f",      # ???
            "\u0639\u0636",      # ???
            "\u064a\u0646",      # ???
            "\u062f\u0648\u0646",    # ????
            "\u0633\u0628\u0628",    # ????
            "\u0634\u0643\u0644",    # ????
            "\u0641\u0636\u0644",    # ????
            "\u0627\u0632\u064a\u062f",   # ?????
            "\u0627\u0643\u062b\u0631",   # ?????
            "\u0627\u0642\u0644",    # ????
            "\u0642\u062f\u0631",
            "\u0646\u0641\u0633",
            "\u0647\u0630\u0627",
            "\u0647\u0630\u0647",
            "\u0647",
            "\u0647\u0627",
            "\u0647\u0645",
            "\u0647\u0645\u0627",
        }

        for position in positions:
            after_anchor = normalized_text[
                position:
                min(len(normalized_text), position + 90)
            ]

            # Relation + explicit "??" + probable place.
            match = re.search(
                rf"(?<!\w){re.escape(anchor)}(?!\w)"
                rf"(?:\s+\S+){{0,1}}\s+\u0641\u064a\s+"
                rf"([\u0621-\u063A\u0641-\u064A]{{2,}})",
                after_anchor,
            )

            if match:
                target = match.group(1)

                if not any(
                    target == word or target.startswith(word)
                    for word in temporal_or_nonplace
                ):
                    return 0.34

            # Relation + Arabic ? prefix: ??? ????? ???? ????????...
            match = re.search(
                rf"(?<!\w){re.escape(anchor)}(?!\w)"
                rf"\s+\u0628"
                rf"([\u0621-\u063A\u0641-\u064A]{{2,}})",
                after_anchor,
            )

            if match:
                target = match.group(1)

                temporal_b_stems = (
                    "\u0639\u062f",      # ??? / ????
                    "\u0633\u0646",      # ??? / ?????
                    "\u0634\u0647\u0631",
                    "\u064a\u0648\u0645",
                    "\u0639\u0627\u0645",
                    "\u0639\u0634\u0631",
                    "\u062e\u0645\u0633",
                    "\u0627\u0631\u0628\u0639",
                    "\u062b\u0644\u0627\u062b",
                    "\u0633\u0628\u0639",
                    "\u062d\u064a\u0646",
                    "\u0642\u0628\u0644",
                    "\u0639\u0647\u062f",
                    "\u062d\u064a\u0627\u0629",
                    "\u0648\u0642\u062a",
                    "\u0645\u062f\u0629",
                )

                blocked = any(
                    target == word or target.startswith(word)
                    for word in bad_b_targets
                ) or any(
                    target.startswith(stem)
                    for stem in temporal_b_stems
                )

                if not blocked:
                    return 0.34

            # Explicit location wording close to the relation.
            if re.search(
                r"(?:\u0645\u0643\u0627\u0646|\u0645\u0648\u0636\u0639|"
                r"\u0645\u062f\u064a\u0646\u0629|\u0642\u0631\u064a\u0629|"
                r"\u0628\u0644\u062f|\u062f\u0627\u0631)",
                after_anchor[:70],
            ):
                return 0.20


    if kind == "when":
        pattern = (
            r"(?:\d{2,4}|\u0639\u0627\u0645|\u0633\u0646\u0629|"
            r"\u064a\u0648\u0645|\u0634\u0647\u0631|\u0647\u062c\u0631\u064a|"
            r"\u0645\u064a\u0644\u0627\u062f\u064a)"
        )

        if any(re.search(pattern, window) for window in windows):
            return 0.30

    if kind == "how_many":
        if any(re.search(r"\d+", window) for window in windows):
            return 0.30

    if kind == "why":
        pattern = (
            r"(?:\u0644\u0627\u0646|\u0628\u0633\u0628\u0628|"
            r"\u0633\u0628\u0628|\u0644\u0643\u064a)"
        )

        if any(re.search(pattern, window) for window in windows):
            return 0.26

    if kind == "who":
        pattern = (
            r"(?:\u0647\u0648|\u0647\u064a|\u0627\u0633\u0645\u0647|"
            r"\u064a\u062f\u0639\u0649|\u064a\u0639\u0631\u0641)"
        )

        if any(re.search(pattern, window) for window in windows):
            return 0.18

    return 0.0

def _score(question: str, text: str) -> float:
    query_tokens = _tokens(question)
    doc_tokens = _tokens(text)

    if not query_tokens or not doc_tokens:
        return 0.0

    query_set = set(query_tokens)
    doc_set = set(doc_tokens)

    matched = query_set & doc_set
    coverage = len(matched) / max(len(query_set), 1)

    normalized_question = _normalize(question)
    normalized_text = _normalize(text)

    phrase_bonus = 1.0 if normalized_question and normalized_question in normalized_text else 0.0

    span = _minimum_term_span_tokens(doc_tokens, list(matched))

    if span == 99999:
        proximity = 0.0
    elif span <= 8:
        proximity = 1.0
    elif span <= 20:
        proximity = 0.65
    elif span <= 40:
        proximity = 0.35
    else:
        proximity = 0.10

    density = min(
        1.0,
        len(matched) / max(min(len(doc_set), 30), 1)
    )

    base_score = (
        0.70 * coverage
        + 0.15 * proximity
        + 0.10 * phrase_bonus
        + 0.05 * density
    )

    intent_bonus = _intent_bonus(question, text)
    question_kind = _question_type(question)

    # For typed questions such as where/when/how-many/why,
    # matching the requested answer type matters more than
    # merely repeating the query words.
    if question_kind != "general":
        if intent_bonus > 0:
            intent_strength = min(1.0, intent_bonus / 0.34)
            return min(
                0.99,
                (0.62 * base_score) + (0.38 * intent_strength),
            )

        return 0.55 * base_score

    return min(1.0, base_score)


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 180):
    text = " ".join((text or "").split())

    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(0, end - overlap)

    return chunks


def semantic_rerank(
    question: str,
    candidates: list[dict],
    top_k: int = 10,
    max_chunks: int = 400,
):
    if not candidates:
        return []

    groups = []

    for item in candidates:
        source_text = item.get("text") or item.get("snippet") or ""
        chunks = chunk_text(source_text)

        group = []

        for chunk in chunks:
            enriched = dict(item)
            enriched["snippet"] = chunk
            enriched["semantic_score"] = _score(question, chunk)
            group.append(enriched)

        if group:
            groups.append(group)

    chunk_candidates = []

    round_index = 0

    while len(chunk_candidates) < max_chunks:
        added = False

        for group in groups:
            if round_index < len(group):
                chunk_candidates.append(group[round_index])
                added = True

                if len(chunk_candidates) >= max_chunks:
                    break

        if not added:
            break

        round_index += 1

    chunk_candidates.sort(
        key=lambda item: item["semantic_score"],
        reverse=True,
    )

    return chunk_candidates[:top_k]


def _minimum_term_span(text: str, terms: list[str]) -> int:
    doc_tokens = _tokens(text)
    normalized_terms = []

    for term in terms:
        normalized_terms.extend(_tokens(term))

    return _minimum_term_span_tokens(doc_tokens, normalized_terms)


def has_sufficient_evidence(
    results: list[dict],
    question_terms: list[str] | None = None,
) -> bool:
    if not results:
        return False

    best = results[0]
    semantic_score = best.get("semantic_score", 0.0)

    if semantic_score < EVIDENCE_THRESHOLD:
        return False

    if not question_terms:
        return True

    text = best.get("snippet") or best.get("text") or ""
    normalized_text = _normalize(text)

    normalized_terms = []

    for term in question_terms:
        pieces = _tokens(term)
        normalized_terms.extend(pieces)

    if not normalized_terms:
        return True

    matched_terms = [
        term for term in normalized_terms
        if term in normalized_text
    ]

    coverage = len(set(matched_terms)) / max(len(set(normalized_terms)), 1)

    if coverage < 0.60:
        return False

    if len(set(matched_terms)) >= 2:
        span = _minimum_term_span(text, list(set(matched_terms)))

        if span > 40:
            return False

    return True


def sentence_rerank(
    question: str,
    candidates: list[dict],
    top_k: int = 10,
    min_length: int = 35,
):
    if not candidates:
        return []

    sentence_candidates = []

    for item in candidates:
        text = item.get("snippet") or item.get("text") or ""

        parts = re.split(
            r"(?<=[.!?\u061f])\s+|\n+",
            text,
        )

        for part in parts:
            part = " ".join(part.split()).strip()

            if len(part) < min_length:
                continue

            enriched = dict(item)
            enriched["snippet"] = part

            local_score = _score(question, part)
            parent_score = float(
                item.get("semantic_score", local_score) or local_score
            )

            kind = _question_type(question)

            if kind != "general":
                intent_bonus = _intent_bonus(question, part)
                intent_strength = min(1.0, intent_bonus / 0.34)

                final_score = (
                    (0.55 * local_score)
                    + (0.35 * parent_score)
                    + (0.10 * intent_strength)
                )
            else:
                final_score = (
                    (0.70 * local_score)
                    + (0.30 * parent_score)
                )

            enriched["sentence_score"] = min(1.0, final_score)
            sentence_candidates.append(enriched)

    sentence_candidates.sort(
        key=lambda item: item["sentence_score"],
        reverse=True,
    )

    return sentence_candidates[:top_k]
