#!/usr/bin/env python3
"""
词云参数详解和演示
展示WordCloud的各种可调参数和效果对比
"""

import os
import sys
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from wordcloud import WordCloud

def wordcloud_parameters_demo():
    """词云参数详解和演示"""
    print("🎨 词云参数详解和演示...")
    
    # 加载词频数据
    freq_file = "output_batch/combined_all_papers_frequencies.json"
    with open(freq_file, 'r', encoding='utf-8') as f:
        freq_data = json.load(f)
    
    top_words = freq_data.get('top_words', [])[:100]
    word_frequencies = {item['word']: item['frequency'] for item in top_words}
    
    output_dir = "output_batch/parameter_demos"
    os.makedirs(output_dir, exist_ok=True)
    
    print("📋 WordCloud主要参数类别：")
    
    # =====================================
    # 1. 基础尺寸和布局参数
    # =====================================
    print("\n1️⃣ 基础尺寸和布局参数")
    
    size_configs = [
        {"name": "小尺寸", "width": 400, "height": 300, "desc": "适合小图标或缩略图"},
        {"name": "标准尺寸", "width": 800, "height": 600, "desc": "适合一般展示"},
        {"name": "高清尺寸", "width": 1600, "height": 1200, "desc": "适合打印或大屏显示"},
        {"name": "超宽尺寸", "width": 1920, "height": 800, "desc": "适合横幅或宽屏显示"}
    ]
    
    for config in size_configs:
        wc = WordCloud(
            width=config["width"], 
            height=config["height"],
            background_color='black',
            color_func=lambda *args, **kwargs: 'white',
            max_words=50,
            random_state=42
        ).generate_from_frequencies(word_frequencies)
        
        plt.figure(figsize=(12, 8))
        plt.imshow(wc, interpolation='bilinear')
        plt.title(f'{config["name"]} ({config["width"]}×{config["height"]}) - {config["desc"]}', 
                 fontsize=14, color='white')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/size_{config["name"]}.png', 
                   facecolor='black', bbox_inches='tight')
        plt.close()
    
    # =====================================
    # 2. 词汇数量和密度参数
    # =====================================
    print("2️⃣ 词汇数量和密度参数")
    
    word_count_configs = [
        {"max_words": 30, "desc": "稀疏布局，突出重点词汇"},
        {"max_words": 100, "desc": "平衡布局，中等密度"},
        {"max_words": 200, "desc": "密集布局，丰富内容"},
        {"max_words": 400, "desc": "超密集布局，最大信息量"}
    ]
    
    for i, config in enumerate(word_count_configs):
        wc = WordCloud(
            width=800, height=600,
            background_color='black',
            color_func=lambda *args, **kwargs: 'white',
            max_words=config["max_words"],
            random_state=42
        ).generate_from_frequencies(word_frequencies)
        
        plt.figure(figsize=(10, 8))
        plt.imshow(wc, interpolation='bilinear')
        plt.title(f'词汇数量: {config["max_words"]} - {config["desc"]}', 
                 fontsize=14, color='white')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/words_{config["max_words"]}.png', 
                   facecolor='black', bbox_inches='tight')
        plt.close()
    
    # =====================================
    # 3. 字体大小参数
    # =====================================
    print("3️⃣ 字体大小参数")
    
    font_size_configs = [
        {"min": 8, "max": 40, "desc": "小字体，精致密集"},
        {"min": 12, "max": 80, "desc": "中等字体，平衡可读"},
        {"min": 20, "max": 120, "desc": "大字体，醒目突出"},
        {"min": 30, "max": 200, "desc": "超大字体，视觉冲击"}
    ]
    
    for config in font_size_configs:
        wc = WordCloud(
            width=800, height=600,
            background_color='black',
            color_func=lambda *args, **kwargs: 'white',
            max_words=80,
            min_font_size=config["min"],
            max_font_size=config["max"],
            random_state=42
        ).generate_from_frequencies(word_frequencies)
        
        plt.figure(figsize=(10, 8))
        plt.imshow(wc, interpolation='bilinear')
        plt.title(f'字体大小: {config["min"]}-{config["max"]} - {config["desc"]}', 
                 fontsize=14, color='white')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/fontsize_{config["min"]}_{config["max"]}.png', 
                   facecolor='black', bbox_inches='tight')
        plt.close()
    
    # =====================================
    # 4. 相对缩放参数 (relative_scaling)
    # =====================================
    print("4️⃣ 相对缩放参数")
    
    scaling_configs = [
        {"scaling": 0.0, "desc": "无缩放，所有词汇大小相近"},
        {"scaling": 0.3, "desc": "轻微缩放，温和的大小差异"},
        {"scaling": 0.5, "desc": "适中缩放，明显的层次"},
        {"scaling": 0.8, "desc": "强烈缩放，极大的大小差异"},
        {"scaling": 1.0, "desc": "最大缩放，最极端的大小对比"}
    ]
    
    for config in scaling_configs:
        wc = WordCloud(
            width=800, height=600,
            background_color='black',
            color_func=lambda *args, **kwargs: 'white',
            max_words=80,
            relative_scaling=config["scaling"],
            random_state=42
        ).generate_from_frequencies(word_frequencies)
        
        plt.figure(figsize=(10, 8))
        plt.imshow(wc, interpolation='bilinear')
        plt.title(f'相对缩放: {config["scaling"]} - {config["desc"]}', 
                 fontsize=14, color='white')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/scaling_{config["scaling"]}.png', 
                   facecolor='black', bbox_inches='tight')
        plt.close()
    
    # =====================================
    # 5. 文字方向参数
    # =====================================
    print("5️⃣ 文字方向参数")
    
    orientation_configs = [
        {"prefer_horizontal": 1.0, "desc": "全部水平排列"},
        {"prefer_horizontal": 0.8, "desc": "主要水平，少量垂直"},
        {"prefer_horizontal": 0.5, "desc": "水平垂直各半"},
        {"prefer_horizontal": 0.2, "desc": "主要垂直，少量水平"},
        {"prefer_horizontal": 0.0, "desc": "全部垂直排列"}
    ]
    
    for config in orientation_configs:
        wc = WordCloud(
            width=800, height=600,
            background_color='black',
            color_func=lambda *args, **kwargs: 'white',
            max_words=80,
            prefer_horizontal=config["prefer_horizontal"],
            random_state=42
        ).generate_from_frequencies(word_frequencies)
        
        plt.figure(figsize=(10, 8))
        plt.imshow(wc, interpolation='bilinear')
        plt.title(f'水平偏好: {config["prefer_horizontal"]} - {config["desc"]}', 
                 fontsize=14, color='white')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/orientation_{config["prefer_horizontal"]}.png', 
                   facecolor='black', bbox_inches='tight')
        plt.close()
    
    # =====================================
    # 6. 边距和步长参数
    # =====================================
    print("6️⃣ 边距和步长参数")
    
    margin_configs = [
        {"margin": 2, "font_step": 1, "desc": "最小边距，最精细调整"},
        {"margin": 5, "font_step": 2, "desc": "小边距，精细调整"},
        {"margin": 10, "font_step": 4, "desc": "中等边距，标准调整"},
        {"margin": 20, "font_step": 8, "desc": "大边距，快速调整"}
    ]
    
    for config in margin_configs:
        wc = WordCloud(
            width=800, height=600,
            background_color='black',
            color_func=lambda *args, **kwargs: 'white',
            max_words=100,
            margin=config["margin"],
            font_step=config["font_step"],
            random_state=42
        ).generate_from_frequencies(word_frequencies)
        
        plt.figure(figsize=(10, 8))
        plt.imshow(wc, interpolation='bilinear')
        plt.title(f'边距: {config["margin"]}, 字体步长: {config["font_step"]} - {config["desc"]}', 
                 fontsize=14, color='white')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/margin_{config["margin"]}_step_{config["font_step"]}.png', 
                   facecolor='black', bbox_inches='tight')
        plt.close()
    
    # =====================================
    # 7. 大小写处理参数
    # =====================================
    print("7️⃣ 大小写处理参数")
    
    # 准备不同大小写的词汇
    case_variations = {}
    
    # 原始词汇（小写）
    original_words = {k: v for k, v in list(word_frequencies.items())[:50]}
    
    # 全部大写
    upper_words = {k.upper(): v for k, v in original_words.items()}
    
    # 首字母大写
    title_words = {k.title(): v for k, v in original_words.items()}
    
    # 混合大小写（随机）
    import random
    random.seed(42)
    mixed_words = {}
    for k, v in original_words.items():
        if random.random() > 0.5:
            mixed_words[k.upper()] = v
        else:
            mixed_words[k.lower()] = v
    
    case_configs = [
        {"words": original_words, "name": "全小写", "desc": "统一小写，简洁风格"},
        {"words": upper_words, "name": "全大写", "desc": "强调效果，醒目突出"},
        {"words": title_words, "name": "首字母大写", "desc": "正式风格，易读性好"},
        {"words": mixed_words, "name": "混合大小写", "desc": "变化丰富，视觉层次"}
    ]
    
    for config in case_configs:
        wc = WordCloud(
            width=800, height=600,
            background_color='black',
            color_func=lambda *args, **kwargs: 'white',
            max_words=50,
            random_state=42
        ).generate_from_frequencies(config["words"])
        
        plt.figure(figsize=(10, 8))
        plt.imshow(wc, interpolation='bilinear')
        plt.title(f'{config["name"]} - {config["desc"]}', 
                 fontsize=14, color='white')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/case_{config["name"]}.png', 
                   facecolor='black', bbox_inches='tight')
        plt.close()
    
    # =====================================
    # 8. 背景颜色参数
    # =====================================
    print("8️⃣ 背景颜色参数")
    
    background_configs = [
        {"bg": "black", "text": "white", "desc": "经典黑底白字"},
        {"bg": "white", "text": "black", "desc": "简洁白底黑字"},
        {"bg": "#1a1a2e", "text": "#eee", "desc": "深蓝底浅色字"},
        {"bg": "#16213e", "text": "#0f3460", "desc": "深色主题"},
        {"bg": "#2c3e50", "text": "#ecf0f1", "desc": "现代灰色主题"}
    ]
    
    for config in background_configs:
        wc = WordCloud(
            width=800, height=600,
            background_color=config["bg"],
            color_func=lambda *args, **kwargs: config["text"],
            max_words=80,
            random_state=42
        ).generate_from_frequencies(word_frequencies)
        
        plt.figure(figsize=(10, 8))
        plt.imshow(wc, interpolation='bilinear')
        plt.title(f'背景: {config["bg"]} - {config["desc"]}', 
                 fontsize=14, color=config["text"])
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/background_{config["bg"].replace("#", "")}.png', 
                   facecolor=config["bg"], bbox_inches='tight')
        plt.close()
    
    # =====================================
    # 生成参数说明文档
    # =====================================
    print("📋 生成参数说明文档...")
    
    parameters_doc = {
        "wordcloud_parameters": {
            "基础参数": {
                "width": {
                    "描述": "词云图片宽度（像素）",
                    "默认值": 400,
                    "建议范围": "400-2000",
                    "影响": "影响图片尺寸和词汇布局空间"
                },
                "height": {
                    "描述": "词云图片高度（像素）",
                    "默认值": 200,
                    "建议范围": "200-1500",
                    "影响": "影响图片尺寸和词汇布局空间"
                },
                "background_color": {
                    "描述": "背景颜色",
                    "默认值": "black",
                    "选项": ["black", "white", "transparent", "任何颜色代码"],
                    "影响": "影响整体视觉效果和文字对比度"
                }
            },
            "词汇控制参数": {
                "max_words": {
                    "描述": "显示的最大词汇数量",
                    "默认值": 200,
                    "建议范围": "20-500",
                    "影响": "控制词云密度和信息量"
                },
                "min_word_length": {
                    "描述": "最小词长度",
                    "默认值": 0,
                    "建议范围": "2-6",
                    "影响": "过滤过短的词汇"
                },
                "max_word_length": {
                    "描述": "最大词长度",
                    "默认值": "无限制",
                    "建议范围": "10-50",
                    "影响": "过滤过长的词汇"
                },
                "stopwords": {
                    "描述": "停用词集合",
                    "默认值": "内置英文停用词",
                    "类型": "set类型",
                    "影响": "移除不重要的常用词"
                }
            },
            "字体参数": {
                "font_path": {
                    "描述": "字体文件路径",
                    "默认值": "系统默认字体",
                    "类型": "字符串路径",
                    "影响": "影响文字外观风格"
                },
                "min_font_size": {
                    "描述": "最小字体大小",
                    "默认值": 4,
                    "建议范围": "8-30",
                    "影响": "控制最小词汇的可读性"
                },
                "max_font_size": {
                    "描述": "最大字体大小",
                    "默认值": 100,
                    "建议范围": "40-200",
                    "影响": "控制最大词汇的显著性"
                },
                "font_step": {
                    "描述": "字体大小调整步长",
                    "默认值": 1,
                    "建议范围": "1-10",
                    "影响": "影响布局精度和生成速度"
                }
            },
            "布局参数": {
                "relative_scaling": {
                    "描述": "相对缩放因子",
                    "默认值": 0.5,
                    "范围": "0.0-1.0",
                    "影响": "控制词汇大小差异程度"
                },
                "prefer_horizontal": {
                    "描述": "水平排列偏好",
                    "默认值": 0.7,
                    "范围": "0.0-1.0",
                    "影响": "控制水平vs垂直排列比例"
                },
                "margin": {
                    "描述": "词汇间边距",
                    "默认值": 2,
                    "建议范围": "1-20",
                    "影响": "控制词汇间距离和密度"
                }
            },
            "高级参数": {
                "collocations": {
                    "描述": "是否允许词汇搭配",
                    "默认值": True,
                    "选项": [True, False],
                    "影响": "避免相关词汇重复出现"
                },
                "random_state": {
                    "描述": "随机数种子",
                    "默认值": "随机",
                    "类型": "整数",
                    "影响": "确保结果可重现"
                },
                "normalize_plurals": {
                    "描述": "标准化复数形式",
                    "默认值": True,
                    "选项": [True, False],
                    "影响": "合并单复数形式"
                },
                "include_numbers": {
                    "描述": "是否包含数字",
                    "默认值": False,
                    "选项": [True, False],
                    "影响": "控制是否显示数字"
                }
            },
            "颜色参数": {
                "color_func": {
                    "描述": "自定义颜色函数",
                    "默认值": "默认彩色方案",
                    "类型": "函数",
                    "影响": "完全自定义词汇颜色"
                },
                "colormap": {
                    "描述": "matplotlib颜色映射",
                    "默认值": "随机颜色",
                    "选项": ["viridis", "plasma", "cool", "hot等"],
                    "影响": "使用预定义颜色方案"
                }
            }
        }
    }
    
    # 保存参数文档
    doc_path = os.path.join(output_dir, "wordcloud_parameters_guide.json")
    with open(doc_path, 'w', encoding='utf-8') as f:
        json.dump(parameters_doc, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 参数演示完成！")
    print(f"📁 演示图片保存在: {output_dir}/")
    print(f"📖 参数说明文档: {doc_path}")
    print(f"🎨 总共生成了 {len(size_configs) + len(word_count_configs) + len(font_size_configs) + len(scaling_configs) + len(orientation_configs) + len(margin_configs) + len(case_configs) + len(background_configs)} 个演示图片")

if __name__ == "__main__":
    wordcloud_parameters_demo()