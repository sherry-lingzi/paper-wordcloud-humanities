"""
文本提取器
使用BeautifulSoup从ar5iv HTML页面中提取纯文本内容
"""

from bs4 import BeautifulSoup, Tag
import re
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TextExtractor:
    """从HTML中提取和清理文本内容"""
    
    def __init__(self, 
                 extract_abstract: bool = True,
                 extract_introduction: bool = True,
                 extract_conclusion: bool = True,
                 extract_references: bool = False,
                 remove_math: bool = False):
        """
        初始化文本提取器
        
        Args:
            extract_abstract: 是否提取摘要
            extract_introduction: 是否提取引言
            extract_conclusion: 是否提取结论
            extract_references: 是否提取参考文献
            remove_math: 是否移除数学公式
        """
        self.extract_abstract = extract_abstract
        self.extract_introduction = extract_introduction
        self.extract_conclusion = extract_conclusion
        self.extract_references = extract_references
        self.remove_math = remove_math
        
    def extract_text_from_html(self, html_content: str) -> Dict[str, str]:
        """
        从HTML内容中提取结构化文本
        
        Args:
            html_content: HTML内容字符串
            
        Returns:
            包含不同部分文本的字典
        """
        soup = BeautifulSoup(html_content, 'html5lib')
        
        # 清理HTML，移除不需要的元素
        self._clean_soup(soup)
        
        extracted_text = {}
        
        # 提取标题
        extracted_text['title'] = self._extract_title(soup)
        
        # 提取摘要
        if self.extract_abstract:
            extracted_text['abstract'] = self._extract_abstract(soup)
        
        # 提取正文内容
        extracted_text['body'] = self._extract_body(soup)
        
        # 提取引言
        if self.extract_introduction:
            extracted_text['introduction'] = self._extract_introduction(soup)
        
        # 提取结论
        if self.extract_conclusion:
            extracted_text['conclusion'] = self._extract_conclusion(soup)
        
        # 提取参考文献
        if self.extract_references:
            extracted_text['references'] = self._extract_references(soup)
        
        # 提取完整文本（用于词云生成）
        extracted_text['full_text'] = self._combine_texts(extracted_text)
        
        return extracted_text
    
    def _clean_soup(self, soup: BeautifulSoup) -> None:
        """
        清理BeautifulSoup对象，移除不需要的元素
        
        Args:
            soup: BeautifulSoup对象
        """
        # 移除脚本和样式
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # 移除PGF/TikZ渲染代码（LaTeX图形引擎产生的噪音）
        for element in soup.find_all(['g', 'defs', 'path', 'rect', 'circle']):
            element.decompose()
        
        # 移除所有包含LaTeX/PGF/HTML属性的元素
        # 1. 移除包含PGF命令的文本节点
        pgf_patterns = [
            'pgfsys', 'beginscope', 'endscope', 'closescope', 'invoke', 
            'definecolor', 'pgfpicture', 'makeatletter', 'hbox', 'vbox',
            'tikz@color', 'pgfstroke', 'pgffill', 'setlinewidth', 'moveto', 'lineto',
            'curveto', 'nullfont', 'rgb{', 'class=', 'id=', 'xref='
        ]
        
        # 删除包含这些模式的整个父元素
        for pattern in pgf_patterns:
            for element in soup.find_all(text=lambda t: t and pattern in t.lower()):
                if element.parent:
                    element.parent.decompose()
        
        # 2. 移除所有HTML属性（彻底清除class、id等）
        for tag in soup.find_all(True):
            tag.attrs = {}
        
        # 3. 移除包含大量数字和符号的元素（可能是渲染代码）
        for element in soup.find_all(text=True):
            if element.strip():
                # 如果文本中符号+数字占比超过70%，删除
                text = element.strip()
                symbol_digit_count = sum(1 for c in text if not c.isalpha() and not c.isspace())
                if len(text) > 10 and symbol_digit_count / len(text) > 0.7:
                    element.extract()
        
        # 移除导航和菜单元素
        for element in soup.find_all(['div'], class_=['ltx_navigation', 'ltx_page_navbar', 'ltx_page_footer']):
            element.decompose()
        
        # 移除数学公式（如果设置）
        if self.remove_math:
            for element in soup.find_all(['math', 'span'], class_=['ltx_Math', 'ltx_equation']):
                element.decompose()
        
        # 移除图表引用
        for element in soup.find_all(['figure', 'table'], class_=['ltx_figure', 'ltx_table']):
            if element.find('figcaption') or element.find('caption'):
                # 保留标题，移除图片/表格内容
                caption = element.find('figcaption') or element.find('caption')
                element.clear()
                if caption:
                    element.append(caption)
        
        # 移除LaTeX特殊命令残留
        for element in soup.find_all(text=True):
            if isinstance(element.parent, Tag):
                cleaned_text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', element)
                cleaned_text = re.sub(r'\\[a-zA-Z]+', '', cleaned_text)
                element.replace_with(cleaned_text)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取论文标题"""
        # 尝试多种方式查找标题
        title_selectors = [
            'h1.ltx_title',
            '.ltx_title',
            'title',
            'h1',
            '.paper-title'
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                title = title_element.get_text().strip()
                # 清理arXiv页面标题中的额外信息
                title = re.sub(r'^.*?\]\s*', '', title)  # 移除 [1234.5678]
                title = re.sub(r'\s*-\s*arXiv.*$', '', title, flags=re.IGNORECASE)
                return title
        
        return ""
    
    def _extract_abstract(self, soup: BeautifulSoup) -> str:
        """提取摘要"""
        # 查找摘要部分
        abstract_selectors = [
            '.ltx_abstract',
            'section.ltx_abstract',
            'div.ltx_abstract',
            '[class*="abstract"]'
        ]
        
        for selector in abstract_selectors:
            abstract_element = soup.select_one(selector)
            if abstract_element:
                # 移除"Abstract"标题
                abstract_text = abstract_element.get_text()
                abstract_text = re.sub(r'^Abstract\s*:?\s*', '', abstract_text, flags=re.IGNORECASE)
                return self._clean_text(abstract_text)
        
        return ""
    
    def _extract_body(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        # 查找正文容器
        body_selectors = [
            '.ltx_document',
            '.ltx_page_main',
            'main',
            'article',
            'body'
        ]
        
        body_texts = []
        
        for selector in body_selectors:
            body_element = soup.select_one(selector)
            if body_element:
                # 提取所有段落
                paragraphs = body_element.find_all(['p', 'div'], class_=lambda x: x and 'ltx_p' in str(x))
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and len(text) > 20:  # 过滤太短的段落
                        body_texts.append(text)
                break
        
        return self._clean_text('\n'.join(body_texts))
    
    def _extract_introduction(self, soup: BeautifulSoup) -> str:
        """提取引言部分"""
        # 查找引言标题
        intro_keywords = ['introduction', 'motivation', 'background']
        intro_text = ""
        
        for keyword in intro_keywords:
            # 查找包含关键词的标题
            headers = soup.find_all(['h1', 'h2', 'h3', 'h4'], text=re.compile(keyword, re.IGNORECASE))
            for header in headers:
                # 获取该标题后的内容
                intro_text = self._extract_section_content(header)
                if intro_text:
                    break
            if intro_text:
                break
        
        return self._clean_text(intro_text)
    
    def _extract_conclusion(self, soup: BeautifulSoup) -> str:
        """提取结论部分"""
        # 查找结论标题
        conclusion_keywords = ['conclusion', 'summary', 'discussion', 'outlook']
        conclusion_text = ""
        
        for keyword in conclusion_keywords:
            headers = soup.find_all(['h1', 'h2', 'h3', 'h4'], text=re.compile(keyword, re.IGNORECASE))
            for header in headers:
                conclusion_text = self._extract_section_content(header)
                if conclusion_text:
                    break
            if conclusion_text:
                break
        
        return self._clean_text(conclusion_text)
    
    def _extract_references(self, soup: BeautifulSoup) -> str:
        """提取参考文献"""
        # 查找参考文献部分
        ref_selectors = [
            '.ltx_bibliography',
            'section.ltx_bibliography',
            '[class*="references"]',
            '[class*="bibliography"]'
        ]
        
        for selector in ref_selectors:
            ref_element = soup.select_one(selector)
            if ref_element:
                return self._clean_text(ref_element.get_text())
        
        return ""
    
    def _extract_section_content(self, header: Tag) -> str:
        """提取某个标题后的内容，直到下一个同级标题"""
        content_parts = []
        current = header.next_sibling
        
        while current:
            if hasattr(current, 'name'):
                # 如果遇到同级或更高级标题，停止
                if current.name in ['h1', 'h2', 'h3', 'h4']:
                    break
                # 提取段落内容
                if current.name in ['p', 'div']:
                    text = current.get_text().strip()
                    if text:
                        content_parts.append(text)
            
            current = current.next_sibling
        
        return '\n'.join(content_parts)
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本，移除多余的空白字符和特殊符号
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除LaTeX命令残留
        text = re.sub(r'\\[a-zA-Z]+\*?', '', text)
        text = re.sub(r'\{[^}]*\}', '', text)
        
        # 移除PGF/TikZ残留命令和函数调用
        pgf_cleanup_patterns = [
            r'\b(pgfsys|beginscope|endscope|closescope|invoke|definecolor|pgfpicture|makeatletter|tikz)\w*\b',
            r'\b(hbox|vbox|moveto|lineto|stroke|fill|setlinewidth)\w*\b',
            r'\{\d+\.\d+pt\}',  # 长度单位
            r'rgb\{\d+,\d+,\d+\}',  # RGB颜色
            r'\w*scope\w*',  # 各种scope相关
        ]
        
        for pattern in pgf_cleanup_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # 移除特殊字符
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', ' ', text)
        
        # 移除数字过多的行（可能是公式编号等）
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip():
                # 如果一行中数字太多，可能是公式或编号，跳过
                digit_ratio = sum(c.isdigit() for c in line) / len(line) if line else 0
                if digit_ratio < 0.5:  # 数字占比小于50%的行保留
                    cleaned_lines.append(line.strip())
        
        text = ' '.join(cleaned_lines)
        
        # 最终清理
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _combine_texts(self, extracted_text: Dict[str, str]) -> str:
        """
        组合不同部分的文本用于词云生成
        
        Args:
            extracted_text: 提取的文本字典
            
        Returns:
            组合后的完整文本
        """
        parts = []
        
        # 按重要性添加不同部分
        if extracted_text.get('title'):
            # 标题重复3次增加权重
            parts.extend([extracted_text['title']] * 3)
        
        if extracted_text.get('abstract'):
            # 摘要重复2次
            parts.extend([extracted_text['abstract']] * 2)
        
        if extracted_text.get('introduction'):
            parts.append(extracted_text['introduction'])
        
        if extracted_text.get('body'):
            parts.append(extracted_text['body'])
        
        if extracted_text.get('conclusion'):
            parts.append(extracted_text['conclusion'])
        
        return ' '.join(parts)
    
    def extract_keywords(self, text: str, top_n: int = 50) -> List[Tuple[str, int]]:
        """
        提取关键词及其频率
        
        Args:
            text: 输入文本
            top_n: 返回前N个关键词
            
        Returns:
            (关键词, 频率) 的列表
        """
        from collections import Counter
        import nltk
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize
        
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except:
            logger.warning("NLTK数据下载失败，使用基础分词")
        
        # 基础清理
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 分词
        try:
            words = word_tokenize(text)
            stop_words = set(stopwords.words('english'))
        except:
            # 如果NLTK不可用，使用简单分词
            words = text.split()
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did'}
        
        # 过滤停用词和短词
        filtered_words = [word for word in words 
                         if word not in stop_words 
                         and len(word) > 2 
                         and not word.isdigit()]
        
        # 统计词频
        word_freq = Counter(filtered_words)
        
        return word_freq.most_common(top_n)


# 测试函数
def test_text_extractor():
    """测试TextExtractor功能"""
    from html_fetcher import HTMLFetcher
    
    # 获取测试HTML内容
    fetcher = HTMLFetcher()
    test_arxiv_id = "2211.02002"
    html_content = fetcher.fetch_html_content(test_arxiv_id)
    
    if not html_content:
        print("无法获取测试HTML内容")
        return
    
    # 测试文本提取
    extractor = TextExtractor()
    extracted_text = extractor.extract_text_from_html(html_content)
    
    print(f"✓ 成功提取文本")
    print(f"标题: {extracted_text['title'][:100]}...")
    print(f"摘要长度: {len(extracted_text['abstract'])} 字符")
    print(f"正文长度: {len(extracted_text['body'])} 字符")
    print(f"完整文本长度: {len(extracted_text['full_text'])} 字符")
    
    # 测试关键词提取
    keywords = extractor.extract_keywords(extracted_text['full_text'], top_n=10)
    print(f"前10个关键词: {keywords}")


if __name__ == "__main__":
    test_text_extractor()