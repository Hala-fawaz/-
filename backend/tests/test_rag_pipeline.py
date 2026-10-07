"""End-to-end tests of the guide's knowledge-base answers, with a fake model."""

import os
import tempfile
import unittest
from pathlib import Path

from rag_fixtures import FakeGroq, write_fixture_sources

from app.rag import fts_builder, fts_retriever, llm, pipeline
from app.rag.generator import INSUFFICIENT_ANSWER, finalize_answer


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        folder = Path(cls.tmp.name)
        cls.sources = write_fixture_sources(folder)
        cls.db_path = folder / "index" / "knowledge_fts.db"
        cls.stats = fts_builder.build_fts_index(cls.sources, cls.db_path, verbose=False)
        cls.saved_db = fts_retriever.DB_PATH
        fts_retriever.DB_PATH = cls.db_path

    @classmethod
    def tearDownClass(cls):
        fts_retriever.DB_PATH = cls.saved_db
        llm.set_client(None)
        cls.tmp.cleanup()

    def setUp(self):
        self.env = {key: os.environ.get(key) for key in ("GROQ_MODEL", "GROQ_FALLBACK_MODEL", "RAG_VERIFY_ANSWERS")}
        os.environ["GROQ_MODEL"] = "openai/gpt-oss-120b"
        os.environ["GROQ_FALLBACK_MODEL"] = "allam-2-7b"
        os.environ["RAG_VERIFY_ANSWERS"] = "0"

    def tearDown(self):
        for key, value in self.env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        llm.set_client(None)

    def ask(self, question, replies, station=None):
        fake = FakeGroq(replies)
        llm.set_client(fake)
        return pipeline.answer_question(question, station=station, debug=True), fake

    def test_index_build(self):
        self.assertEqual(self.stats["version"], fts_builder.INDEX_VERSION)
        self.assertIn("كتاب مشكول copy/001.txt", self.stats["skipped_duplicates"])
        self.assertTrue(fts_builder.index_is_ready(self.db_path))

    def test_badr_narrative_question(self):
        reply = (
            "خرج النبي ﷺ في رمضان لاعتراض عير قريش [1]. ثم نصر الله المؤمنين يوم الفرقان [2].\n\n"
            "وفي ذلك درس في الثقة بالله [2]."
        )
        result, fake = self.ask("ماذا حدث في غزوة بدر؟", {"openai/gpt-oss-120b": reply})

        prompt = fake.prompt()
        self.assertIn("بدر", prompt)
        self.assertIn("سرد قصصي", prompt)                     # narrative mode hint
        self.assertIn("راوي رِسالة", fake.calls[0]["messages"][0]["content"])
        self.assertNotIn("[1]", result["answer"])            # citations removed from the text
        self.assertIn("\n\n", result["answer"])              # paragraphs kept
        self.assertTrue(result["sources"])
        self.assertTrue(all("/" not in s["source"] for s in result["sources"]))
        self.assertEqual(result["debug"]["model"], "openai/gpt-oss-120b")

    def test_vocalized_text_is_searchable(self):
        result, fake = self.ask("متى كانت وقعة بدر؟", {"*": "كانت يوم الجمعة السابع عشر من رمضان [1]."})
        titles = [item["title"] for item in result["debug"]["evidence"]]
        self.assertIn("كتاب مشكول - ج1", titles)

    def test_station_question(self):
        result, fake = self.ask(
            "ما الأماكن المهمة في المحطة؟",
            {"*": "من أماكنها بئر بدر والعدوة الدنيا والعريش [1]."},
            station="غزوة بدر — بدر",
        )
        self.assertIn("غزوة بدر", fake.prompt())
        self.assertIn("العريش", fake.prompt())
        self.assertTrue(result["answer"].startswith("من أماكنها"))

    def test_no_relevant_passage_means_no_model_call(self):
        result, fake = self.ask("ما عاصمة اليابان؟", {"*": "طوكيو"})
        self.assertEqual(result["answer"], INSUFFICIENT_ANSWER)
        self.assertEqual(fake.calls, [])

    def test_model_abstains(self):
        result, _ = self.ask("ماذا حدث في غزوة بدر؟", {"*": INSUFFICIENT_ANSWER})
        self.assertEqual(result["answer"], INSUFFICIENT_ANSWER)
        self.assertEqual(result["sources"], [])

    def test_fallback_model_when_primary_fails(self):
        result, fake = self.ask(
            "ماذا حدث في غزوة أحد؟",
            {"openai/gpt-oss-120b": RuntimeError("rate limited"), "allam-2-7b": "جعل النبي ﷺ الرماة على الجبل [1]."},
        )
        self.assertEqual([call["model"] for call in fake.calls], ["openai/gpt-oss-120b", "allam-2-7b"])
        self.assertEqual(result["debug"]["model"], "allam-2-7b")
        self.assertIn("الرماة", result["answer"])

    def test_both_models_down(self):
        result, _ = self.ask("ماذا حدث في غزوة أحد؟", {"*": RuntimeError("down")})
        self.assertEqual(result["status"], "llm_unavailable")
        self.assertEqual(result["answer"], pipeline.BUSY_ANSWER)
        self.assertTrue(result["sources"])

    def test_verifier_reply_from_the_report_keeps_the_answer(self):
        os.environ["RAG_VERIFY_ANSWERS"] = "1"
        answer = "خرج النبي ﷺ لاعتراض العير [1]. ونصر الله المؤمنين [2]."
        result, fake = self.ask("ماذا حدث في غزوة بدر؟", {
            "openai/gpt-oss-120b": [answer, "ACCEPTED SENTENCES:\n1,2\n\nThese sentences are accepted because"],
        })
        self.assertEqual(len(fake.calls), 2)
        self.assertEqual(result["answer"], "خرج النبي ﷺ لاعتراض العير. ونصر الله المؤمنين.")

    def test_greeting(self):
        result, fake = self.ask("السلام عليكم", {"*": "x"})
        self.assertIn("راوي رِسالة", result["answer"])
        self.assertEqual(fake.calls, [])

    def test_small_context_model_gets_fewer_passages(self):
        os.environ["GROQ_MODEL"] = "allam-2-7b"
        os.environ["GROQ_FALLBACK_MODEL"] = "none"
        _, fake = self.ask("ماذا حدث في غزوة بدر؟", {"allam-2-7b": "نصر الله المؤمنين [1]."})
        self.assertLessEqual(fake.prompt().count("\n["), 4)
        self.assertLessEqual(fake.calls[0]["max_tokens"], 700)
        self.assertNotIn("extra_body", fake.calls[0])

    def test_missing_index(self):
        saved = fts_retriever.DB_PATH
        started = []
        original = pipeline.ensure_index_async
        pipeline.ensure_index_async = lambda path=None: started.append(path)
        fts_retriever.DB_PATH = Path(self.tmp.name) / "missing" / "knowledge_fts.db"
        try:
            with self.assertRaises(fts_retriever.KnowledgeIndexNotReady):
                pipeline.answer_question("ماذا حدث في غزوة بدر؟")
            self.assertEqual(len(started), 1)
        finally:
            fts_retriever.DB_PATH = saved
            pipeline.ensure_index_async = original


class FinalizeTests(unittest.TestCase):
    evidence = [{"text": "قال الله تعالى: إذ تستغيثون ربكم فاستجاب لكم أني ممدكم بألف من الملائكة مردفين"}]

    def test_quote_found_in_evidence_is_kept(self):
        raw = "ونزل قوله تعالى: «إِذْ تَسْتَغِيثُونَ رَبَّكُمْ فَاسْتَجَابَ لَكُمْ» [1]."
        result = finalize_answer(raw, self.evidence)
        self.assertIn("«إِذْ تَسْتَغِيثُونَ", result.text)
        self.assertEqual(result.cited, [1])

    def test_invented_quote_is_dropped(self):
        raw = "انتصر المسلمون [1]. وقال تعالى: «وَلَقَدْ نَصَرَكُمُ اللَّهُ بِبَدْرٍ وَأَنْتُمْ أَذِلَّةٌ» [1]."
        result = finalize_answer(raw, self.evidence)
        self.assertEqual(result.text, "انتصر المسلمون.")

    def test_markdown_and_cut_off_sentence(self):
        raw = "**غزوة بدر**: كانت في رمضان [1]. ثم بدأت المعركة وكان"
        result = finalize_answer(raw, self.evidence, finish_reason="length")
        self.assertEqual(result.text, "غزوة بدر: كانت في رمضان.")


if __name__ == "__main__":
    unittest.main()
