"""Tests for turning source files into passages."""

import unittest

from rag_fixtures import JOURNEY_EVENTS, SEERAH_BOOK, VOCALIZED_VOLUME

from app.rag.source_parser import display_title, parse_shamela, parse_structured


class ShamelaTests(unittest.TestCase):
    def setUp(self):
        self.passages = parse_shamela(SEERAH_BOOK, "السيرة المختصرة.txt")

    def test_book_card_and_running_title_are_skipped(self):
        texts = "\n".join(p.text for p in self.passages)
        self.assertNotIn("الكتاب", texts.split("\n")[0])
        self.assertFalse(any(p.text.strip() == "السيرة المختصرة" for p in self.passages))
        self.assertFalse(any(p.text.endswith("السيرة المختصرة") for p in self.passages))

    def test_pages_and_breadcrumbs(self):
        by_page = {p.page: p for p in self.passages}
        self.assertEqual(by_page["1"].heading, "الهجرة إلى المدينة")
        # Page 3 never says «بدر» but sits inside the Badr chapter.
        self.assertIn("غزوة بدر الكبرى", by_page["3"].heading)
        self.assertIn("غزوة أحد", by_page["4"].heading)
        counts = [p for p in self.passages if p.page == "2"]
        self.assertTrue(any("عدد الجيشين" in p.heading and "غزوة بدر الكبرى" in p.heading for p in counts))

    def test_footnotes_and_marks_are_removed(self):
        page_two = " ".join(p.text for p in self.passages if p.page == "2")
        self.assertNotIn("ابن هشام 1/ 606", page_two)
        self.assertNotIn("«1»", page_two)

    def test_volume_title(self):
        self.assertEqual(display_title("كتاب مشكول/001.txt"), "كتاب مشكول - ج1")
        passages = parse_shamela(VOCALIZED_VOLUME, "كتاب مشكول/001.txt")
        self.assertEqual(passages[0].title, "كتاب مشكول - ج1")
        self.assertEqual(passages[0].page, "10")


class StructuredTests(unittest.TestCase):
    def test_stations(self):
        passages = parse_structured(JOURNEY_EVENTS, "journey-events.txt")
        headings = {p.heading for p in passages}
        self.assertIn("العهد المدني › المحطة 36: غزوة بدر الكبرى", headings)
        badr = [p for p in passages if "المحطة 36" in p.heading]
        self.assertEqual(badr[0].title, "رحلة الإسلام — المحطة 36: غزوة بدر الكبرى")
        self.assertIsNone(badr[0].page)
        self.assertIn("العريش", " ".join(p.text for p in badr))
        # The era description must not leak into a station.
        self.assertFalse(any("وصف المرحلة" in p.text for p in passages))


if __name__ == "__main__":
    unittest.main()
