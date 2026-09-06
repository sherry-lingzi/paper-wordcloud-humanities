# Paper WordCloud / Scholar Portrait

这是一个面向**英文科学论文**和本地**中文人文学术论文集**的可解释性遮罩词云工具。它特别适合文学、哲学、历史、文化研究与 STS，用论文语料生成一位学者的“学术关键词肖像”。原项目的 ArXiv 下载、mask、固定随机种子、黑底白字及高分辨率输出均被保留；MIT 许可证和原作者信息未改动。

## 中文人文学者学术关键词肖像

准备：

```
papers/                 老师的 PDF 论文集
terms.txt               需要保持完整的学术术语
theme_words.txt         希望轻度强调的核心概念
custom_stopwords.txt    首次审查后补充的无意义高频词
```

处理链路为：PDF 页面级清洗 → 重复页眉页脚去除 → 参考文献截断 → 摘要/关键词识别 → jieba 分词 → 术语保护 → 停用词过滤 → 词频与文档频率统计 → 可审查 CSV → 词云。全过程不使用 LLM、云端 NLP、OCR 或自动下载字体，不会修改原始 PDF。

先进行 dry-run，审查 CSV：

```bash
python arxiv_wordcloud.py --pdfs ./papers --recursive --dry-run \
  --scoring-mode balanced \
  --terms ./terms.txt --theme-words ./theme_words.txt \
  --stopwords ./custom_stopwords.txt \
  --export-frequencies ./output/frequencies.csv
```

检查 Top words 和 `frequencies.csv` 后，增补停用词或术语，再生成正式图像：

```bash
python arxiv_wordcloud.py --pdfs ./papers --recursive \
  --mask ./mask.png --output ./output/portrait.png \
  --terms ./terms.txt --theme-words ./theme_words.txt \
  --stopwords ./custom_stopwords.txt \
  --export-frequencies ./output/frequencies.csv \
  --font "C:/Windows/Fonts/msyh.ttc"
```

`terms` **不等于** `theme words`：前者只通过 jieba 保护分词，例如“科学技术哲学”不被拆开；后者既保护分词，又在它真实出现在论文中时进行温和、有限的加权。默认不会把语料中没有出现的 theme word 塞进词云；如确有需要，显式加入 `--inject-theme-words`。

### 两种统计模式

`raw`（默认）按整个论文集的真实总词频统计，适合论文篇幅接近、或希望观察整个语料库语言重心的情况。

`balanced` 先在每篇论文内部按其加权 token 总分归一化，再汇总各篇结果；每篇论文大致相当于一张选票，摘要和关键词权重仍在篇内生效。它适合不同论文篇幅差异较大、论文/书评/专著章节混合，或制作长期学术研究轨迹与 Scholar Portrait。若论文篇幅差异明显，建议先用 `--scoring-mode balanced` 生成审查表，再与 `raw` 结果比较。

Windows CMD 可使用以下命令（`^` 为续行符；PowerShell 可改为单行或使用反引号）：

```cmd
python arxiv_wordcloud.py ^
  --pdfs .\papers ^
  --recursive ^
  --dry-run ^
  --scoring-mode balanced ^
  --terms .\terms.txt ^
  --theme-words .\theme_words.txt ^
  --stopwords .\custom_stopwords.txt ^
  --export-frequencies .\output\frequencies.csv
```

```cmd
python arxiv_wordcloud.py ^
  --pdfs .\papers ^
  --recursive ^
  --scoring-mode balanced ^
  --mask .\mask.png ^
  --output .\output\portrait.png ^
  --terms .\terms.txt ^
  --theme-words .\theme_words.txt ^
  --stopwords .\custom_stopwords.txt ^
  --export-frequencies .\output\frequencies.csv ^
  --font C:\Windows\Fonts\msyh.ttc
```

CSV 使用 UTF-8-SIG，Windows Excel 可直接打开；包含 `score`、`raw_frequency`、`document_frequency`、`document_ratio`、关键词/主题词/受保护术语标记。摘要默认权重为 1.5，作者关键词默认额外权重为 3.0。默认会从后半部分识别独立的“参考文献 / References / Bibliography”标题并截断，可用 `--keep-references` 保留。

中文词汇默认横排比例为 1.0。未给 `--font` 时会尝试 Windows/macOS/Linux 常见 CJK 字体；找不到时会明确报错，请提供 `--font <支持中文的字体路径>`，不会默默生成方框。

词云不是严格的文献计量分析，而是一种基于论文语料的可解释性学术视觉化。

## 英文 ArXiv 论文

```bash
python arxiv_wordcloud.py --ids examples/arxiv_ids.txt \
  --mask examples/mask.jpg --output result.png \
  --theme-words examples/theme_words.txt
```

原有 Python API 保持可用：`create_wordcloud_from_arxiv`、`create_wordcloud_from_pdfs`、`create_wordcloud_from_texts`、`get_word_frequencies` 与 `create_masked_wordcloud`。

## 新增 CLI 参数

`--terms`、`--stopwords`、`--export-frequencies`、`--recursive`、`--keep-references`、`--abstract-weight`、`--keyword-weight`、`--theme-boost`、`--inject-theme-words`、`--prefer-horizontal`、`--scoring-mode {raw,balanced}`、`--dry-run`。

## 安装与许可证

```bash
pip install -r requirements.txt
```

项目采用 MIT License；原项目作者为 Yin-Kai Yu（余荫铠，2024），版权声明完整保留于 [LICENSE](LICENSE)。

[English](README.md)
