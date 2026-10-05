from backend.app.rag.hybrid_retriever import hybrid_retrieve
from backend.app.rag.generator import generate_answer


def test_birth_date_regression():
    question = "\u0645\u062a\u0649 \u0648\u0644\u062f \u0627\u0644\u0631\u0633\u0648\u0644 \u0645\u062d\u0645\u062f\u061f"

    sources = hybrid_retrieve(
        question,
        top_k=2,
        candidate_k=200,
    )

    answer = generate_answer(question, sources)

    assert "571" in answer, answer
    assert "\u0627\u0644\u0627\u062b\u0646\u064a\u0646" in answer or "\u0627\u0644\u0625\u062b\u0646\u064a\u0646" in answer, answer
    assert "\u0645\u062d\u0645\u062f \u0637\u0644\u0639\u062a" not in answer, answer
    assert "\u062b\u0645 \u0647\u0627\u062c\u0631" not in answer, answer
    assert "\u062e\u0645\u0633\u064a\u0646 \u0633\u0646\u0629" not in answer, answer


def test_makkah_importance_retrieval():
    question = "\u0645\u0627 \u0623\u0647\u0645\u064a\u0629 \u0645\u0643\u0629 \u0641\u064a \u0628\u062f\u0627\u064a\u0629 \u0627\u0644\u062f\u0639\u0648\u0629\u061f"

    sources = hybrid_retrieve(
        question,
        top_k=2,
        candidate_k=200,
    )

    assert sources, "No sources returned"

    top_text = sources[0]["snippet"]

    assert "\u0645\u0643\u0629" in top_text, top_text
    assert "\u0645\u0631\u0643\u0632 \u062f\u064a\u0646 \u0627\u0644\u0639\u0631\u0628" in top_text, top_text
    assert "\u0627\u0644\u0643\u0639\u0628\u0629" in top_text, top_text
    assert "\u0627\u0644\u062f\u0639\u0648\u0629" in top_text, top_text


if __name__ == "__main__":
    test_birth_date_regression()
    test_makkah_importance_retrieval()
    print("PASS: guide regression tests")
