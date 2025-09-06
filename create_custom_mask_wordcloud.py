#!/usr/bin/env python3
"""
使用自定义遮罩创建词云图
在用户提供的人物剪影遮罩中生成黑底白字的词云
"""

import os
import sys
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.wordcloud_generator import WordCloudGenerator
from wordcloud import WordCloud

def create_custom_mask_wordcloud():
    """使用自定义遮罩创建词云"""
    print("🎭 开始创建自定义遮罩词云...")
    
    # 1. 加载和处理遮罩图片
    mask_path = "mask/mask.jpg"
    if not os.path.exists(mask_path):
        print(f"❌ 找不到遮罩文件: {mask_path}")
        return
    
    print(f"📸 加载遮罩图片: {mask_path}")
    
    # 加载图片
    mask_image = Image.open(mask_path)
    print(f"   原始尺寸: {mask_image.size}")
    
    # 调整图片尺寸（保持宽高比）
    target_width = 800
    width, height = mask_image.size
    target_height = int(height * target_width / width)
    
    mask_image = mask_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    print(f"   调整后尺寸: {mask_image.size}")
    
    # 转换为灰度图
    if mask_image.mode != 'L':
        mask_image = mask_image.convert('L')
    
    # 转换为numpy数组
    mask_array = np.array(mask_image)
    print(f"   遮罩数组形状: {mask_array.shape}")
    print(f"   像素值范围: {mask_array.min()} - {mask_array.max()}")
    
    # 创建遮罩：白色区域（人物剪影）用于放置词汇，黑色区域保持空白
    # WordCloud的遮罩约定：255=不放置词汇，其他值=可以放置词汇
    processed_mask = np.where(mask_array > 128, 0, 255).astype(np.uint8)
    
    print(f"   处理后遮罩统计:")
    print(f"   - 可放置词汇区域: {np.sum(processed_mask == 0)} 像素")
    print(f"   - 空白区域: {np.sum(processed_mask == 255)} 像素")
    
    # 2. 加载合并的词频数据
    import json
    
    freq_file = "output_batch/combined_all_papers_frequencies.json"
    if not os.path.exists(freq_file):
        print(f"❌ 找不到词频文件: {freq_file}")
        return
    
    print(f"📊 加载词频数据: {freq_file}")
    
    with open(freq_file, 'r', encoding='utf-8') as f:
        freq_data = json.load(f)
    
    # 获取前150个高频词汇（适合人物轮廓）
    top_words = freq_data.get('top_words', [])[:150]
    word_frequencies = {item['word']: item['frequency'] for item in top_words}
    
    print(f"   加载词汇数: {len(word_frequencies)}")
    print(f"   最高频词汇: {top_words[0]['word']} ({top_words[0]['frequency']})")
    
    # 3. 创建自定义颜色函数（白色为主，略带蓝色调）
    def white_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        """自定义颜色函数：生成白色到浅蓝色的词汇"""
        # 科学术语使用纯白色
        scientific_terms = ['quantum', 'spin', 'phase', 'lattice', 'simulation', 
                          'critical', 'state', 'hamiltonian', 'dirac', 'symmetry']
        
        if word.lower() in scientific_terms:
            return 'rgb(255, 255, 255)'  # 纯白色
        else:
            # 其他词汇使用白色到浅蓝色
            np.random.seed(hash(word) % 2**32)
            blue_component = np.random.randint(200, 255)
            return f'rgb(255, 255, {blue_component})'
    
    # 4. 创建词云
    print(f"🎨 生成遮罩词云...")
    
    # 创建WordCloud对象
    wordcloud = WordCloud(
        width=target_width,
        height=target_height,
        background_color='black',  # 黑色背景
        max_words=150,
        relative_scaling=0.6,
        min_font_size=8,
        max_font_size=60,
        prefer_horizontal=0.8,
        mask=processed_mask,
        color_func=white_color_func,
        collocations=False,
        random_state=42
    )
    
    # 生成词云
    wordcloud.generate_from_frequencies(word_frequencies)
    
    print(f"   词云生成完成，包含 {len(wordcloud.words_)} 个词汇")
    
    # 5. 保存词云
    output_dir = "output_batch"
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(12, 15), dpi=300)
    
    # 显示词云
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    
    # 添加标题
    ax.set_title('科学文献词云 - 人物剪影\n10篇量子物理论文合并分析', 
                fontsize=16, fontweight='bold', color='white', pad=20)
    
    # 设置黑色背景
    fig.patch.set_facecolor('black')
    
    # 保存高分辨率图片
    output_path = os.path.join(output_dir, "custom_mask_wordcloud_silhouette.png")
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', 
               facecolor='black', edgecolor='none')
    plt.close()
    
    print(f"✅ 遮罩词云已保存: {output_path}")
    
    # 6. 创建对比图（原始遮罩 + 生成的词云）
    print(f"🖼️  创建对比展示图...")
    
    fig, axes = plt.subplots(1, 2, figsize=(20, 10), dpi=300)
    fig.patch.set_facecolor('black')
    
    # 左侧：原始遮罩
    axes[0].imshow(mask_array, cmap='gray')
    axes[0].set_title('原始遮罩图', fontsize=14, fontweight='bold', color='white')
    axes[0].axis('off')
    
    # 右侧：生成的词云
    axes[1].imshow(wordcloud, interpolation='bilinear')
    axes[1].set_title('生成的词云图', fontsize=14, fontweight='bold', color='white')
    axes[1].axis('off')
    
    # 总标题
    fig.suptitle('自定义遮罩词云生成对比', fontsize=18, fontweight='bold', 
                color='white', y=0.95)
    
    # 保存对比图
    comparison_path = os.path.join(output_dir, "mask_wordcloud_comparison.png")
    plt.savefig(comparison_path, dpi=300, bbox_inches='tight',
               facecolor='black', edgecolor='none')
    plt.close()
    
    print(f"✅ 对比图已保存: {comparison_path}")
    
    # 7. 生成统计报告
    print(f"📋 生成统计报告...")
    
    # 计算词云覆盖率
    wordcloud_array = np.array(wordcloud.to_array())
    total_mask_pixels = np.sum(processed_mask == 0)  # 可放置区域
    
    # 统计实际放置的词汇
    placed_words = len(wordcloud.words_)
    word_size_stats = {
        'min_frequency': min(wordcloud.words_.values()) if wordcloud.words_ else 0,
        'max_frequency': max(wordcloud.words_.values()) if wordcloud.words_ else 0,
        'avg_frequency': sum(wordcloud.words_.values()) / len(wordcloud.words_) if wordcloud.words_ else 0
    }
    
    # 创建报告
    report = {
        "mask_info": {
            "original_size": f"{width}x{height}",
            "processed_size": f"{target_width}x{target_height}",
            "available_pixels": int(total_mask_pixels),
            "mask_coverage": f"{(total_mask_pixels/(target_width*target_height))*100:.1f}%"
        },
        "wordcloud_stats": {
            "total_input_words": len(word_frequencies),
            "placed_words": placed_words,
            "placement_rate": f"{(placed_words/len(word_frequencies))*100:.1f}%",
            "word_frequency_stats": word_size_stats
        },
        "top_10_placed_words": [
            {"word": word, "frequency": freq} 
            for word, freq in sorted(wordcloud.words_.items(), 
                                   key=lambda x: x[1], reverse=True)[:10]
        ],
        "generated_files": {
            "main_wordcloud": os.path.basename(output_path),
            "comparison_image": os.path.basename(comparison_path)
        }
    }
    
    # 保存报告
    report_path = os.path.join(output_dir, "custom_mask_wordcloud_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 统计报告已保存: {report_path}")
    
    # 8. 输出最终总结
    print(f"\n🎉 自定义遮罩词云生成完成！")
    print(f"📊 处理统计:")
    print(f"   - 遮罩尺寸: {target_width}x{target_height}")
    print(f"   - 可用区域: {(total_mask_pixels/(target_width*target_height))*100:.1f}%")
    print(f"   - 放置词汇: {placed_words}/{len(word_frequencies)} ({(placed_words/len(word_frequencies))*100:.1f}%)")
    print(f"   - 输出文件: {output_dir}/")
    
    if wordcloud.words_:
        print(f"📈 放置的前5个词汇:")
        top_placed = sorted(wordcloud.words_.items(), key=lambda x: x[1], reverse=True)[:5]
        for word, freq in top_placed:
            print(f"   - {word}: {freq}")

if __name__ == "__main__":
    create_custom_mask_wordcloud()