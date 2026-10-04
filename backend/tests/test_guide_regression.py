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


if __name__ == "__main__":
    test_birth_date_regression()
    print("PASS: birth-date regression test")
