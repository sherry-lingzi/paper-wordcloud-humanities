"""
科学文献NLP处理模块
专门针对科学论文的文本预处理和分析
"""

import re
import string
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# 导入配置
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from data.papers_config import SCIENTIFIC_TERMS, ACADEMIC_STOPWORDS
except ImportError:
    logger.warning("无法导入配置文件，使用默认设置")
    SCIENTIFIC_TERMS = []
    ACADEMIC_STOPWORDS = []


class ScienceNLP:
    """科学文献专用的自然语言处理器"""
    
    def __init__(self, 
                 preserve_scientific_terms: bool = True,
                 remove_academic_stopwords: bool = True,
                 min_word_length: int = 3,
                 max_word_length: int = 20,
                 enable_stemming: bool = False,
                 enable_lemmatization: bool = True):
        """
        初始化科学NLP处理器
        
        Args:
            preserve_scientific_terms: 是否保留科学术语
            remove_academic_stopwords: 是否移除学术停用词
            min_word_length: 最小词长度
            max_word_length: 最大词长度
            enable_stemming: 是否启用词干提取
            enable_lemmatization: 是否启用词形还原
        """
        self.preserve_scientific_terms = preserve_scientific_terms
        self.remove_academic_stopwords = remove_academic_stopwords
        self.min_word_length = min_word_length
        self.max_word_length = max_word_length
        self.enable_stemming = enable_stemming
        self.enable_lemmatization = enable_lemmatization
        
        # 科学术语词汇表（转换为小写）
        self.scientific_terms = set(term.lower() for term in SCIENTIFIC_TERMS)
        
        # 学术停用词（转换为小写）
        self.academic_stopwords = set(word.lower() for word in ACADEMIC_STOPWORDS)
        
        # 通用英语停用词
        self.common_stopwords = self._get_common_stopwords()
        
        # 所有停用词
        self.all_stopwords = self.common_stopwords.union(self.academic_stopwords)
        
        # 数学物理符号模式
        self.math_patterns = [
            r'\b[a-zA-Z]_\{[^}]+\}',  # 下标
            r'\b[a-zA-Z]\^[0-9]',      # 指数
            r'\$[^$]*\$',              # LaTeX数学符号
            r'\\[a-zA-Z]+',           # LaTeX命令
            r'\b[0-9]+\.[0-9]+e[+-][0-9]+',  # 科学记数法
        ]
        
        # 初始化NLTK工具（如果可用）
        self.nltk_available = self._init_nltk()
        
    def _get_common_stopwords(self) -> Set[str]:
        """获取通用英语停用词"""
        # 基础英语停用词列表
        basic_stopwords = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
            'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
            'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
            'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
            'while', 'of', 'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after',
            'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just',
            'don', 'should', 'now'
        }
        
        return basic_stopwords
    
    def _init_nltk(self) -> bool:
        """初始化NLTK工具"""
        try:
            import nltk
            from nltk.corpus import stopwords
            from nltk.stem import PorterStemmer, WordNetLemmatizer
            from nltk.tokenize import word_tokenize
            
            # 尝试下载必要的数据
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('wordnet', quiet=True)
                nltk.download('omw-1.4', quiet=True)
            except:
                logger.warning("NLTK数据下载失败，将使用基础功能")
            
            # 初始化工具
            self.stemmer = PorterStemmer()
            self.lemmatizer = WordNetLemmatizer()
            
            # 添加NLTK停用词
            try:
                nltk_stopwords = set(stopwords.words('english'))
                self.common_stopwords = self.common_stopwords.union(nltk_stopwords)
                self.all_stopwords = self.common_stopwords.union(self.academic_stopwords)
            except:
                pass
            
            return True
            
        except ImportError:
            logger.warning("NLTK不可用，将使用基础文本处理")
            self.stemmer = None
            self.lemmatizer = None
            return False
    
    def preprocess_text(self, text: str) -> str:
        """
        预处理科学文献文本
        
        Args:
            text: 原始文本
            
        Returns:
            预处理后的文本
        """
        if not text:
            return ""
        
        # 1. 基础清理
        text = self._basic_cleaning(text)
        
        # 2. 处理数学符号
        text = self._handle_math_symbols(text)
        
        # 3. 分词和过滤
        words = self._tokenize_and_filter(text)
        
        # 4. 词干提取或词形还原
        words = self._apply_morphological_analysis(words)
        
        # 5. 最终过滤
        words = self._final_filtering(words)
        
        return ' '.join(words)
    
    def _basic_cleaning(self, text: str) -> str:
        """基础文本清理"""
        # 转换为小写
        text = text.lower()
        
        # 移除URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 移除邮箱
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _handle_math_symbols(self, text: str) -> str:
        """处理数学符号和公式"""
        # 移除或转换数学模式
        for pattern in self.math_patterns:
            text = re.sub(pattern, ' ', text)
        
        # 移除单独的希腊字母符号（通常是数学变量）
        greek_letters = ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 
                        'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'omicron', 'pi', 'rho', 
                        'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega']
        
        for letter in greek_letters:
            # 保留作为物理术语的希腊字母，但移除单独出现的
            if letter not in self.scientific_terms:
                text = re.sub(r'\b' + letter + r'\b', ' ', text)
        
        return text
    
    def _tokenize_and_filter(self, text: str) -> List[str]:
        """分词并初步过滤"""
        # 使用正则表达式分词（保留连字符）
        words = re.findall(r'\b[a-zA-Z]+(?:-[a-zA-Z]+)*\b', text)
        
        # 基础过滤
        filtered_words = []
        for word in words:
            word = word.lower().strip()
            
            # 长度过滤
            if len(word) < self.min_word_length or len(word) > self.max_word_length:
                continue
            
            # 数字过滤
            if word.isdigit():
                continue
            
            # 单个字符重复过滤
            if len(set(word)) == 1:
                continue
            
            # 科学术语优先保留
            if self.preserve_scientific_terms and word in self.scientific_terms:
                filtered_words.append(word)
                continue
            
            # 停用词过滤
            if self.remove_academic_stopwords and word in self.all_stopwords:
                continue
            
            filtered_words.append(word)
        
        return filtered_words
    
    def _apply_morphological_analysis(self, words: List[str]) -> List[str]:
        """应用词形学分析（词干提取或词形还原）"""
        if not self.nltk_available:
            return words
        
        processed_words = []
        
        for word in words:
            # 科学术语不进行词形变化
            if self.preserve_scientific_terms and word in self.scientific_terms:
                processed_words.append(word)
                continue
            
            # 词形还原优先于词干提取
            if self.enable_lemmatization and self.lemmatizer:
                try:
                    lemmatized = self.lemmatizer.lemmatize(word)
                    processed_words.append(lemmatized)
                    continue
                except:
                    pass
            
            # 词干提取
            if self.enable_stemming and self.stemmer:
                try:
                    stemmed = self.stemmer.stem(word)
                    processed_words.append(stemmed)
                    continue
                except:
                    pass
            
            # 如果都失败，保留原词
            processed_words.append(word)
        
        return processed_words
    
    def _final_filtering(self, words: List[str]) -> List[str]:
        """最终过滤和质量检查"""
        final_words = []
        
        for word in words:
            # 过滤太短的词（再次检查，因为词干提取可能产生短词）
            if len(word) < 2:
                continue
            
            # 过滤纯符号
            if not re.match(r'^[a-zA-Z-]+$', word):
                continue
            
            # 过滤意义不大的词
            meaningless_patterns = [
                r'^[a-z]\d+$',  # a1, b2等
                r'^\d+[a-z]$',  # 1a, 2b等
                r'^[xyz]+$',    # 纯变量名
            ]
            
            skip = False
            for pattern in meaningless_patterns:
                if re.match(pattern, word):
                    skip = True
                    break
            
            if skip:
                continue
            
            final_words.append(word)
        
        return final_words
    
    def extract_scientific_keywords(self, text: str, top_n: int = 50) -> List[Tuple[str, int]]:
        """
        提取科学关键词，优先显示科学术语
        
        Args:
            text: 预处理后的文本
            top_n: 返回前N个关键词
            
        Returns:
            (关键词, 频率) 的列表
        """
        words = text.split()
        word_freq = Counter(words)
        
        # 分离科学术语和普通词汇
        scientific_freq = {}
        general_freq = {}
        
        for word, freq in word_freq.items():
            if word in self.scientific_terms:
                scientific_freq[word] = freq
            else:
                general_freq[word] = freq
        
        # 科学术语给予更高权重
        weighted_freq = {}
        for word, freq in scientific_freq.items():
            weighted_freq[word] = freq * 2  # 科学术语权重翻倍
        
        for word, freq in general_freq.items():
            weighted_freq[word] = freq
        
        # 返回排序结果
        sorted_words = sorted(weighted_freq.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_words[:top_n]
    
    def analyze_text_quality(self, text: str) -> Dict[str, float]:
        """
        分析文本质量指标
        
        Args:
            text: 输入文本
            
        Returns:
            质量指标字典
        """
        if not text:
            return {"quality_score": 0.0}
        
        words = text.split()
        total_words = len(words)
        
        if total_words == 0:
            return {"quality_score": 0.0}
        
        # 科学术语占比
        scientific_words = sum(1 for word in words if word in self.scientific_terms)
        scientific_ratio = scientific_words / total_words
        
        # 停用词占比
        stopword_count = sum(1 for word in words if word in self.all_stopwords)
        stopword_ratio = stopword_count / total_words
        
        # 词汇多样性
        unique_words = len(set(words))
        diversity_ratio = unique_words / total_words
        
        # 平均词长
        avg_word_length = sum(len(word) for word in words) / total_words
        
        # 计算综合质量分数
        quality_score = (
            scientific_ratio * 0.3 +           # 科学术语比例
            (1 - stopword_ratio) * 0.2 +       # 低停用词比例
            diversity_ratio * 0.3 +            # 词汇多样性
            min(avg_word_length / 6, 1) * 0.2  # 合理的平均词长
        )
        
        return {
            "quality_score": round(quality_score, 3),
            "total_words": total_words,
            "unique_words": unique_words,
            "scientific_ratio": round(scientific_ratio, 3),
            "stopword_ratio": round(stopword_ratio, 3),
            "diversity_ratio": round(diversity_ratio, 3),
            "avg_word_length": round(avg_word_length, 2)
        }
    
    def get_text_statistics(self, text: str) -> Dict[str, int]:
        """获取文本统计信息"""
        if not text:
            return {}
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        return {
            "total_characters": len(text),
            "total_words": len(words),
            "unique_words": len(set(words)),
            "sentences": len([s for s in sentences if s.strip()]),
            "avg_words_per_sentence": len(words) / max(len(sentences), 1),
            "scientific_terms_count": sum(1 for word in words if word in self.scientific_terms)
        }


# 测试函数
def test_science_nlp():
    """测试ScienceNLP功能"""
    nlp = ScienceNLP()
    
    # 测试文本
    test_text = """
    The quantum Monte Carlo simulation reveals the emergence of superconducting phases
    in strongly correlated electron systems. The Hubbard model demonstrates antiferromagnetic
    ordering with critical temperature Tc. Mathematical formulas like H = ∑_i c†_i c_i
    are essential for understanding fermion dynamics in condensed matter physics.
    """
    
    print("原始文本:")
    print(test_text)
    print("\n" + "="*50 + "\n")
    
    # 文本预处理
    processed_text = nlp.preprocess_text(test_text)
    print("预处理后:")
    print(processed_text)
    print("\n" + "="*30 + "\n")
    
    # 提取科学关键词
    keywords = nlp.extract_scientific_keywords(processed_text, top_n=10)
    print("科学关键词:")
    for word, freq in keywords:
        print(f"  {word}: {freq}")
    print("\n" + "="*30 + "\n")
    
    # 文本质量分析
    quality = nlp.analyze_text_quality(processed_text)
    print("文本质量分析:")
    for key, value in quality.items():
        print(f"  {key}: {value}")
    print("\n" + "="*30 + "\n")
    
    # 文本统计
    stats = nlp.get_text_statistics(processed_text)
    print("文本统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    test_science_nlp()