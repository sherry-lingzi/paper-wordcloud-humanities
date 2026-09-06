"""Explainable Chinese/English tokenisation and frequency scoring."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

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


class HumanitiesTokenizer:
    """An analysis-local jieba tokenizer that never mutates global jieba state."""

    def __init__(self, terms: Iterable[str] = ()) -> None:
        self._tokenizer = jieba.Tokenizer()
        self.protected_terms: set[str] = set()
        self.add_terms(terms)

    def add_terms(self, terms: Iterable[str]) -> set[str]:
        """Protect terms in this analysis session only."""
        for value in terms:
            term = normalise_term(value)
            if term:
                self._tokenizer.add_word(term)
                self.protected_terms.add(term)
        return self.protected_terms

    def tokenize(self, text: str, stopwords: set[str]) -> list[str]:
        """Tokenise Chinese and retain useful Latin names/acronyms."""
        tokens: list[str] = []
        for raw_token in self._tokenizer.cut(normalise_term(text), HMM=False):
            token = normalise_term(raw_token)
            if _token_is_valid(token, self.protected_terms, stopwords):
                tokens.append(token)
        return tokens


def register_terms(terms: Iterable[str]) -> set[str]:
    """Compatibility helper returning normalised terms without global mutation."""
    return {normalise_term(value) for value in terms if normalise_term(value)}


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
    """Compatibility wrapper using an isolated tokenizer for each call."""
    return HumanitiesTokenizer(protected_terms).tokenize(text, default_stopwords() if stopwords is None else stopwords)


def analyse_documents(
    documents: Iterable[PaperDocument], *, terms: Iterable[str] = (), theme_words: Iterable[str] = (),
    extra_stopwords: Iterable[str] = (), abstract_weight: float = 1.5, keyword_weight: float = 3.0,
    theme_boost: float = 1.2, inject_theme_words: bool = False, scoring_mode: str = "raw",
) -> FrequencyResult:
    """Score papers using raw corpus counts or equal-per-document contributions.

    In ``balanced`` mode each document's weighted token counter is divided by
    its own total before aggregation. Abstract and keyword bonuses therefore
    still apply inside each document, while every non-empty document sums to 1.
    """
    if scoring_mode not in {"raw", "balanced"}:
        raise ValueError("scoring_mode must be 'raw' or 'balanced'")
    docs = list(documents)
    explicit_terms = register_terms(terms)
    themes_in_order = [normalise_term(word) for word in theme_words if normalise_term(word)]
    themes = set(themes_in_order)
    keywords_in_order = [normalise_term(keyword) for doc in docs for keyword in doc.keywords]
    keywords = set(keywords_in_order)
    analyzer = HumanitiesTokenizer(explicit_terms | themes | keywords)
    stopwords = default_stopwords() | {normalise_term(word) for word in extra_stopwords}

    raw_frequency: Counter[str] = Counter()
    scores: Counter[str] = Counter()
    document_frequency: Counter[str] = Counter()
    for document in docs:
        body_tokens = analyzer.tokenize(document.body, stopwords)
        abstract_tokens = analyzer.tokenize(document.abstract, stopwords)
        raw_frequency.update(body_tokens)
        raw_frequency.update(abstract_tokens)
        document_score: Counter[str] = Counter(body_tokens)
        document_score.update({token: abstract_weight for token in abstract_tokens})
        document_keywords = {normalise_term(value) for value in document.keywords if normalise_term(value)}
        for keyword in document_keywords:
            document_score[keyword] += keyword_weight
        document_frequency.update(set(body_tokens) | set(abstract_tokens) | document_keywords)
        if scoring_mode == "balanced":
            total = sum(document_score.values())
            if total:
                scores.update({word: value / total for word, value in document_score.items()})
        else:
            scores.update(document_score)

    for index, theme in enumerate(themes_in_order):
        if theme in scores:
            factor = max(1.0, theme_boost - min(index, 20) * 0.005)
            scores[theme] *= factor
        elif inject_theme_words:
            scores[theme] = max(1.0, keyword_weight) * theme_boost
            document_frequency.setdefault(theme, 0)
            raw_frequency.setdefault(theme, 0)

    return FrequencyResult(scores=dict(scores), raw_frequency=dict(raw_frequency),
        document_frequency=dict(document_frequency), keywords=keywords, themes=themes,
        protected_terms=explicit_terms, document_count=len(docs), scoring_mode=scoring_mode)
