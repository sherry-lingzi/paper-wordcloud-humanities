#!/usr/bin/env python3
"""Paper WordCloud / Scholar Portrait for English science and Chinese humanities."""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import sys
from typing import Iterable, Sequence

import matplotlib
matplotlib.use("Agg")  # Rendering is non-interactive and must work on headless Windows.
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import requests
from wordcloud import WordCloud

from humanities_text import PaperDocument, extract_pdf_document, extract_text_from_pdf
from tokenizer_zh import FrequencyResult, analyse_documents, read_word_list


def download_arxiv_pdf(arxiv_id: str, output_dir: str = "papers") -> str | None:
    """Download one ArXiv PDF without stopping the complete batch on failure."""
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{arxiv_id}.pdf")
    if os.path.exists(pdf_path):
        print(f"PDF already exists: {arxiv_id}")
        return pdf_path
    try:
        print(f"Downloading {arxiv_id}...")
        response = requests.get(f"https://arxiv.org/pdf/{arxiv_id}.pdf", timeout=30)
        response.raise_for_status()
        Path(pdf_path).write_bytes(response.content)
        print(f"Downloaded: {arxiv_id} ({len(response.content) // 1024}KB)")
        return pdf_path
    except Exception as exc:
        print(f"Failed to download {arxiv_id}: {exc}")
        return None


def _get_documents_from_arxiv_ids(ids: Sequence[str], keep_references: bool = False) -> list[PaperDocument]:
    print(f"Processing {len(ids)} ArXiv papers...")
    documents: list[PaperDocument] = []
    for arxiv_id in ids:
        pdf_path = download_arxiv_pdf(arxiv_id)
        if not pdf_path:
            continue
        try:
            document = extract_pdf_document(pdf_path, keep_references=keep_references)
        except RuntimeError as exc:
            print(f"Warning: {exc}; continuing")
            continue
        if document.body or document.abstract:
            documents.append(document)
    return documents


def _get_documents_from_pdf_directory(pdf_dir: str, *, recursive: bool = False,
                                      keep_references: bool = False) -> list[PaperDocument]:
    """Extract local PDFs, allowing a bad or scanned PDF to fail independently."""
    root = Path(pdf_dir)
    pdf_files = sorted(root.rglob("*.pdf") if recursive else root.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        return []
    print(f"Processing {len(pdf_files)} PDF files...")
    documents: list[PaperDocument] = []
    for pdf_file in pdf_files:
        try:
            document = extract_pdf_document(pdf_file, keep_references=keep_references)
        except RuntimeError as exc:
            print(f"Warning: {exc}; continuing with remaining PDFs")
            continue
        if document.body or document.abstract:
            documents.append(document)
            print(f"Extracted {pdf_file.name} ({len(document.body) // 1000}k chars)")
        else:
            print(f"Warning: no selectable text in {pdf_file.name}; possible scanned PDF")
    return documents


# Legacy helpers retained for source compatibility.
def _get_texts_from_arxiv_ids(arxiv_ids: Sequence[str]) -> list[str]:
    return ["\n".join((doc.body, doc.abstract)) for doc in _get_documents_from_arxiv_ids(arxiv_ids)]


def _get_texts_from_pdf_directory(pdf_dir: str) -> list[str]:
    return ["\n".join((doc.body, doc.abstract)) for doc in _get_documents_from_pdf_directory(pdf_dir)]


def get_word_frequencies(texts: Sequence[str], min_word_length: int = 3,
                         theme_words_file: str | None = None) -> dict[str, float]:
    """Original API, upgraded to Chinese-aware jieba tokenisation."""
    del min_word_length
    docs = [PaperDocument(source=f"text-{i}", body=text) for i, text in enumerate(texts)]
    return analyse_documents(docs, theme_words=read_word_list(theme_words_file)).scores


def _contains_chinese(words: Iterable[str]) -> bool:
    return any("\u3400" <= char <= "\u9fff" for word in words for char in word)


def find_cjk_font() -> str | None:
    """Find a common installed CJK font without copying/downloading one."""
    candidates = [
        "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/Deng.ttf", "C:/Windows/Fonts/simsun.ttc",
        "/System/Library/Fonts/PingFang.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    return next((path for path in candidates if Path(path).is_file()), None)


def resolve_font(font_path: str | None, words: Iterable[str]) -> str | None:
    if font_path:
        if not Path(font_path).is_file():
            raise FileNotFoundError(f"Font file not found: {font_path}")
        return font_path
    if _contains_chinese(words):
        font = find_cjk_font()
        if not font:
            raise RuntimeError("Chinese text detected but no CJK font was found. Use --font <CJK font path>.")
        print(f"Using detected CJK font: {font}")
        return font
    return None


def create_masked_wordcloud(word_freq: dict[str, float], mask_path: str, output_path: str,
                            font_path: str | None = None, max_words: int = 500,
                            background_color: str = "black", prefer_horizontal: float = 0.7) -> bool:
    """Create the original fixed-seed, high-resolution, mask-based word cloud."""
    if not word_freq:
        print("No eligible words found after filtering.")
        return False
    try:
        mask_image = Image.open(mask_path).convert("L")
        width, height = mask_image.size
        hq_width, hq_height = width * 4, height * 4
        hq_mask = mask_image.resize((hq_width, hq_height), Image.Resampling.LANCZOS)
        processed_mask = np.where(np.array(hq_mask) < 128, 0, 255).astype(np.uint8)

        def white_color_func(*_args, **_kwargs):
            return "rgb(255, 255, 255)"

        cloud = WordCloud(width=hq_width, height=hq_height, background_color=background_color,
            max_words=max_words, relative_scaling=0.3, min_font_size=12, max_font_size=400,
            prefer_horizontal=prefer_horizontal, mask=processed_mask, color_func=white_color_func,
            collocations=False, random_state=42, font_step=1, margin=5, font_path=font_path).generate_from_frequencies(word_freq)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        dpi = 800
        figure, axis = plt.subplots(figsize=(hq_width / dpi, hq_height / dpi), dpi=dpi)
        axis.imshow(cloud, interpolation="bilinear")
        axis.axis("off")
        figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        axis.set_position([0, 0, 1, 1])
        figure.patch.set_facecolor(background_color)
        figure.savefig(output, dpi=dpi, bbox_inches="tight", pad_inches=0,
                       facecolor=background_color, edgecolor="none")
        plt.close(figure)
        print(f"High-quality wordcloud saved: {output}")
        print(f"   Resolution: {hq_width}x{hq_height} @ {dpi} DPI; words placed: {len(cloud.words_)}")
        return True
    except Exception as exc:
        print(f"Failed to create wordcloud: {exc}")
        return False


def export_frequencies(result: FrequencyResult, path: str) -> None:
    """Export the transparent audit table in Excel-compatible UTF-8-SIG CSV."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    words = sorted(result.scores, key=lambda word: (-result.scores[word], word))
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["rank", "word", "score", "raw_frequency",
            "document_frequency", "document_ratio", "is_keyword", "is_theme", "is_protected_term", "source_type"])
        writer.writeheader()
        for rank, word in enumerate(words, 1):
            df = result.document_frequency.get(word, 0)
            source = "+".join(kind for kind, enabled in (("keyword", word in result.keywords),
                ("theme", word in result.themes), ("term", word in result.protected_terms)) if enabled)
            writer.writerow({"rank": rank, "word": word, "score": f"{result.scores[word]:.6f}",
                "raw_frequency": result.raw_frequency.get(word, 0), "document_frequency": df,
                "document_ratio": f"{df / result.document_count:.6f}" if result.document_count else "0",
                "is_keyword": word in result.keywords, "is_theme": word in result.themes,
                "is_protected_term": word in result.protected_terms, "source_type": source})
    print(f"Frequency audit saved: {destination}")


def analyse_papers(documents: Sequence[PaperDocument], *, terms_file: str | None = None,
                   theme_words_file: str | None = None, stopwords_file: str | None = None,
                   abstract_weight: float = 1.5, keyword_weight: float = 3.0,
                   theme_boost: float = 1.2, inject_theme_words: bool = False) -> FrequencyResult:
    """Load user lists and compute raw, weighted and document-frequency statistics."""
    return analyse_documents(documents, terms=read_word_list(terms_file), theme_words=read_word_list(theme_words_file),
        extra_stopwords=read_word_list(stopwords_file), abstract_weight=abstract_weight, keyword_weight=keyword_weight,
        theme_boost=theme_boost, inject_theme_words=inject_theme_words)


def create_wordcloud(texts: Sequence[str], mask_path: str, output_path: str, font_path: str | None = None,
                     theme_words_file: str | None = None, max_words: int = 500) -> bool:
    docs = [PaperDocument(source=f"text-{i}", body=text) for i, text in enumerate(texts)]
    result = analyse_papers(docs, theme_words_file=theme_words_file)
    return create_masked_wordcloud(result.scores, mask_path, output_path, font_path, max_words)


def process_arxiv_ids(arxiv_ids: Sequence[str], mask_path: str, output_path: str, font_path: str | None = None,
                      theme_words_file: str | None = None, max_words: int = 500) -> bool:
    return create_wordcloud(_get_texts_from_arxiv_ids(arxiv_ids), mask_path, output_path, font_path, theme_words_file, max_words)


def process_pdf_directory(pdf_dir: str, mask_path: str, output_path: str, font_path: str | None = None,
                          theme_words_file: str | None = None, max_words: int = 500) -> bool:
    return create_wordcloud(_get_texts_from_pdf_directory(pdf_dir), mask_path, output_path, font_path, theme_words_file, max_words)


def _print_top_words(result: FrequencyResult, limit: int = 30) -> None:
    top = sorted(result.scores, key=lambda word: (-result.scores[word], word))[:limit]
    print(f"Top {len(top)} words (score / raw / document frequency):")
    for word in top:
        print(f"   {word}: {result.scores[word]:.2f} / {result.raw_frequency.get(word, 0)} / {result.document_frequency.get(word, 0)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Paper WordCloud / Scholar Portrait images.")
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--ids", help="UTF-8 file of ArXiv IDs")
    inputs.add_argument("--pdfs", help="Directory containing local PDF papers")
    parser.add_argument("--mask", help="Mask image (required unless --dry-run)")
    parser.add_argument("--output", help="Output image (required unless --dry-run)")
    parser.add_argument("--font", help="CJK-capable font path, if auto-detection is unsuitable")
    parser.add_argument("--theme-words", help="UTF-8 terms to protect and gently boost")
    parser.add_argument("--terms", help="UTF-8 terms to protect only")
    parser.add_argument("--stopwords", help="UTF-8 stopwords merged with bundled list")
    parser.add_argument("--export-frequencies", help="UTF-8-SIG CSV audit output")
    parser.add_argument("--recursive", action="store_true", help="Search PDFs recursively")
    parser.add_argument("--keep-references", action="store_true", help="Keep reference sections")
    parser.add_argument("--abstract-weight", type=float, default=1.5)
    parser.add_argument("--keyword-weight", type=float, default=3.0)
    parser.add_argument("--theme-boost", type=float, default=1.2)
    parser.add_argument("--inject-theme-words", action="store_true", help="Inject themes absent from corpus")
    parser.add_argument("--prefer-horizontal", type=float, default=None)
    parser.add_argument("--max-words", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true", help="Score/export without rendering a word cloud")
    args = parser.parse_args()
    if args.ids and not Path(args.ids).is_file(): parser.error(f"ArXiv IDs file not found: {args.ids}")
    if args.pdfs and not Path(args.pdfs).is_dir(): parser.error(f"PDF directory not found: {args.pdfs}")
    for word_list in (args.terms, args.theme_words, args.stopwords):
        if word_list and not Path(word_list).is_file(): parser.error(f"Word-list file not found: {word_list}")
    if not args.dry_run:
        if not args.mask or not Path(args.mask).is_file(): parser.error("--mask must name an existing image unless --dry-run")
        if not args.output: parser.error("--output is required unless --dry-run")
    if args.ids:
        ids = [line.strip() for line in Path(args.ids).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        documents = _get_documents_from_arxiv_ids(ids, args.keep_references)
    else:
        documents = _get_documents_from_pdf_directory(args.pdfs, recursive=args.recursive, keep_references=args.keep_references)
    if not documents:
        print("No usable documents were extracted.")
        return 1
    result = analyse_papers(documents, terms_file=args.terms, theme_words_file=args.theme_words,
        stopwords_file=args.stopwords, abstract_weight=args.abstract_weight, keyword_weight=args.keyword_weight,
        theme_boost=args.theme_boost, inject_theme_words=args.inject_theme_words)
    _print_top_words(result)
    if args.export_frequencies: export_frequencies(result, args.export_frequencies)
    if args.dry_run:
        print("Dry run complete; no word-cloud image was generated.")
        return 0
    try:
        font = resolve_font(args.font, result.scores)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}")
        return 1
    horizontal = args.prefer_horizontal if args.prefer_horizontal is not None else (1.0 if _contains_chinese(result.scores) else 0.7)
    if not 0 <= horizontal <= 1:
        print("Error: --prefer-horizontal must be between 0 and 1.")
        return 1
    return 0 if create_masked_wordcloud(result.scores, args.mask, args.output, font, args.max_words,
                                         prefer_horizontal=horizontal) else 1


def create_wordcloud_from_arxiv(arxiv_ids: Sequence[str], mask_image: str, output_file: str,
                                font_path: str | None = None, theme_words_file: str | None = None, max_words: int = 500) -> bool:
    return process_arxiv_ids(arxiv_ids, mask_image, output_file, font_path, theme_words_file, max_words)


def create_wordcloud_from_pdfs(pdf_directory: str, mask_image: str, output_file: str,
                               font_path: str | None = None, theme_words_file: str | None = None, max_words: int = 500) -> bool:
    return process_pdf_directory(pdf_directory, mask_image, output_file, font_path, theme_words_file, max_words)


def create_wordcloud_from_texts(texts: Sequence[str], mask_image: str, output_file: str,
                                font_path: str | None = None, theme_words_file: str | None = None, max_words: int = 500) -> bool:
    return create_wordcloud(texts, mask_image, output_file, font_path, theme_words_file, max_words)


if __name__ == "__main__":
    sys.exit(main())
