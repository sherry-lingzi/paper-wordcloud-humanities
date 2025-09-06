"""
HTML内容获取器
从ar5iv获取arXiv论文的HTML格式内容
"""

import requests
import time
import os
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HTMLFetcher:
    """从ar5iv获取HTML格式的arXiv论文内容"""
    
    def __init__(self, cache_dir: str = "data/cache", delay: float = 1.0):
        """
        初始化HTML获取器
        
        Args:
            cache_dir: 缓存目录路径
            delay: 请求间隔时间（秒）
        """
        self.cache_dir = cache_dir
        self.delay = delay
        self.session = requests.Session()
        
        # 设置User-Agent避免被封
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # 创建缓存目录
        os.makedirs(cache_dir, exist_ok=True)
        
    def get_ar5iv_url(self, arxiv_id: str) -> str:
        """
        构建ar5iv的HTML URL
        
        Args:
            arxiv_id: arXiv ID (例如: 2211.02002)
            
        Returns:
            ar5iv HTML页面的URL
        """
        return f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
    
    def get_cache_path(self, arxiv_id: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{arxiv_id}.html")
    
    def fetch_html_content(self, arxiv_id: str, use_cache: bool = True) -> Optional[str]:
        """
        获取指定arXiv论文的HTML内容
        
        Args:
            arxiv_id: arXiv ID
            use_cache: 是否使用缓存
            
        Returns:
            HTML内容字符串，获取失败返回None
        """
        cache_path = self.get_cache_path(arxiv_id)
        
        # 检查缓存
        if use_cache and os.path.exists(cache_path):
            logger.info(f"从缓存加载 {arxiv_id}")
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"读取缓存失败 {arxiv_id}: {e}")
        
        # 从网络获取
        url = self.get_ar5iv_url(arxiv_id)
        logger.info(f"获取 {arxiv_id} 从 {url}")
        
        try:
            # 添加延迟避免频率过高
            time.sleep(self.delay)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 检查是否成功获取到HTML内容
            if response.status_code == 200:
                html_content = response.text
                
                # 简单验证是否为有效的学术论文HTML
                if self._is_valid_paper_html(html_content):
                    # 保存到缓存
                    try:
                        with open(cache_path, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        logger.info(f"已缓存 {arxiv_id}")
                    except Exception as e:
                        logger.warning(f"保存缓存失败 {arxiv_id}: {e}")
                    
                    return html_content
                else:
                    logger.error(f"获取到的内容不是有效的论文HTML: {arxiv_id}")
                    return None
            else:
                logger.error(f"HTTP错误 {response.status_code} for {arxiv_id}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"请求超时: {arxiv_id}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败 {arxiv_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"获取HTML内容时发生未知错误 {arxiv_id}: {e}")
            return None
    
    def _is_valid_paper_html(self, html_content: str) -> bool:
        """
        验证HTML内容是否为有效的学术论文
        
        Args:
            html_content: HTML内容
            
        Returns:
            是否为有效论文HTML
        """
        # 检查一些关键标识
        indicators = [
            '<title>',
            'abstract',
            'arxiv',
            '<p>',
            '<div>',
            'author'
        ]
        
        html_lower = html_content.lower()
        return any(indicator in html_lower for indicator in indicators) and len(html_content) > 1000
    
    def batch_fetch(self, arxiv_ids: List[str], use_cache: bool = True) -> Dict[str, Optional[str]]:
        """
        批量获取多篇论文的HTML内容
        
        Args:
            arxiv_ids: arXiv ID列表
            use_cache: 是否使用缓存
            
        Returns:
            字典，键为arXiv ID，值为HTML内容（失败时为None）
        """
        results = {}
        total = len(arxiv_ids)
        
        logger.info(f"开始批量获取 {total} 篇论文的HTML内容")
        
        for i, arxiv_id in enumerate(arxiv_ids, 1):
            logger.info(f"处理进度: {i}/{total} - {arxiv_id}")
            html_content = self.fetch_html_content(arxiv_id, use_cache)
            results[arxiv_id] = html_content
            
            if html_content:
                logger.info(f"成功获取 {arxiv_id} ({len(html_content)} 字符)")
            else:
                logger.error(f"获取失败 {arxiv_id}")
        
        successful = sum(1 for content in results.values() if content is not None)
        logger.info(f"批量获取完成: {successful}/{total} 成功")
        
        return results
    
    def get_paper_info(self, arxiv_id: str) -> Dict[str, str]:
        """
        从HTML中提取论文基本信息
        
        Args:
            arxiv_id: arXiv ID
            
        Returns:
            包含论文基本信息的字典
        """
        html_content = self.fetch_html_content(arxiv_id)
        if not html_content:
            return {}
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html5lib')
        
        info = {}
        
        # 提取标题
        title_tag = soup.find('title')
        if title_tag:
            info['title'] = title_tag.get_text().strip()
        
        # 提取摘要
        abstract_tag = soup.find('div', class_='ltx_abstract') or soup.find('section', class_='ltx_abstract')
        if abstract_tag:
            info['abstract'] = abstract_tag.get_text().strip()
        
        # 提取作者信息
        authors_tags = soup.find_all('span', class_='ltx_creator')
        if authors_tags:
            authors = [tag.get_text().strip() for tag in authors_tags]
            info['authors'] = ', '.join(authors)
        
        return info
    
    def clear_cache(self):
        """清空缓存目录"""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
            logger.info("缓存已清空")
    
    def get_cache_info(self) -> Dict[str, int]:
        """获取缓存信息"""
        if not os.path.exists(self.cache_dir):
            return {"cached_papers": 0, "total_size": 0}
        
        cached_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.html')]
        total_size = sum(os.path.getsize(os.path.join(self.cache_dir, f)) for f in cached_files)
        
        return {
            "cached_papers": len(cached_files),
            "total_size": total_size
        }


# 测试函数
def test_html_fetcher():
    """测试HTMLFetcher功能"""
    fetcher = HTMLFetcher()
    
    # 测试单个论文获取
    test_arxiv_id = "2211.02002"
    html_content = fetcher.fetch_html_content(test_arxiv_id)
    
    if html_content:
        print(f"✓ 成功获取 {test_arxiv_id}")
        print(f"HTML长度: {len(html_content)} 字符")
        
        # 测试信息提取
        info = fetcher.get_paper_info(test_arxiv_id)
        print(f"论文信息: {info}")
    else:
        print(f"✗ 获取失败 {test_arxiv_id}")
    
    # 显示缓存信息
    cache_info = fetcher.get_cache_info()
    print(f"缓存信息: {cache_info}")


if __name__ == "__main__":
    test_html_fetcher()