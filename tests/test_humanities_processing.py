"""Focused regression tests for the Scholar Portrait Chinese pipeline."""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

import fitz

from arxiv_wordcloud import _get_documents_from_pdf_directory, export_frequencies
from humanities_text import PaperDocument, extract_abstract_and_keywords, remove_references
from tokenizer_zh import analyse_documents, default_stopwords, register_terms, tokenize


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

    def test_abstract_and_keywords_are_separated(self) -> None:
        body, abstract, keywords = extract_abstract_and_keywords("摘要：技术哲学讨论主体。\n关键词：技术哲学；后人类\n正文继续讨论。")
        self.assertEqual(abstract, "技术哲学讨论主体。")
        self.assertEqual(keywords, ("技术哲学", "后人类"))
        self.assertIn("正文继续", body)

    def test_theme_words_are_not_injected_without_flag(self) -> None:
        docs = [PaperDocument("one", "主体与世界")]
        plain = analyse_documents(docs, theme_words=["后人类主义"])
        injected = analyse_documents(docs, theme_words=["后人类主义"], inject_theme_words=True)
        self.assertNotIn("后人类主义", plain.scores)
        self.assertIn("后人类主义", injected.scores)

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
