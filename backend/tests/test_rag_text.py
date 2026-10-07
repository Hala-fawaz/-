"""Unit tests for Arabic normalization, query planning and reply parsing.

Run from the repository root or from backend/:
    python -m pytest backend/tests        (or)   python -m unittest discover backend/tests
"""

import unittest

import rag_fixtures  # noqa: F401  (puts backend/ on sys.path)

from app.rag.arabic_text import index_text, normalize, strip_prefix, term_alternatives
from app.rag.fts_retriever import plan_query
from app.rag.llm import parse_accept_ids


class NormalizeTests(unittest.TestCase):
    def test_diacritics_are_removed(self):
        # The old index kept harakat and split «بَدْرٍ» into ب / د / ر.
        self.assertEqual(normalize("بَدْرٍ"), "بدر")
        self.assertEqual(normalize("غَزْوَةُ"), "غزوه")

    def test_letter_forms_are_unified(self):
        self.assertEqual(normalize("إبراهيم"), "ابراهيم")
        self.assertEqual(normalize("أحد"), "احد")
        self.assertEqual(normalize("غزوة"), normalize("غزوه"))
        self.assertEqual(normalize("٦٢٤"), "624")

    def test_alef_maqsura_is_kept(self):
        # «على» (on) must not become «علي» (the name).
        self.assertEqual(normalize("على"), "على")

    def test_ligature_and_invisible_marks(self):
        self.assertEqual(normalize("ﷺ"), "صلى الله عليه وسلم")
        self.assertEqual(normalize("\N{ZERO WIDTH NON-JOINER}المدخل"), "المدخل")

    def test_prefixes(self):
        self.assertEqual(strip_prefix("وبالمدينه"), "مدينه")
        self.assertEqual(strip_prefix("للهجره"), "هجره")
        self.assertEqual(strip_prefix("الله"), "الله")
        self.assertEqual(strip_prefix("بدر"), "بدر")

    def test_index_text_adds_variants(self):
        indexed = index_text("فلما كان ببدر بدرًا").split()
        self.assertIn("ببدر", indexed)
        self.assertGreaterEqual(indexed.count("بدر"), 2)

    def test_query_alternatives(self):
        self.assertEqual(term_alternatives("غزوة"), ["غزوه", "غزو*"])
        self.assertIn("موسى", term_alternatives("موسي"))
        self.assertIn("هجره", term_alternatives("الهجرة"))


class PlanTests(unittest.TestCase):
    def test_question_verb_is_not_required(self):
        # The old retriever required «حدث» in the passage.
        plan = plan_query("ماذا حدث في غزوة بدر؟")
        self.assertEqual([g.word for g in plan.hard], ["بدر"])
        self.assertEqual([g.word for g in plan.soft], ["غزوه"])
        self.assertEqual(plan.mode, "narrative")

    def test_colloquial_question(self):
        plan = plan_query("وش صار في بدر؟")
        self.assertEqual([g.word for g in plan.required], ["بدر"])
        self.assertEqual(plan.mode, "narrative")

    def test_brief_question_types(self):
        self.assertEqual(plan_query("متى كانت غزوة بدر؟").answer_type, "when")
        self.assertEqual(plan_query("كم عدد المسلمين في بدر؟").answer_type, "how_many")
        self.assertEqual(plan_query("متى كانت غزوة بدر؟").mode, "brief")
        self.assertEqual(plan_query("ما الأماكن المهمة في المحطة؟", station="غزوة بدر").answer_type, "where")

    def test_word_families(self):
        alternatives = plan_query("متى ولد النبي؟").hard[0].alternatives
        self.assertIn("مولد*", alternatives)

    def test_kunya_forms(self):
        plan = plan_query("ما موقف أبي طالب؟")
        kunya = [g for g in plan.soft if g.word == "ابي"][0]
        self.assertEqual(set(kunya.alternatives), {"ابو", "ابي", "ابا"})
        self.assertEqual([g.word for g in plan.hard], ["طالب"])

    def test_station_pointer_requires_station_words(self):
        plan = plan_query("ما الأماكن المهمة في المحطة؟", station="غزوة بدر — بدر")
        self.assertTrue(plan.station_required)
        self.assertEqual([g.word for g in plan.required], ["بدر"])

    def test_station_is_only_a_hint_otherwise(self):
        plan = plan_query("من هي خديجة؟", station="غزوة بدر — بدر")
        self.assertFalse(plan.station_required)
        self.assertEqual([g.word for g in plan.required], ["خديجه"])


class ParseAcceptTests(unittest.TestCase):
    def test_reply_that_broke_the_old_parser(self):
        # Raw allam-2-7b reply recorded in rag-report.md.
        reply = "ACCEPTED SENTENCES:\n1,2,3,4,5,6\n\nThese sentences are accepted because they directly address"
        self.assertEqual(parse_accept_ids(reply, 6), {1, 2, 3, 4, 5, 6})

    def test_reply_with_explanation(self):
        reply = "ACCEPT: 1,3,8\n\nThe relevant evidence claims ... These items are:\n\n1. غزوة بدر"
        self.assertEqual(parse_accept_ids(reply, 8), {1, 3, 8})

    def test_none_and_unreadable(self):
        self.assertEqual(parse_accept_ids("ACCEPT: NONE", 3), set())
        self.assertIsNone(parse_accept_ids("All good.", 3))
        self.assertIsNone(parse_accept_ids("ACCEPT: 9", 3))


if __name__ == "__main__":
    unittest.main()
