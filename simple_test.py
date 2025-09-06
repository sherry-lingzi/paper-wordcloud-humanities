#!/usr/bin/env python3
"""
简单的词云生成测试
"""

import os
import sys
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.html_fetcher import HTMLFetcher
from src.text_extractor import TextExtractor
from src.wordcloud_generator import WordCloudGenerator

def simple_test():
    """简单的测试流程"""
    print("开始简单测试...")
    
    # 1. 获取HTML内容
    print("1. 获取HTML内容...")
    fetcher = HTMLFetcher()
    test_arxiv_id = "2211.02002"
    html_content = fetcher.fetch_html_content(test_arxiv_id)
    
    if not html_content:
        print("❌ 无法获取HTML内容")
        return
    
    print(f"✅ 成功获取HTML内容 ({len(html_content)} 字符)")
    
    # 2. 提取文本
    print("2. 提取文本...")
    extractor = TextExtractor()
    extracted_text = extractor.extract_text_from_html(html_content)
    
    if not extracted_text.get('full_text'):
        print("❌ 无法提取文本")
        return
        
    print(f"✅ 成功提取文本 ({len(extracted_text['full_text'])} 字符)")
    print(f"   标题: {extracted_text['title'][:80]}...")
    
    # 3. 创建简单的词云
    print("3. 生成词云...")
    generator = WordCloudGenerator()
    
    # 简单处理文本
    text = extracted_text['full_text'].lower()
    # 移除过短的词
    words = [word for word in text.split() if len(word) > 3]
    processed_text = ' '.join(words)
    
    # 生成词云
    wordcloud = generator.generate_wordcloud(
        text=processed_text,
        title="Test Scientific WordCloud",
        color_scheme='scientific'
    )
    
    # 保存词云
    output_path = generator.save_wordcloud(
        wordcloud,
        "simple_test_wordcloud",
        title="SU(N) Fermions - Quantum Spin Liquid"
    )
    
    print(f"✅ 词云已生成并保存到: {output_path}")
    
    # 4. 显示统计信息
    print("\n📊 统计信息:")
    print(f"   处理前词数: {len(text.split())}")
    print(f"   处理后词数: {len(words)}")
    print(f"   词云中词数: {len(wordcloud.words_)}")
    
    if wordcloud.words_:
        top_words = sorted(wordcloud.words_.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"   前10个高频词:")
        for word, freq in top_words:
            print(f"     {word}: {freq}")
    
    print("\n🎉 简单测试完成！")

if __name__ == "__main__":
    simple_test()