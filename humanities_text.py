"""Conservative, page-aware text preparation for humanities PDFs."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
from pathlib import Path
import re
from typing import Iterable
import unicodedata
import warnings

import fitz  # PyMuPDF


REFERENCE_HEADINGS = {"参考文献", "参考书目", "REFERENCES", "BIBLIOGRAPHY"}
_PAGE_NUMBER_RE = re.compile(r"^[—–\-\s]*\d{1,5}[—–\-\s]*$")
_ABSTRACT_RE = re.compile(
    r"(?ims)^\s*摘要\s*[:：]?\s*(.+?)(?=^\s*(?:关键词|关键字)\s*[:：]?|^\s*$|\Z)"
)
_KEYWORD_RE = re.compile(r"(?im)^\s*(?:关键词|关键字)\s*[:：]?\s*(.+?)\s*$")


@dataclass
class PaperDocument:
    """The text and author-supplied metadata extracted from one paper."""

    source: str
    body: str
    abstract: str = ""
    keywords: tuple[str, ...] = ()


def normalize_text(text: str) -> str:
    """Apply Unicode NFKC while preserving Chinese text and line boundaries."""
    return unicodedata.normalize("NFKC", text).replace("\u00a0", " ")


def _normalise_line(line: str) -> str:
    return re.sub(r"\s+", " ", normalize_text(line)).strip()


def _is_short_repeated_line(line: str) -> bool:
    return 1 <= len(line) <= 80 and not re.search(r"[。！？!?；;]", line)


def clean_pdf_pages(page_texts: Iterable[str]) -> list[str]:
    """Remove page numbers and likely repeated headers/footers from page texts.

    Only short lines repeated on a substantial share of pages are removed.  This
    deliberately conservative heuristic avoids trying to infer PDF layout.
    """
    pages = [[_normalise_line(line) for line in text.splitlines()] for text in page_texts]
    pages = [[line for line in page if line] for page in pages]
    if not pages:
        return []

    occurrences: Counter[str] = Counter()
    for page in pages:
        occurrences.update({line for line in page if _is_short_repeated_line(line)})
    threshold = max(2, math.ceil(len(pages) * 0.4))
    repeated = {line for line, count in occurrences.items() if count >= threshold}

    cleaned: list[str] = []
    for page in pages:
        kept = [line for line in page if line not in repeated and not _PAGE_NUMBER_RE.fullmatch(line)]
        cleaned.append("\n".join(kept))
    return cleaned


def is_reference_heading(line: str) -> bool:
    """Return true only for an independent, unnumbered references heading."""
    compact = re.sub(r"[\s:：.。]", "", normalize_text(line)).upper()
    return compact in REFERENCE_HEADINGS


def remove_references(lines: list[str], keep_references: bool = False) -> list[str]:
    """Trim an end-matter references section without treating prose as a heading."""
    if keep_references or not lines:
        return lines
    start = math.floor(len(lines) * 0.45)
    for index in range(start, len(lines)):
        if is_reference_heading(lines[index]):
            return lines[:index]
    return lines


def extract_abstract_and_keywords(text: str) -> tuple[str, str, tuple[str, ...]]:
    """Extract Chinese abstract and keyword lines and remove them from body text."""
    text = normalize_text(text)
    abstract = ""
    abstract_match = _ABSTRACT_RE.search(text)
    if abstract_match:
        abstract = abstract_match.group(1).strip()
        text = text[:abstract_match.start()] + text[abstract_match.end():]

    keywords: list[str] = []
    keyword_match = _KEYWORD_RE.search(text)
    if keyword_match:
        raw_keywords = keyword_match.group(1)
        keywords = [
            item.strip() for item in re.split(r"[；;,，、]", raw_keywords)
            if item.strip() and len(item.strip()) <= 80
        ]
        text = text[:keyword_match.start()] + text[keyword_match.end():]
    return re.sub(r"\n{3,}", "\n\n", text).strip(), abstract, tuple(keywords)


def extract_pdf_document(pdf_path: str | Path, keep_references: bool = False) -> PaperDocument:
    """Extract a PDF safely; raise only for the individual PDF that could not open."""
    path = Path(pdf_path)
    try:
        with fitz.open(path) as pdf:
            page_texts = [page.get_text("text") for page in pdf]
    except Exception as exc:  # caller continues with the remaining PDFs
        raise RuntimeError(f"Failed to extract {path}: {exc}") from exc

    cleaned_pages = clean_pdf_pages(page_texts)
    lines = [line for page in cleaned_pages for line in page.splitlines() if line.strip()]
    lines = remove_references(lines, keep_references=keep_references)
    body, abstract, keywords = extract_abstract_and_keywords("\n".join(lines))
    if len(body) + len(abstract) < 80:
        warnings.warn(
            f"{path.name}: very little selectable text was extracted; it may be a scanned PDF. Skipping it is recommended.",
            RuntimeWarning,
            stacklevel=2,
        )
    return PaperDocument(source=str(path), body=body, abstract=abstract, keywords=keywords)


def extract_text_from_pdf(pdf_path: str | Path, keep_references: bool = False) -> str:
    """Backwards-compatible text-only wrapper around :func:`extract_pdf_document`."""
    document = extract_pdf_document(pdf_path, keep_references=keep_references)
    return "\n".join(part for part in (document.body, document.abstract) if part)
