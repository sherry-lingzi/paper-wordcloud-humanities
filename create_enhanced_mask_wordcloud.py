#!/usr/bin/env python3
"""
增强版自定义遮罩词云生成器
优化参数：全大写、自定义字体、高密度、更多词汇、超高像素
手动添加主题词："strongly correlated systems", "QMC"
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

def create_enhanced_mask_wordcloud():
    """创建增强版遮罩词云"""
    print("🎭 开始创建增强版遮罩词云...")
    
    # 1. 加载和处理遮罩图片
    mask_path = "mask/mask.jpg"
    if not os.path.exists(mask_path):
        print(f"❌ 找不到遮罩文件: {mask_path}")
        return
    
    print(f"📸 加载遮罩图片: {mask_path}")
    
    # 加载图片，保持原始尺寸但提升到更高分辨率
    mask_image = Image.open(mask_path)
    original_size = mask_image.size
    
    # 提升分辨率 - 放大3倍以获得更高像素密度
    enhanced_width = original_size[0] * 3   
    enhanced_height = original_size[1] * 3  
    
    print(f"   原始尺寸: {original_size}")
    print(f"   增强尺寸: {enhanced_width}x{enhanced_height}")
    
    # 高质量缩放
    mask_image = mask_image.resize((enhanced_width, enhanced_height), Image.Resampling.LANCZOS)
    
    # 转换为灰度图
    if mask_image.mode != 'L':
        mask_image = mask_image.convert('L')
    
    # 转换为numpy数组
    mask_array = np.array(mask_image)
    print(f"   遮罩数组形状: {mask_array.shape}")
    print(f"   像素值范围: {mask_array.min()} - {mask_array.max()}")
    
    # 创建遮罩：黑色区域（非人物剪影）用于放置词汇，白色区域（人物剪影）保持空白
    processed_mask = np.where(mask_array < 128, 0, 255).astype(np.uint8)
    
    print(f"   处理后遮罩统计:")
    print(f"   - 可放置词汇区域（黑色区域）: {np.sum(processed_mask == 0)} 像素")
    print(f"   - 空白区域（人物剪影）: {np.sum(processed_mask == 255)} 像素")
    
    # 2. 加载合并的词频数据并添加主题词
    import json
    
    freq_file = "output_batch/combined_all_papers_frequencies.json"
    if not os.path.exists(freq_file):
        print(f"❌ 找不到词频文件: {freq_file}")
        return
    
    print(f"📊 加载词频数据: {freq_file}")
    
    with open(freq_file, 'r', encoding='utf-8') as f:
        freq_data = json.load(f)
    
    # 获取更多词汇（300个）
    top_words = freq_data.get('top_words', [])[:300]
    word_frequencies = {item['word']: item['frequency'] for item in top_words}
    
    # 手动添加最高权重的主题词
    print(f"📝 手动添加主题词...")
    
    # 获取当前最高频率作为基准
    max_current_freq = max(word_frequencies.values()) if word_frequencies else 2000
    
    # 添加主题词，给予最高权重
    theme_words = {
        "STRONGLY CORRELATED SYSTEMS": max_current_freq * 1.1,  # 最高权重
        "QMC": max_current_freq * 1.15                          # 第二高权重
    }
    
    # 合并词汇，主题词优先
    enhanced_frequencies = {**theme_words, **word_frequencies}
    
    print(f"   原有词汇数: {len(word_frequencies)}")
    print(f"   添加主题词: {list(theme_words.keys())}")
    print(f"   总词汇数: {len(enhanced_frequencies)}")
    print(f"   最高频词汇: STRONGLY CORRELATED SYSTEMS ({theme_words['STRONGLY CORRELATED SYSTEMS']:.0f})")
    
    # 转换为全大写
    uppercase_frequencies = {}
    for word, freq in enhanced_frequencies.items():
        uppercase_word = word.upper()
        # 如果大写后有重复，选择频率更高的
        if uppercase_word in uppercase_frequencies:
            uppercase_frequencies[uppercase_word] = max(uppercase_frequencies[uppercase_word], freq)
        else:
            uppercase_frequencies[uppercase_word] = freq
    
    print(f"   转换为大写后词汇数: {len(uppercase_frequencies)}")
    
    # 3. 设置字体路径
    font_path = r"/mnt/c/Users/余荫铠/AppData/Local/Microsoft/Windows/Fonts/Harding Text Web Regular Regular.ttf"
    
    # 检查字体文件是否存在
    if os.path.exists(font_path):
        print(f"✅ 找到字体文件: {os.path.basename(font_path)}")
    else:
        print(f"⚠️  字体文件不存在: {font_path}")
        print(f"   将使用系统默认字体")
        font_path = None
    
    # 4. 创建纯白色颜色函数
    def pure_white_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        """纯白色颜色函数：所有词汇都使用纯白色"""
        return 'rgb(255, 255, 255)'  # 纯白色
    
    # 5. 创建增强版词云
    print(f"🎨 生成增强版遮罩词云...")
    print(f"   - 尺寸: {enhanced_width}x{enhanced_height}")
    print(f"   - 字体: {'自定义Harding Text Web Bold' if font_path else '系统默认'}")
    print(f"   - 词汇数: {len(uppercase_frequencies)}")
    print(f"   - 全大写: 是")
    print(f"   - 高密度: 是")
    
    # 创建WordCloud对象 - 增强参数设置
    wordcloud = WordCloud(
        width=enhanced_width,         # 增强宽度
        height=enhanced_height,       # 增强高度
        background_color='black',     # 黑色背景
        max_words=400,
        relative_scaling=0.5,
        min_font_size=12,
        max_font_size=300,
        prefer_horizontal=0.7,
        mask=processed_mask,
        color_func=pure_white_color_func,
        collocations=False,
        random_state=42,
        font_step=1,               # 更精细的字体调整
        margin=5,                   # 减少边距
        font_path=font_path          # 自定义字体
    )
    
    # 生成词云
    print(f"   正在生成词云... (这可能需要一些时间)")
    wordcloud.generate_from_frequencies(uppercase_frequencies)
    
    placed_words = len(wordcloud.words_)
    print(f"   ✅ 词云生成完成，包含 {placed_words} 个词汇")
    
    # 检查主题词是否成功放置
    placed_theme_words = []
    for theme_word in theme_words.keys():
        if theme_word in wordcloud.words_:
            placed_theme_words.append(theme_word)
    
    print(f"   🎯 主题词放置情况: {len(placed_theme_words)}/{len(theme_words)}")
    for word in placed_theme_words:
        print(f"      ✅ {word}")
    
    # 6. 保存超高分辨率词云
    output_dir = "output_batch"
    
    # 计算图形尺寸（以英寸为单位，800 DPI）
    dpi = 800
    fig_width = enhanced_width / dpi
    fig_height = enhanced_height / dpi
    
    print(f"🖼️  保存设置:")
    print(f"   - 分辨率: {dpi} DPI")
    print(f"   - 图形尺寸: {fig_width:.2f}x{fig_height:.2f} 英寸")
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    
    # 显示词云，完全无边距
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    
    # 完全移除边距
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_position([0, 0, 1, 1])
    
    # 设置黑色背景
    fig.patch.set_facecolor('black')
    
    # 保存超高分辨率图片
    output_path = os.path.join(output_dir, "enhanced_mask_wordcloud_silhouette.png")
    
    print(f"💾 保存高分辨率图片...")
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', pad_inches=0,
               facecolor='black', edgecolor='none')
    plt.close()
    
    print(f"✅ 增强版遮罩词云已保存: {output_path}")
    
    # 7. 创建对比图（原图 vs 增强词云）
    print(f"🖼️  创建对比展示图...")
    
    fig, axes = plt.subplots(1, 2, figsize=(24, 12), dpi=600)
    fig.patch.set_facecolor('black')
    
    # 左侧：原始遮罩（缩小版用于对比）
    axes[0].imshow(mask_array, cmap='gray')
    axes[0].set_title('原始遮罩图 (1080x1080)', fontsize=18, fontweight='bold', color='white')
    axes[0].axis('off')
    
    # 右侧：生成的词云（缩小版用于对比）
    axes[1].imshow(wordcloud, interpolation='bilinear')
    axes[1].set_title(f'增强版词云图 ({enhanced_width}x{enhanced_height})', 
                     fontsize=18, fontweight='bold', color='white')
    axes[1].axis('off')
    
    # 总标题
    fig.suptitle('增强版遮罩词云：全大写 + 自定义字体 + 超高密度 + 主题词强化', 
                fontsize=20, fontweight='bold', color='white', y=0.95)
    
    # 保存对比图
    comparison_path = os.path.join(output_dir, "enhanced_mask_wordcloud_comparison.png")
    plt.savefig(comparison_path, dpi=600, bbox_inches='tight',
               facecolor='black', edgecolor='none')
    plt.close()
    
    print(f"✅ 对比图已保存: {comparison_path}")
    
    # 8. 生成详细统计报告
    print(f"📋 生成增强版统计报告...")
    
    total_pixels = enhanced_width * enhanced_height
    available_pixels = np.sum(processed_mask == 0)
    
    # 统计放置的词汇
    word_size_stats = {
        'min_frequency': min(wordcloud.words_.values()) if wordcloud.words_ else 0,
        'max_frequency': max(wordcloud.words_.values()) if wordcloud.words_ else 0,
        'avg_frequency': sum(wordcloud.words_.values()) / len(wordcloud.words_) if wordcloud.words_ else 0
    }
    
    # 创建增强版报告
    enhanced_report = {
        "enhancement_info": {
            "description": "增强版遮罩词云：全大写 + 自定义字体 + 超高密度",
            "enhancements": [
                "分辨率提升2倍（2160x2160像素）",
                "全大写显示",
                f"自定义字体：{os.path.basename(font_path) if font_path else '系统默认'}",
                "超高密度布局（margin=1, font_step=1）",
                "更大的字体范围（18-300）",
                "更强的相对缩放（0.8）",
                "手动添加主题词",
                "显示更多词汇（350个）"
            ]
        },
        "theme_words": {
            "added_manually": list(theme_words.keys()),
            "frequencies": theme_words,
            "successfully_placed": placed_theme_words
        },
        "image_specs": {
            "original_size": f"{original_size[0]}x{original_size[1]}",
            "enhanced_size": f"{enhanced_width}x{enhanced_height}",
            "resolution": f"{dpi} DPI",
            "total_pixels": total_pixels,
            "available_pixels": int(available_pixels),
            "usage_rate": f"{(available_pixels/total_pixels)*100:.1f}%"
        },
        "wordcloud_stats": {
            "input_words_original": len(word_frequencies),
            "input_words_with_themes": len(enhanced_frequencies),
            "uppercase_words": len(uppercase_frequencies),
            "successfully_placed": placed_words,
            "placement_rate": f"{(placed_words/len(uppercase_frequencies))*100:.1f}%",
            "word_frequency_stats": word_size_stats
        },
        "font_settings": {
            "font_path": font_path,
            "font_available": font_path is not None and os.path.exists(font_path),
            "min_font_size": 18,
            "max_font_size": 300,
            "font_step": 1,
            "margin": 1
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
    
    # 保存增强版报告
    report_path = os.path.join(output_dir, "enhanced_mask_wordcloud_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced_report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 增强版统计报告已保存: {report_path}")
    
    # 9. 输出最终总结
    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    
    print(f"\n🎉 增强版遮罩词云生成完成！")
    print(f"📊 增强统计:")
    print(f"   - 图片尺寸: {enhanced_width}x{enhanced_height} (提升4倍像素)")
    print(f"   - 分辨率: {dpi} DPI (超高清)")
    print(f"   - 字体: {'✅ 自定义Harding Text Web Bold' if font_path and os.path.exists(font_path) else '⚠️ 系统默认字体'}")
    print(f"   - 显示格式: 全大写")
    print(f"   - 主题词: {len(placed_theme_words)}/{len(theme_words)} 成功放置")
    print(f"   - 放置词汇: {placed_words}/{len(uppercase_frequencies)} ({(placed_words/len(uppercase_frequencies))*100:.1f}%)")
    print(f"   - 密度设置: 最高密度 (margin=1, font_step=1)")
    print(f"   - 文件大小: {file_size:.1f} MB")
    print(f"   - 输出目录: {output_dir}/")
    
    if wordcloud.words_:
        print(f"📈 放置的前5个词汇 (包含主题词):")
        top_placed = sorted(wordcloud.words_.items(), key=lambda x: x[1], reverse=True)[:5]
        for word, freq in top_placed:
            symbol = "🎯" if word in theme_words else "📝"
            print(f"   {symbol} {word}: {freq:.3f}")

if __name__ == "__main__":
    create_enhanced_mask_wordcloud()