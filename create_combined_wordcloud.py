#!/usr/bin/env python3
"""
创建合并词云图
合并所有10篇论文的词频数据，生成汇总词云
"""

import os
import sys
import json
import matplotlib
matplotlib.use('Agg')
from collections import Counter

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.wordcloud_generator import WordCloudGenerator
from data.papers_config import PAPERS_CONFIG

def create_combined_wordcloud():
    """创建合并词云"""
    print("🚀 开始创建合并词云...")
    
    # 收集所有词频数据
    combined_frequencies = Counter()
    paper_weights = {}
    successful_papers = []
    
    output_dir = "output"
    
    for paper_info in PAPERS_CONFIG:
        arxiv_id = paper_info['arxiv_id']
        title = paper_info['title']
        
        # 查找对应的词频文件
        freq_file = os.path.join(output_dir, f"{arxiv_id}_frequencies.json")
        
        if os.path.exists(freq_file):
            try:
                with open(freq_file, 'r', encoding='utf-8') as f:
                    freq_data = json.load(f)
                
                # 获取词频数据
                top_words = freq_data.get('top_words', [])
                paper_total_freq = sum(item['frequency'] for item in top_words)
                
                # 根据论文总词频设置权重（归一化）
                paper_weights[arxiv_id] = min(paper_total_freq / 1000, 2.0)  # 最大权重2.0
                
                # 添加到合并词频中
                for item in top_words:
                    word = item['word']
                    freq = item['frequency']
                    # 应用论文权重
                    weighted_freq = int(freq * paper_weights[arxiv_id])
                    combined_frequencies[word] += weighted_freq
                
                successful_papers.append({
                    'arxiv_id': arxiv_id,
                    'title': title,
                    'word_count': len(top_words),
                    'total_frequency': paper_total_freq,
                    'weight': paper_weights[arxiv_id]
                })
                
                print(f"✅ 加载 {arxiv_id}: {len(top_words)} 个词汇, 权重 {paper_weights[arxiv_id]:.2f}")
                
            except Exception as e:
                print(f"❌ 无法加载 {arxiv_id}: {e}")
        else:
            print(f"⚠️  未找到词频文件: {freq_file}")
    
    if not combined_frequencies:
        print("❌ 没有找到词频数据！")
        return
    
    print(f"\n📊 合并统计:")
    print(f"   成功论文数: {len(successful_papers)}")
    print(f"   总计词汇数: {len(combined_frequencies)}")
    print(f"   总计词频: {sum(combined_frequencies.values())}")
    
    # 显示论文权重信息
    print(f"\n⚖️  论文权重分布:")
    for paper in successful_papers:
        print(f"   {paper['arxiv_id']}: {paper['weight']:.2f} ({paper['word_count']} 词汇)")
    
    # 创建词云生成器
    generator = WordCloudGenerator(
        width=1600,
        height=1200,
        background_color='white',
        max_words=300,
        output_dir=output_dir
    )
    
    print(f"\n🎨 生成合并词云...")
    
    # 生成主合并词云
    wordcloud = generator.generate_wordcloud(
        word_frequencies=combined_frequencies,
        title="Combined Analysis: 10 Scientific Papers",
        color_scheme='scientific',
        enhance_scientific_terms=True
    )
    
    # 保存合并词云
    combined_path = generator.save_wordcloud(
        wordcloud,
        "combined_all_papers_wordcloud",
        title="合并词云分析 - 10篇科学文献",
        add_stats=True
    )
    
    print(f"✅ 合并词云已保存: {combined_path}")
    
    # 生成高频词汇报告
    print(f"\n📈 前30个全局高频词汇:")
    top_global_words = combined_frequencies.most_common(30)
    for i, (word, freq) in enumerate(top_global_words, 1):
        print(f"   {i:2d}. {word:<20} : {freq:>4d}")
    
    # 导出合并词频数据
    export_path = generator.export_word_frequencies(
        combined_frequencies,
        "combined_all_papers_frequencies",
        top_n=200
    )
    print(f"✅ 合并词频数据已导出: {export_path}")
    
    # 创建不同颜色方案的词云样式画廊
    print(f"\n🎨 生成样式画廊...")
    
    # 选择前100个高频词用于样式展示
    top_100_words = dict(combined_frequencies.most_common(100))
    
    color_schemes = ['scientific', 'physics', 'cool', 'warm']
    gallery_paths = []
    
    for scheme in color_schemes:
        style_wordcloud = generator.generate_wordcloud(
            word_frequencies=top_100_words,
            title=f"Combined Analysis - {scheme.title()} Style",
            color_scheme=scheme,
            enhance_scientific_terms=True
        )
        
        style_path = generator.save_wordcloud(
            style_wordcloud,
            f"combined_style_{scheme}",
            title=f"合并词云 - {scheme.title()}风格"
        )
        gallery_paths.append(style_path)
        print(f"   ✅ {scheme}风格: {os.path.basename(style_path)}")
    
    # 创建圆形词云
    print(f"\n🔵 生成圆形合并词云...")
    circle_mask = generator.create_shape_mask('circle', (1200, 1200))
    circle_wordcloud = generator.generate_wordcloud(
        word_frequencies=top_100_words,
        title="Combined Analysis - Circular",
        color_scheme='physics',
        shape_mask=circle_mask,
        enhance_scientific_terms=True
    )
    
    circle_path = generator.save_wordcloud(
        circle_wordcloud,
        "combined_circular_wordcloud",
        title="圆形合并词云 - 10篇科学文献"
    )
    print(f"✅ 圆形词云已保存: {circle_path}")
    
    # 生成最终报告
    print(f"\n📋 生成最终报告...")
    
    final_report = {
        "summary": {
            "total_papers": len(successful_papers),
            "total_unique_words": len(combined_frequencies),
            "total_word_frequency": sum(combined_frequencies.values()),
            "average_paper_weight": sum(paper_weights.values()) / len(paper_weights) if paper_weights else 0
        },
        "papers_processed": successful_papers,
        "top_30_global_words": [{"word": word, "frequency": freq} for word, freq in top_global_words],
        "generated_files": {
            "combined_wordcloud": os.path.basename(combined_path),
            "circular_wordcloud": os.path.basename(circle_path),
            "style_gallery": [os.path.basename(path) for path in gallery_paths],
            "frequency_data": os.path.basename(export_path)
        }
    }
    
    report_path = os.path.join(output_dir, "combined_wordcloud_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 最终报告已保存: {report_path}")
    
    print(f"\n🎉 合并词云创建完成！")
    print(f"   主词云: {os.path.basename(combined_path)}")
    print(f"   圆形词云: {os.path.basename(circle_path)}")
    print(f"   样式画廊: {len(gallery_paths)} 个风格")
    print(f"   所有文件保存在: {output_dir}/")

if __name__ == "__main__":
    create_combined_wordcloud()