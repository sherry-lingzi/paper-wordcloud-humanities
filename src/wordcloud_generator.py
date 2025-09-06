"""
词云生成器
支持多种样式和自定义选项的科学文献词云生成
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from wordcloud import WordCloud
from PIL import Image, ImageDraw, ImageFont
import os
import json
from typing import Dict, List, Tuple, Optional, Union
import logging
from collections import Counter

logger = logging.getLogger(__name__)

# 导入配置
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from data.papers_config import SCIENTIFIC_TERMS
except ImportError:
    SCIENTIFIC_TERMS = []


class WordCloudGenerator:
    """科学文献词云生成器"""
    
    def __init__(self, 
                 width: int = 1200, 
                 height: int = 800,
                 background_color: str = 'white',
                 max_words: int = 200,
                 relative_scaling: float = 0.5,
                 min_font_size: int = 10,
                 max_font_size: int = 100,
                 prefer_horizontal: float = 0.7,
                 output_dir: str = "output"):
        """
        初始化词云生成器
        
        Args:
            width: 词云图片宽度
            height: 词云图片高度
            background_color: 背景颜色
            max_words: 最大词数
            relative_scaling: 相对缩放因子
            min_font_size: 最小字体大小
            max_font_size: 最大字体大小
            prefer_horizontal: 水平文字偏好（0-1）
            output_dir: 输出目录
        """
        self.width = width
        self.height = height
        self.background_color = background_color
        self.max_words = max_words
        self.relative_scaling = relative_scaling
        self.min_font_size = min_font_size
        self.max_font_size = max_font_size
        self.prefer_horizontal = prefer_horizontal
        self.output_dir = output_dir
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 科学术语列表
        self.scientific_terms = set(term.lower() for term in SCIENTIFIC_TERMS)
        
        # 预定义颜色方案
        self.color_schemes = {
            'scientific': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
            'physics': ['#0d47a1', '#1565c0', '#1976d2', '#1e88e5', '#2196f3',
                       '#42a5f5', '#64b5f6', '#90caf9', '#bbdefb', '#e3f2fd'],
            'warm': ['#d32f2f', '#f57c00', '#fbc02d', '#689f38', '#388e3c'],
            'cool': ['#0288d1', '#0097a7', '#00695c', '#388e3c', '#689f38'],
            'monochrome': ['#212121', '#424242', '#616161', '#757575', '#9e9e9e'],
            'gradient': ['#ff5722', '#ff7043', '#ff8a65', '#ffab91', '#ffccbc']
        }
        
        # 默认字体路径
        self.font_paths = self._get_available_fonts()
    
    def _get_available_fonts(self) -> List[str]:
        """获取可用字体路径"""
        fonts = []
        
        # 常见字体名称
        font_names = [
            'DejaVu Sans', 'Arial', 'Helvetica', 'Times New Roman',
            'Liberation Sans', 'FreeSans', 'Ubuntu'
        ]
        
        for font_name in font_names:
            try:
                font_path = fm.findfont(fm.FontProperties(family=font_name))
                if font_path and os.path.exists(font_path):
                    fonts.append(font_path)
            except:
                continue
        
        # 如果没有找到字体，使用默认
        if not fonts:
            fonts.append(fm.findfont(fm.FontProperties()))
        
        return fonts
    
    def generate_wordcloud(self, 
                          text: str = None, 
                          word_frequencies: Dict[str, int] = None,
                          title: str = "WordCloud",
                          color_scheme: str = 'scientific',
                          custom_colors: List[str] = None,
                          font_path: str = None,
                          shape_mask: np.ndarray = None,
                          enhance_scientific_terms: bool = True) -> WordCloud:
        """
        生成词云
        
        Args:
            text: 输入文本
            word_frequencies: 词频字典
            title: 词云标题
            color_scheme: 颜色方案
            custom_colors: 自定义颜色列表
            font_path: 字体路径
            shape_mask: 形状遮罩
            enhance_scientific_terms: 是否增强科学术语
            
        Returns:
            WordCloud对象
        """
        # 准备数据
        if word_frequencies is None and text is None:
            raise ValueError("必须提供text或word_frequencies中的一个")
        
        if word_frequencies is None:
            # 从文本中计算词频
            words = text.split()
            word_frequencies = Counter(words)
        
        # 增强科学术语
        if enhance_scientific_terms:
            word_frequencies = self._enhance_scientific_terms(word_frequencies)
        
        # 选择颜色函数
        color_func = self._get_color_function(color_scheme, custom_colors)
        
        # 选择字体
        if font_path is None and self.font_paths:
            font_path = self.font_paths[0]
        
        # 创建WordCloud对象
        wordcloud = WordCloud(
            width=self.width,
            height=self.height,
            background_color=self.background_color,
            max_words=self.max_words,
            relative_scaling=self.relative_scaling,
            min_font_size=self.min_font_size,
            max_font_size=self.max_font_size,
            prefer_horizontal=self.prefer_horizontal,
            font_path=font_path,
            mask=shape_mask,
            color_func=color_func,
            collocations=False,  # 避免重复词汇
            random_state=42      # 固定随机种子保证可重复性
        )
        
        # 生成词云
        wordcloud.generate_from_frequencies(word_frequencies)
        
        return wordcloud
    
    def _enhance_scientific_terms(self, word_frequencies: Dict[str, int]) -> Dict[str, int]:
        """增强科学术语的权重"""
        enhanced = word_frequencies.copy()
        
        for word, freq in word_frequencies.items():
            if word.lower() in self.scientific_terms:
                # 科学术语权重增加50%
                enhanced[word] = int(freq * 1.5)
        
        return enhanced
    
    def _get_color_function(self, color_scheme: str, custom_colors: List[str] = None):
        """获取颜色函数"""
        if custom_colors:
            colors = custom_colors
        elif color_scheme in self.color_schemes:
            colors = self.color_schemes[color_scheme]
        else:
            colors = self.color_schemes['scientific']
        
        def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
            # 科学术语使用特殊颜色
            if word.lower() in self.scientific_terms:
                return colors[0]  # 使用第一个颜色（通常是最显眼的）
            else:
                # 其他词汇随机选择颜色
                np.random.seed(hash(word) % 2**32)
                return np.random.choice(colors[1:])
        
        return color_func
    
    def create_shape_mask(self, shape_type: str = 'circle', size: Tuple[int, int] = None) -> np.ndarray:
        """
        创建形状遮罩
        
        Args:
            shape_type: 形状类型 ('circle', 'square', 'heart', 'star')
            size: 尺寸 (width, height)
            
        Returns:
            形状遮罩数组
        """
        if size is None:
            size = (self.width, self.height)
        
        width, height = size
        mask = np.zeros((height, width), dtype=np.uint8)
        
        if shape_type == 'circle':
            # 圆形
            center_x, center_y = width // 2, height // 2
            radius = min(width, height) // 3
            y, x = np.ogrid[:height, :width]
            mask_circle = (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2
            mask[mask_circle] = 255
        
        elif shape_type == 'square':
            # 正方形
            margin = min(width, height) // 6
            mask[margin:height-margin, margin:width-margin] = 255
        
        elif shape_type == 'heart':
            # 心形
            self._create_heart_mask(mask, width, height)
        
        elif shape_type == 'star':
            # 星形
            self._create_star_mask(mask, width, height)
        
        return mask
    
    def _create_heart_mask(self, mask: np.ndarray, width: int, height: int):
        """创建心形遮罩"""
        center_x, center_y = width // 2, height // 2
        scale = min(width, height) // 10
        
        for y in range(height):
            for x in range(width):
                # 心形方程
                x_norm = (x - center_x) / scale
                y_norm = (center_y - y) / scale
                
                if ((x_norm**2 + y_norm**2 - 1)**3 - x_norm**2 * y_norm**3) <= 0:
                    mask[y, x] = 255
    
    def _create_star_mask(self, mask: np.ndarray, width: int, height: int):
        """创建星形遮罩"""
        center_x, center_y = width // 2, height // 2
        outer_radius = min(width, height) // 3
        inner_radius = outer_radius // 2
        
        # 五角星的顶点
        angles = [i * 2 * np.pi / 10 - np.pi/2 for i in range(10)]
        points = []
        
        for i, angle in enumerate(angles):
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            points.append((int(x), int(y)))
        
        # 使用PIL绘制多边形
        img = Image.new('L', (width, height), 0)
        ImageDraw.Draw(img).polygon(points, outline=255, fill=255)
        mask[:] = np.array(img)
    
    def save_wordcloud(self, 
                      wordcloud: WordCloud, 
                      filename: str, 
                      title: str = None,
                      add_stats: bool = True,
                      dpi: int = 300) -> str:
        """
        保存词云图片
        
        Args:
            wordcloud: WordCloud对象
            filename: 文件名
            title: 图片标题
            add_stats: 是否添加统计信息
            dpi: 图片分辨率
            
        Returns:
            保存的文件路径
        """
        # 创建图形
        plt.figure(figsize=(self.width/100, self.height/100), dpi=dpi)
        
        # 显示词云
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        
        # 添加标题
        if title:
            plt.title(title, fontsize=16, fontweight='bold', pad=20)
        
        # 添加统计信息
        if add_stats:
            stats_text = f"词数: {len(wordcloud.words_)} | 最大频率: {max(wordcloud.words_.values()) if wordcloud.words_ else 0}"
            plt.figtext(0.02, 0.02, stats_text, fontsize=8, alpha=0.7)
        
        # 保存文件
        if not filename.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.svg')):
            filename += '.png'
        
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=dpi, bbox_inches='tight', 
                   facecolor=self.background_color, edgecolor='none')
        plt.close()
        
        logger.info(f"词云已保存到: {filepath}")
        return filepath
    
    def generate_comparison_wordcloud(self, 
                                    texts_dict: Dict[str, str],
                                    title: str = "Comparison WordClouds") -> str:
        """
        生成对比词云图
        
        Args:
            texts_dict: 文本字典 {label: text}
            title: 总标题
            
        Returns:
            保存的文件路径
        """
        n_texts = len(texts_dict)
        if n_texts == 0:
            raise ValueError("至少需要一个文本")
        
        # 计算子图布局
        cols = min(n_texts, 3)
        rows = (n_texts + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(cols*6, rows*4))
        if n_texts == 1:
            axes = [axes]
        elif rows == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        # 为每个文本生成词云
        for i, (label, text) in enumerate(texts_dict.items()):
            if i >= len(axes):
                break
            
            wordcloud = self.generate_wordcloud(
                text=text, 
                color_scheme='scientific' if i == 0 else list(self.color_schemes.keys())[i % len(self.color_schemes)]
            )
            
            axes[i].imshow(wordcloud, interpolation='bilinear')
            axes[i].set_title(label, fontsize=12, fontweight='bold')
            axes[i].axis('off')
        
        # 隐藏多余的子图
        for i in range(n_texts, len(axes)):
            axes[i].axis('off')
        
        plt.tight_layout()
        
        # 保存
        filename = f"comparison_{title.replace(' ', '_').lower()}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"对比词云已保存到: {filepath}")
        return filepath
    
    def generate_combined_wordcloud(self, 
                                  texts_dict: Dict[str, str],
                                  weights: Dict[str, float] = None,
                                  title: str = "Combined WordCloud") -> str:
        """
        生成合并词云图
        
        Args:
            texts_dict: 文本字典 {label: text}
            weights: 权重字典 {label: weight}
            title: 标题
            
        Returns:
            保存的文件路径
        """
        if weights is None:
            weights = {label: 1.0 for label in texts_dict.keys()}
        
        # 合并所有文本的词频
        combined_frequencies = Counter()
        
        for label, text in texts_dict.items():
            weight = weights.get(label, 1.0)
            words = text.split()
            text_freq = Counter(words)
            
            for word, freq in text_freq.items():
                combined_frequencies[word] += int(freq * weight)
        
        # 生成词云
        wordcloud = self.generate_wordcloud(
            word_frequencies=combined_frequencies,
            title=title,
            color_scheme='scientific'
        )
        
        # 保存
        filename = f"combined_{title.replace(' ', '_').lower()}.png"
        filepath = self.save_wordcloud(wordcloud, filename, title)
        
        return filepath
    
    def export_word_frequencies(self, 
                              word_frequencies: Dict[str, int], 
                              filename: str,
                              top_n: int = 100) -> str:
        """
        导出词频数据
        
        Args:
            word_frequencies: 词频字典
            filename: 文件名
            top_n: 导出前N个词
            
        Returns:
            导出文件路径
        """
        # 排序词频
        sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # 准备数据
        export_data = {
            "total_words": len(word_frequencies),
            "total_frequency": sum(word_frequencies.values()),
            "top_words": [{"word": word, "frequency": freq} for word, freq in sorted_words],
            "scientific_terms": [{"word": word, "frequency": freq} 
                               for word, freq in sorted_words 
                               if word.lower() in self.scientific_terms]
        }
        
        # 保存JSON文件
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"词频数据已导出到: {filepath}")
        return filepath
    
    def create_style_gallery(self, text: str, base_filename: str = "gallery"):
        """
        创建样式画廊，展示不同颜色方案的词云
        
        Args:
            text: 输入文本
            base_filename: 基础文件名
        """
        gallery_paths = []
        
        for scheme_name in self.color_schemes.keys():
            wordcloud = self.generate_wordcloud(
                text=text, 
                color_scheme=scheme_name,
                title=f"Style: {scheme_name.title()}"
            )
            
            filename = f"{base_filename}_{scheme_name}.png"
            filepath = self.save_wordcloud(wordcloud, filename, f"Color Scheme: {scheme_name.title()}")
            gallery_paths.append(filepath)
        
        logger.info(f"样式画廊已生成: {len(gallery_paths)} 个样式")
        return gallery_paths


# 测试函数
def test_wordcloud_generator():
    """测试WordCloudGenerator功能"""
    generator = WordCloudGenerator()
    
    # 测试文本
    test_text = """
    quantum monte carlo simulation superconductivity electron phonon coupling
    dirac fermions antiferromagnetic phase transition critical temperature
    hubbard model condensed matter physics strongly correlated systems
    many body theory computational physics numerical analysis
    """
    
    print("测试基础词云生成...")
    
    # 生成基础词云
    wordcloud = generator.generate_wordcloud(
        text=test_text * 10,  # 重复文本增加词频
        title="Test Scientific WordCloud"
    )
    
    # 保存词云
    filepath = generator.save_wordcloud(
        wordcloud, 
        "test_wordcloud", 
        title="Scientific Literature WordCloud"
    )
    
    print(f"✓ 词云已生成: {filepath}")
    
    # 测试形状遮罩
    print("测试形状遮罩...")
    circle_mask = generator.create_shape_mask('circle')
    wordcloud_circle = generator.generate_wordcloud(
        text=test_text * 10,
        shape_mask=circle_mask,
        color_scheme='physics'
    )
    
    filepath_circle = generator.save_wordcloud(
        wordcloud_circle, 
        "test_wordcloud_circle", 
        title="Circular WordCloud"
    )
    
    print(f"✓ 圆形词云已生成: {filepath_circle}")
    
    # 测试词频导出
    word_freq = {word: len(word) for word in test_text.split()}
    export_path = generator.export_word_frequencies(word_freq, "test_frequencies")
    print(f"✓ 词频数据已导出: {export_path}")


if __name__ == "__main__":
    test_wordcloud_generator()