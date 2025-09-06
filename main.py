#!/usr/bin/env python3
"""
科学文献词云生成器 - 主程序
批量处理arXiv论文并生成词云可视化
"""

import os
import sys
import time
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入自定义模块
try:
    from src.html_fetcher import HTMLFetcher
    from src.text_extractor import TextExtractor
    from src.science_nlp import ScienceNLP
    from src.wordcloud_generator import WordCloudGenerator
    from data.papers_config import PAPERS_CONFIG
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖包已安装: pip install -r requirements.txt")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wordcloud_generation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class WordCloudPipeline:
    """词云生成流水线"""
    
    def __init__(self, config: Dict = None):
        """
        初始化流水线
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 初始化各个组件
        self.html_fetcher = HTMLFetcher(
            cache_dir=self.config.get('cache_dir', 'data/cache'),
            delay=self.config.get('request_delay', 1.0)
        )
        
        self.text_extractor = TextExtractor(
            extract_abstract=self.config.get('extract_abstract', True),
            extract_introduction=self.config.get('extract_introduction', True),
            extract_conclusion=self.config.get('extract_conclusion', True),
            remove_math=self.config.get('remove_math', False)
        )
        
        self.nlp_processor = ScienceNLP(
            preserve_scientific_terms=self.config.get('preserve_scientific_terms', True),
            remove_academic_stopwords=self.config.get('remove_academic_stopwords', True),
            enable_lemmatization=self.config.get('enable_lemmatization', True)
        )
        
        self.wordcloud_generator = WordCloudGenerator(
            width=self.config.get('wordcloud_width', 1200),
            height=self.config.get('wordcloud_height', 800),
            background_color=self.config.get('background_color', 'white'),
            max_words=self.config.get('max_words', 200),
            output_dir=self.config.get('output_dir', 'output')
        )
        
        # 处理统计
        self.stats = {
            'processed_papers': 0,
            'failed_papers': 0,
            'generated_wordclouds': 0,
            'start_time': None,
            'end_time': None
        }
    
    def process_single_paper(self, paper_info: Dict) -> Optional[Dict]:
        """
        处理单篇论文
        
        Args:
            paper_info: 论文信息字典
            
        Returns:
            处理结果字典，失败时返回None
        """
        arxiv_id = paper_info['arxiv_id']
        title = paper_info['title']
        
        logger.info(f"开始处理论文: {arxiv_id} - {title}")
        
        try:
            # 1. 获取HTML内容
            html_content = self.html_fetcher.fetch_html_content(arxiv_id)
            if not html_content:
                logger.error(f"无法获取HTML内容: {arxiv_id}")
                return None
            
            # 2. 提取文本
            extracted_text = self.text_extractor.extract_text_from_html(html_content)
            if not extracted_text.get('full_text'):
                logger.error(f"无法提取文本内容: {arxiv_id}")
                return None
            
            # 3. 文本预处理
            processed_text = self.nlp_processor.preprocess_text(extracted_text['full_text'])
            if not processed_text:
                logger.error(f"文本预处理后为空: {arxiv_id}")
                return None
            
            # 4. 提取科学关键词
            keywords = self.nlp_processor.extract_scientific_keywords(processed_text, top_n=100)
            word_frequencies = dict(keywords)
            
            # 5. 生成词云
            wordcloud = self.wordcloud_generator.generate_wordcloud(
                word_frequencies=word_frequencies,
                title=f"{title[:50]}..." if len(title) > 50 else title,
                color_scheme='scientific',
                enhance_scientific_terms=True
            )
            
            # 6. 保存词云
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:50]  # 限制文件名长度
            filename = f"{arxiv_id}_{safe_title}"
            
            filepath = self.wordcloud_generator.save_wordcloud(
                wordcloud, 
                filename, 
                title=f"{arxiv_id}: {title}",
                add_stats=True
            )
            
            # 7. 导出词频数据
            freq_filepath = self.wordcloud_generator.export_word_frequencies(
                word_frequencies, 
                f"{arxiv_id}_frequencies"
            )
            
            # 8. 分析文本质量
            quality_analysis = self.nlp_processor.analyze_text_quality(processed_text)
            text_stats = self.nlp_processor.get_text_statistics(processed_text)
            
            self.stats['processed_papers'] += 1
            self.stats['generated_wordclouds'] += 1
            
            result = {
                'arxiv_id': arxiv_id,
                'title': title,
                'wordcloud_path': filepath,
                'frequencies_path': freq_filepath,
                'word_count': len(word_frequencies),
                'quality_score': quality_analysis.get('quality_score', 0),
                'text_stats': text_stats,
                'top_keywords': keywords[:10],
                'processing_time': time.time(),
                'success': True
            }
            
            logger.info(f"✓ 成功处理: {arxiv_id} | 质量分数: {quality_analysis.get('quality_score', 0):.3f}")
            return result
            
        except Exception as e:
            logger.error(f"✗ 处理失败 {arxiv_id}: {e}")
            self.stats['failed_papers'] += 1
            return {
                'arxiv_id': arxiv_id,
                'title': title,
                'error': str(e),
                'success': False
            }
    
    def process_all_papers(self, paper_configs: List[Dict] = None) -> Dict:
        """
        批量处理所有论文
        
        Args:
            paper_configs: 论文配置列表
            
        Returns:
            处理结果汇总
        """
        if paper_configs is None:
            paper_configs = PAPERS_CONFIG
        
        self.stats['start_time'] = datetime.now()
        total_papers = len(paper_configs)
        
        logger.info(f"开始批量处理 {total_papers} 篇论文")
        
        results = []
        successful_results = []
        
        for i, paper_info in enumerate(paper_configs, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"进度: {i}/{total_papers}")
            
            result = self.process_single_paper(paper_info)
            if result:
                results.append(result)
                if result.get('success'):
                    successful_results.append(result)
            
            # 避免请求过于频繁
            time.sleep(0.5)
        
        self.stats['end_time'] = datetime.now()
        
        # 生成汇总报告
        summary = self._generate_summary_report(results, successful_results)
        
        # 保存处理结果
        self._save_results(results, summary)
        
        logger.info(f"\n{'='*60}")
        logger.info("批量处理完成！")
        logger.info(f"成功: {self.stats['processed_papers']} | 失败: {self.stats['failed_papers']} | 总计: {total_papers}")
        
        return summary
    
    def _generate_summary_report(self, all_results: List[Dict], successful_results: List[Dict]) -> Dict:
        """生成汇总报告"""
        if not successful_results:
            return {"error": "没有成功处理的论文"}
        
        # 计算平均质量分数
        avg_quality = sum(r.get('quality_score', 0) for r in successful_results) / len(successful_results)
        
        # 统计总词数
        total_words = sum(r.get('word_count', 0) for r in successful_results)
        
        # 获取最高频词汇
        all_keywords = {}
        for result in successful_results:
            for word, freq in result.get('top_keywords', []):
                all_keywords[word] = all_keywords.get(word, 0) + freq
        
        top_global_keywords = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # 计算处理时间
        processing_time = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        summary = {
            'total_papers': len(all_results),
            'successful_papers': len(successful_results),
            'failed_papers': len(all_results) - len(successful_results),
            'success_rate': len(successful_results) / len(all_results) if all_results else 0,
            'average_quality_score': round(avg_quality, 3),
            'total_unique_words': total_words,
            'top_global_keywords': top_global_keywords,
            'processing_time_seconds': round(processing_time, 2),
            'generated_files': self.stats['generated_wordclouds'] * 2  # 词云+词频文件
        }
        
        return summary
    
    def _save_results(self, results: List[Dict], summary: Dict):
        """保存处理结果和汇总报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存详细结果
        results_file = os.path.join(self.wordcloud_generator.output_dir, f"processing_results_{timestamp}.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # 保存汇总报告
        summary_file = os.path.join(self.wordcloud_generator.output_dir, f"summary_report_{timestamp}.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"结果已保存: {results_file}")
        logger.info(f"汇总报告: {summary_file}")
    
    def generate_combined_analysis(self, successful_results: List[Dict]):
        """生成合并分析"""
        if not successful_results:
            return
        
        logger.info("生成合并词云分析...")
        
        # 收集所有文本
        all_texts = {}
        text_weights = {}
        
        for result in successful_results:
            arxiv_id = result['arxiv_id']
            # 重新获取处理后的文本（这里简化处理）
            quality_score = result.get('quality_score', 0.5)
            
            # 根据论文质量设置权重
            text_weights[arxiv_id] = max(quality_score, 0.1)
            
            # 从词频重构文本（简化方法）
            keywords = result.get('top_keywords', [])
            reconstructed_text = ' '.join([word for word, freq in keywords])
            all_texts[arxiv_id] = reconstructed_text
        
        # 生成合并词云
        try:
            combined_path = self.wordcloud_generator.generate_combined_wordcloud(
                all_texts, 
                weights=text_weights,
                title="Combined Analysis of All Papers"
            )
            logger.info(f"合并词云已生成: {combined_path}")
        except Exception as e:
            logger.error(f"生成合并词云失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="科学文献词云生成器")
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--single', '-s', help='处理单篇论文(arXiv ID)')
    parser.add_argument('--output', '-o', default='output', help='输出目录')
    parser.add_argument('--no-cache', action='store_true', help='不使用缓存')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 加载配置
    config = {
        'output_dir': args.output,
        'cache_dir': 'data/cache' if not args.no_cache else None
    }
    
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            config.update(json.load(f))
    
    # 初始化流水线
    pipeline = WordCloudPipeline(config)
    
    try:
        if args.single:
            # 处理单篇论文
            paper_info = None
            for paper in PAPERS_CONFIG:
                if paper['arxiv_id'] == args.single:
                    paper_info = paper
                    break
            
            if not paper_info:
                logger.error(f"未找到arXiv ID: {args.single}")
                return
            
            result = pipeline.process_single_paper(paper_info)
            if result and result.get('success'):
                print(f"\n✓ 成功生成词云: {result['wordcloud_path']}")
            else:
                print(f"\n✗ 处理失败")
        else:
            # 批量处理所有论文
            summary = pipeline.process_all_papers()
            
            if 'error' not in summary:
                print(f"\n{'='*60}")
                print("处理完成汇总:")
                print(f"成功: {summary['successful_papers']}/{summary['total_papers']}")
                print(f"成功率: {summary['success_rate']*100:.1f}%")
                print(f"平均质量分数: {summary['average_quality_score']}")
                print(f"处理时间: {summary['processing_time_seconds']:.1f}秒")
                print(f"生成文件数: {summary['generated_files']}")
                
                print("\n全局高频词汇:")
                for word, freq in summary['top_global_keywords'][:10]:
                    print(f"  {word}: {freq}")
                
                # 生成合并分析
                successful_results = [r for r in pipeline.stats.get('results', []) if r.get('success')]
                if successful_results:
                    pipeline.generate_combined_analysis(successful_results)
    
    except KeyboardInterrupt:
        logger.info("用户中断处理")
    except Exception as e:
        logger.error(f"处理过程中发生错误: {e}")
        raise


if __name__ == "__main__":
    main()