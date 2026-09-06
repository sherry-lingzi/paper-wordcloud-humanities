"""Focused regression tests for the Scholar Portrait Chinese pipeline."""

from __future__ import annotations

import tempfile
from pathlib import Path
import subprocess
import sys
import unittest

import fitz

from arxiv_wordcloud import _get_documents_from_pdf_directory, export_frequencies
from humanities_text import PaperDocument, extract_abstract_and_keywords, is_reference_heading, remove_references
from tokenizer_zh import HumanitiesTokenizer, analyse_documents, default_stopwords, register_terms, tokenize


class HumanitiesProcessingTests(unittest.TestCase):
    def test_protected_multiword_term_is_not_split(self) -> None:
        terms = register_terms(["科学技术哲学"])
        self.assertIn("科学技术哲学", tokenize("科学技术哲学关注技术中介", terms, default_stopwords()))

    def test_academic_scaffolding_is_filtered_but_concepts_remain(self) -> None:
        words = tokenize("本文认为通过不同方面讨论主体存在世界实践", (), default_stopwords())
        self.assertFalse({"本文", "认为", "通过", "方面"} & set(words))
        self.assertTrue({"主体", "存在", "世界", "实践"}.issubset(words))

    def test_single_han_word_requires_protection(self) -> None:
        self.assertNotIn("人", tokenize("人、道、气、礼", (), default_stopwords()))
        protected = register_terms(["人"])
        self.assertIn("人", tokenize("人、道、气、礼", protected, default_stopwords()))

    def test_latin_names_and_acronyms_are_retained(self) -> None:
        words = tokenize("Foucault STS AI 与 Heidegger", (), default_stopwords())
        self.assertTrue({"FOUCAULT", "STS", "AI", "HEIDEGGER"}.issubset(words))

    def test_references_heading_is_trimmed_but_prose_is_not(self) -> None:
        self.assertEqual(remove_references(["正文", "相关参考文献表明", "结论"]), ["正文", "相关参考文献表明", "结论"])
        lines = ["正文" for _ in range(10)] + ["参考文献", "[1] 无关内容"]
        self.assertEqual(remove_references(lines), ["正文" for _ in range(10)])

    def test_reference_heading_variants_are_recognised(self) -> None:
        for heading in ("参考文献：", "[参考文献]", "【参考文献】", "（参考文献）", "5 参考文献",
                        "五、参考文献", "六 参考文献", "5. 参考文献", "REFERENCES", "References", "Bibliography"):
            with self.subTest(heading=heading):
                self.assertTrue(is_reference_heading(heading))

    def test_abstract_and_keywords_are_separated(self) -> None:
        body, abstract, keywords = extract_abstract_and_keywords("摘要：技术哲学讨论主体。\n关键词：技术哲学；后人类\n正文继续讨论。")
        self.assertEqual(abstract, "技术哲学讨论主体。")
        self.assertEqual(keywords, ("技术哲学", "后人类"))
        self.assertIn("正文继续", body)

    def test_multiline_keywords_are_extracted_without_swallowing_body(self) -> None:
        text = "关键词：科学技术哲学；技术中介；\n人工智能；后人类主义\n正文第一段内容不应成为关键词"
        body, _, keywords = extract_abstract_and_keywords(text)
        self.assertEqual(keywords, ("科学技术哲学", "技术中介", "人工智能", "后人类主义"))
        self.assertIn("正文第一段", body)

    def test_theme_words_are_not_injected_without_flag(self) -> None:
        docs = [PaperDocument("one", "主体与世界")]
        plain = analyse_documents(docs, theme_words=["后人类主义"])
        injected = analyse_documents(docs, theme_words=["后人类主义"], inject_theme_words=True)
        self.assertNotIn("后人类主义", plain.scores)
        self.assertIn("后人类主义", injected.scores)

    def test_theme_boost_one_is_neutral_and_higher_boost_is_gentle(self) -> None:
        docs = [PaperDocument("one", "技术中介")]
        neutral = analyse_documents(docs, theme_words=["技术中介"], theme_boost=1.0)
        boosted = analyse_documents(docs, theme_words=["技术中介"], theme_boost=1.2)
        self.assertEqual(neutral.scores["技术中介"], 1.0)
        self.assertEqual(boosted.scores["技术中介"], 1.2)

    def test_balanced_scoring_equalises_document_contribution(self) -> None:
        docs = [PaperDocument("long", "主体 " * 100 + "世界"), PaperDocument("short", "世界")]
        balanced = analyse_documents(docs, scoring_mode="balanced")
        raw = analyse_documents(docs, scoring_mode="raw")
        self.assertAlmostEqual(sum(balanced.scores.values()), 2.0)
        self.assertEqual(raw.scores["主体"], 100)
        self.assertEqual(raw.scores["世界"], 2)
        self.assertEqual(balanced.raw_frequency["主体"], 100)
        self.assertEqual(balanced.raw_frequency["世界"], 2)

    def test_independent_tokenizers_do_not_share_terms(self) -> None:
        custom = HumanitiesTokenizer(["科学技术哲学"])
        fresh = HumanitiesTokenizer()
        self.assertIn("科学技术哲学", custom.tokenize("科学技术哲学", default_stopwords()))
        self.assertNotIn("科学技术哲学", fresh.tokenize("科学技术哲学", default_stopwords()))

    def test_invalid_cli_numeric_options_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            for option, value in (("--theme-boost", "0.5"), ("--prefer-horizontal", "1.5"), ("--max-words", "0")):
                with self.subTest(option=option):
                    result = subprocess.run(
                        [sys.executable, "arxiv_wordcloud.py", "--pdfs", temp_dir, "--dry-run", option, value],
                        cwd=Path(__file__).parents[1], capture_output=True, text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(option, result.stderr)

    def test_csv_is_utf8_sig(self) -> None:
        result = analyse_documents([PaperDocument("one", "主体与世界")])
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "频率.csv"
            export_frequencies(result, str(path))
            self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertIn("主体", path.read_text(encoding="utf-8-sig"))

    def test_one_bad_pdf_does_not_abort_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "broken.pdf").write_bytes(b"not a pdf")
            valid = fitz.open()
            page = valid.new_page()
            page.insert_text((72, 72), "Chinese humanities test")
            valid.save(root / "valid.pdf")
            valid.close()
            documents = _get_documents_from_pdf_directory(str(root))
            self.assertEqual(len(documents), 1)


if __name__ == "__main__":
    unittest.main()
