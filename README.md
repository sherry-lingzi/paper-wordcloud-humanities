# Paper WordCloud / Scholar Portrait

An explainable, mask-based word-cloud generator for **English scientific papers** and, first and foremost, local collections of **Chinese humanities PDFs**: literature, philosophy, history, cultural studies, and STS.

It keeps the original project's ArXiv download, custom mask, fixed seed, black-background/white-text, and high-resolution rendering capabilities. The MIT License and original attribution remain unchanged.

## Chinese humanities workflow

The local-PDF pipeline is deliberately conservative and inspectable:

```
PDF → page cleaning → repeated header/footer removal → reference trimming
    → abstract/keyword recognition → jieba tokenisation → protected terms
    → stopword filtering → term/document-frequency scoring → audit CSV → word cloud
```

No LLM, cloud NLP, OCR, font download, or modification of source PDFs is used. A word cloud is an interpretable scholarly visualisation, **not** strict bibliometrics.

Install dependencies:

```bash
pip install -r requirements.txt
```

First inspect the corpus and adjust lists without creating an image:

```bash
python arxiv_wordcloud.py --pdfs ./papers --recursive --dry-run \
  --scoring-mode balanced \
  --terms ./terms.txt --theme-words ./theme_words.txt \
  --stopwords ./custom_stopwords.txt \
  --export-frequencies ./output/frequencies.csv
```

Then render the portrait:

```bash
python arxiv_wordcloud.py --pdfs ./papers --recursive \
  --mask ./mask.png --output ./output/portrait.png \
  --terms ./terms.txt --theme-words ./theme_words.txt \
  --stopwords ./custom_stopwords.txt \
  --export-frequencies ./output/frequencies.csv \
  --font "C:/Windows/Fonts/msyh.ttc"
```

`--terms` and `--theme-words` are intentionally different. Terms only protect a phrase from being split by jieba. Theme words also receive a small, bounded boost **only when they occur in the corpus**. Use `--inject-theme-words` to explicitly override that rule.

### Scoring modes

`raw` (the default) aggregates the real token count of the whole collection, so it is most useful when papers have similar lengths or when the corpus itself is the object of study. `balanced` first divides each paper's weighted token scores by that paper's total weighted score, then aggregates them. Each paper therefore contributes roughly one vote, while abstract and author-keyword bonuses still work inside that paper. For a long-term Scholar Portrait with very unequal paper lengths, review `--scoring-mode balanced` alongside `raw` before rendering.

The CSV is encoded as UTF-8-SIG for Excel and includes final score, raw frequency, document frequency/ratio, and keyword/theme/protected-term flags. Use `--keep-references` to retain references; default local processing trims an independent references heading in the latter half of the text. `--abstract-weight` defaults to 1.5 and `--keyword-weight` to 3.0.

If Chinese tokens are present and no `--font` is supplied, the program looks for common Windows/macOS/Linux CJK fonts. It errors clearly if none is found rather than producing boxes. Chinese output defaults to `--prefer-horizontal 1.0`; English preserves the original 0.7 layout preference.

## Existing English / ArXiv usage

```bash
python arxiv_wordcloud.py --ids examples/arxiv_ids.txt \
  --mask examples/mask.jpg --output result.png \
  --theme-words examples/theme_words.txt
```

The original Python API remains available: `create_wordcloud_from_arxiv`, `create_wordcloud_from_pdfs`, `create_wordcloud_from_texts`, `get_word_frequencies`, and `create_masked_wordcloud`.

## CLI additions

`--terms`, `--stopwords`, `--export-frequencies`, `--recursive`, `--keep-references`, `--abstract-weight`, `--keyword-weight`, `--theme-boost`, `--inject-theme-words`, `--prefer-horizontal`, `--scoring-mode {raw,balanced}`, and `--dry-run` support the Scholar Portrait workflow.

## License and attribution

MIT License. Original project author: Yin-Kai Yu (余荫铠), 2024. The copyright notice is retained verbatim in [LICENSE](LICENSE).

[简体中文](README.zh-CN.md)
