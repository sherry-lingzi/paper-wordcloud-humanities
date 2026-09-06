"""Explainable Chinese/English tokenisation and frequency scoring."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, Mapping
import unicodedata

import jieba

from humanities_text import PaperDocument, normalize_text


ENGLISH_STOPWORDS = {
    "THE", "AND", "OR", "BUT", "IN", "ON", "AT", "TO", "FOR", "OF", "WITH", "BY", "FROM",
    "A", "AN", "AS", "ARE", "WAS", "WERE", "BE", "BEEN", "HAVE", "HAS", "HAD", "DO", "IS",
    "IT", "ITS", "THIS", "THAT", "THESE", "THOSE", "THEY", "THEM", "THEIR", "WE", "OUR",
    "PAPER", "STUDY", "RESEARCH", "ANALYSIS", "METHOD", "RESULT", "RESULTS", "DISCUSSION",
    "INTRODUCTION", "ABSTRACT", "FIGURE", "TABLE", "EQUATION", "SECTION", "CHAPTER", "REFERENCES",
    "ALSO", "THEREFORE", "HOWEVER", "MOREOVER", "THUS", "WHICH", "WHERE", "WHEN", "WHAT",
}
_CJK_RE = re.compile(r"^[\u3400-\u4dbf\u4e00-\u9fff]+$")
_ASCII_TERM_RE = re.compile(r"[A-Za-z]+")
_DOI_RE = re.compile(r"^(?:10\.\d{4,9}/|doi[:.]?)", re.IGNORECASE)


@dataclass
class FrequencyResult:
    """Transparent statistics used to render and audit a portrait."""

    scores: dict[str, float]
    raw_frequency: dict[str, int]
    document_frequency: dict[str, int]
    keywords: set[str]
    themes: set[str]
    protected_terms: set[str]
    document_count: int
    scoring_mode: str = "raw"


def normalise_term(value: str) -> str:
    """NFKC-normalise a term and uppercase only its Latin fragments."""
    return _ASCII_TERM_RE.sub(lambda match: match.group(0).upper(), normalize_text(value).strip())


def read_word_list(path: str | Path | None) -> list[str]:
    """Read a UTF-8/BOM word list, ignoring blank lines and comments."""
    if not path:
        return []
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return [normalise_term(line) for line in handle if line.strip() and not line.lstrip().startswith("#")]


def default_stopwords() -> set[str]:
    """Return bundled humanities stopwords plus conservative English stopwords."""
    resource = Path(__file__).parent / "resources" / "stopwords_zh_humanities.txt"
    return set(read_word_list(resource)) | ENGLISH_STOPWORDS


def register_terms(terms: Iterable[str]) -> set[str]:
    """Register terms with jieba, returning their normalised forms."""
    registered: set[str] = set()
    for value in terms:
        term = normalise_term(value)
        if term:
            jieba.add_word(term)
            registered.add(term)
    return registered


def _token_is_valid(token: str, protected: set[str], stopwords: set[str]) -> bool:
    if not token or token in stopwords or token.isspace() or token in {"-", "_", "/", "."}:
        return False
    if token.isdigit() or _DOI_RE.match(token) or re.fullmatch(r"\d+(?:\.\d+)+", token):
        return False
    if token in protected:
        return True
    if _CJK_RE.fullmatch(token):
        return len(token) >= 2
    if re.fullmatch(r"[A-Z][A-Z0-9-]*", token):
        return len(token) >= 2
    if re.fullmatch(r"[A-Z][A-Z'-]*", token):
        return len(token) >= 3
    return False


def tokenize(text: str, protected_terms: Iterable[str] = (), stopwords: set[str] | None = None) -> list[str]:
    """Tokenise Chinese with jieba and retain useful Latin names/acronyms."""
    protected = {normalise_term(value) for value in protected_terms}
    stopword_set = default_stopwords() if stopwords is None else stopwords
    normalised = normalise_term(text)
    tokens: list[str] = []
    for raw_token in jieba.lcut(normalised, HMM=False):
        token = normalise_term(raw_token)
        if _token_is_valid(token, protected, stopword_set):
            tokens.append(token)
    return tokens


def analyse_documents(
    documents: Iterable[PaperDocument],
    *,
    terms: Iterable[str] = (),
    theme_words: Iterable[str] = (),
    extra_stopwords: Iterable[str] = (),
    abstract_weight: float = 1.5,
    keyword_weight: float = 3.0,
    theme_boost: float = 1.2,
    inject_theme_words: bool = False,
) -> FrequencyResult:
    """Score papers with explicit body, abstract, keyword and theme adjustments."""
    docs = list(documents)
    explicit_terms = register_terms(terms)
    themes_in_order = [normalise_term(word) for word in theme_words if normalise_term(word)]
    themes = register_terms(themes_in_order)
    keywords_in_order = [normalise_term(keyword) for doc in docs for keyword in doc.keywords]
    keywords = register_terms(keywords_in_order)
    protected = explicit_terms | themes | keywords
    stopwords = default_stopwords() | {normalise_term(word) for word in extra_stopwords}

    raw_frequency: Counter[str] = Counter()
    weighted_frequency: Counter[str] = Counter()
    document_frequency: Counter[str] = Counter()
    keyword_documents: Counter[str] = Counter()

    for document in docs:
        body_tokens = tokenize(document.body, protected, stopwords)
        abstract_tokens = tokenize(document.abstract, protected, stopwords)
        raw_frequency.update(body_tokens)
        raw_frequency.update(abstract_tokens)
        weighted_frequency.update(body_tokens)
        weighted_frequency.update({token: abstract_weight for token in abstract_tokens})
        seen = set(body_tokens) | set(abstract_tokens)
        for keyword in {normalise_term(value) for value in document.keywords}:
            if keyword:
                keyword_documents[keyword] += 1
                seen.add(keyword)
        document_frequency.update(seen)

    for keyword, count in keyword_documents.items():
        weighted_frequency[keyword] += keyword_weight * count
    for index, theme in enumerate(themes_in_order):
        if theme in weighted_frequency:
            # A bounded, gentle preference that never becomes negative.
            factor = max(1.10, theme_boost - min(index, 20) * 0.005)
            weighted_frequency[theme] *= factor
        elif inject_theme_words:
            weighted_frequency[theme] = max(1.0, keyword_weight) * max(1.0, theme_boost)
            document_frequency.setdefault(theme, 0)
            raw_frequency.setdefault(theme, 0)

    return FrequencyResult(
        scores=dict(weighted_frequency), raw_frequency=dict(raw_frequency),
        document_frequency=dict(document_frequency), keywords=keywords, themes=themes,
        protected_terms=explicit_terms, document_count=len(docs),
    )
