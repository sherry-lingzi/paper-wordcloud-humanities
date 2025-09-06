#!/usr/bin/env python3
"""
修正版自定义遮罩词云生成器
在黑色区域（非人物剪影）生成纯白色词云，保持人物轮廓空白
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

from wordcloud import WordCloud

def create_corrected_mask_wordcloud():
    """创建修正版遮罩词云"""
    print("🎭 开始创建修正版遮罩词云...")
    
    # 1. 加载和处理遮罩图片
    mask_path = "mask/mask.jpg"
    if not os.path.exists(mask_path):
        print(f"❌ 找不到遮罩文件: {mask_path}")
        return
    
    print(f"📸 加载遮罩图片: {mask_path}")
    
    # 加载图片，保持原始尺寸
    mask_image = Image.open(mask_path)
    original_size = mask_image.size
    print(f"   原始尺寸: {original_size}")
    
    # 转换为灰度图
    if mask_image.mode != 'L':
        mask_image = mask_image.convert('L')
    
    # 转换为numpy数组
    mask_array = np.array(mask_image)
    print(f"   遮罩数组形状: {mask_array.shape}")
    print(f"   像素值范围: {mask_array.min()} - {mask_array.max()}")
    
    # 创建遮罩：黑色区域（非人物剪影）用于放置词汇，白色区域（人物剪影）保持空白
    # WordCloud的遮罩约定：255=不放置词汇，其他值=可以放置词汇
    processed_mask = np.where(mask_array < 128, 0, 255).astype(np.uint8)
    
    print(f"   处理后遮罩统计:")
    print(f"   - 可放置词汇区域（黑色区域）: {np.sum(processed_mask == 0)} 像素")
    print(f"   - 空白区域（人物剪影）: {np.sum(processed_mask == 255)} 像素")
    
    # 2. 加载合并的词频数据
    import json
    
    freq_file = "output_batch/combined_all_papers_frequencies.json"
    if not os.path.exists(freq_file):
        print(f"❌ 找不到词频文件: {freq_file}")
        return
    
    print(f"📊 加载词频数据: {freq_file}")
    
    with open(freq_file, 'r', encoding='utf-8') as f:
        freq_data = json.load(f)
    
    # 获取前200个高频词汇（黑色区域更大，可以放更多词汇）
    top_words = freq_data.get('top_words', [])[:200]
    word_frequencies = {item['word']: item['frequency'] for item in top_words}
    
    print(f"   加载词汇数: {len(word_frequencies)}")
    print(f"   最高频词汇: {top_words[0]['word']} ({top_words[0]['frequency']})")
    
    # 3. 创建纯白色颜色函数
    def pure_white_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        """纯白色颜色函数：所有词汇都使用纯白色"""
        return 'rgb(255, 255, 255)'  # 纯白色
    
    # 4. 创建词云
    print(f"🎨 生成遮罩词云...")
    
    # 创建WordCloud对象，尺寸与原图一致
    wordcloud = WordCloud(
        width=original_size[0],    # 与mask图片宽度一致
        height=original_size[1],   # 与mask图片高度一致
        background_color='black',  # 黑色背景
        max_words=200,
        relative_scaling=0.5,
        min_font_size=12,
        max_font_size=80,
        prefer_horizontal=0.7,
        mask=processed_mask,
        color_func=pure_white_color_func,
        collocations=False,
        random_state=42,
        font_step=1,               # 更精细的字体调整
        margin=2                   # 减少边距
    )
    
    # 生成词云
    wordcloud.generate_from_frequencies(word_frequencies)
    
    print(f"   词云生成完成，包含 {len(wordcloud.words_)} 个词汇")
    
    # 5. 保存高分辨率词云（无标题）
    output_dir = "output_batch"
    
    # 创建图形，尺寸与原图完全一致
    fig_width = original_size[0] / 600  # 600 DPI
    fig_height = original_size[1] / 600  # 600 DPI
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=600)
    
    # 显示词云，无边距
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    
    # 移除所有边距和空白
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_position([0, 0, 1, 1])
    
    # 设置黑色背景
    fig.patch.set_facecolor('black')
    
    # 保存超高分辨率图片
    output_path = os.path.join(output_dir, "corrected_mask_wordcloud_silhouette.png")
    
    plt.savefig(output_path, dpi=600, bbox_inches='tight', pad_inches=0,
               facecolor='black', edgecolor='none')
    plt.close()
    
    print(f"✅ 修正版遮罩词云已保存: {output_path}")
    
    # 6. 创建对比图
    print(f"🖼️  创建对比展示图...")
    
    fig, axes = plt.subplots(1, 2, figsize=(20, 10), dpi=600)
    fig.patch.set_facecolor('black')
    
    # 左侧：原始遮罩
    axes[0].imshow(mask_array, cmap='gray')
    axes[0].set_title('原始遮罩图', fontsize=16, fontweight='bold', color='white')
    axes[0].axis('off')
    
    # 右侧：生成的词云
    axes[1].imshow(wordcloud, interpolation='bilinear')
    axes[1].set_title('修正版词云图', fontsize=16, fontweight='bold', color='white')
    axes[1].axis('off')
    
    # 总标题
    fig.suptitle('修正版遮罩词云：词汇填充黑色区域，保持人物剪影空白', 
                fontsize=18, fontweight='bold', color='white', y=0.95)
    
    # 保存对比图
    comparison_path = os.path.join(output_dir, "corrected_mask_wordcloud_comparison.png")
    plt.savefig(comparison_path, dpi=600, bbox_inches='tight',
               facecolor='black', edgecolor='none')
    plt.close()
    
    print(f"✅ 对比图已保存: {comparison_path}")
    
    # 7. 生成统计报告
    print(f"📋 生成统计报告...")
    
    # 计算词云覆盖率
    total_mask_pixels = np.sum(processed_mask == 0)  # 可放置区域（黑色区域）
    total_pixels = original_size[0] * original_size[1]
    
    # 统计实际放置的词汇
    placed_words = len(wordcloud.words_)
    word_size_stats = {
        'min_frequency': min(wordcloud.words_.values()) if wordcloud.words_ else 0,
        'max_frequency': max(wordcloud.words_.values()) if wordcloud.words_ else 0,
        'avg_frequency': sum(wordcloud.words_.values()) / len(wordcloud.words_) if wordcloud.words_ else 0
    }
    
    # 创建报告
    report = {
        "correction_info": {
            "description": "词汇放置在黑色区域（非人物剪影），人物轮廓保持空白",
            "color_scheme": "纯白色字体",
            "background": "黑色背景"
        },
        "mask_info": {
            "image_size": f"{original_size[0]}x{original_size[1]}",
            "total_pixels": total_pixels,
            "available_pixels_black_area": int(total_mask_pixels),
            "black_area_coverage": f"{(total_mask_pixels/total_pixels)*100:.1f}%",
            "silhouette_area_coverage": f"{((total_pixels-total_mask_pixels)/total_pixels)*100:.1f}%"
        },
        "wordcloud_stats": {
            "resolution": "600 DPI",
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
    report_path = os.path.join(output_dir, "corrected_mask_wordcloud_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 统计报告已保存: {report_path}")
    
    # 8. 输出最终总结
    print(f"\n🎉 修正版遮罩词云生成完成！")
    print(f"📊 处理统计:")
    print(f"   - 图片尺寸: {original_size[0]}x{original_size[1]} (与原图一致)")
    print(f"   - 分辨率: 600 DPI")
    print(f"   - 黑色区域占比: {(total_mask_pixels/total_pixels)*100:.1f}% (词汇放置区域)")
    print(f"   - 人物剪影占比: {((total_pixels-total_mask_pixels)/total_pixels)*100:.1f}% (保持空白)")
    print(f"   - 放置词汇: {placed_words}/{len(word_frequencies)} ({(placed_words/len(word_frequencies))*100:.1f}%)")
    print(f"   - 字体颜色: 纯白色")
    print(f"   - 输出文件: {output_dir}/")
    
    if wordcloud.words_:
        print(f"📈 放置的前5个词汇:")
        top_placed = sorted(wordcloud.words_.items(), key=lambda x: x[1], reverse=True)[:5]
        for word, freq in top_placed:
            print(f"   - {word}: {freq:.3f}")
    
    # 9. 获取文件大小信息
    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    print(f"📁 文件大小: {file_size:.1f} MB")

if __name__ == "__main__":
    create_corrected_mask_wordcloud()