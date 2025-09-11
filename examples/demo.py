#!/usr/bin/env python3
"""
Demo script for Paper WordCloud Generator
This shows how to use the library programmatically
"""

import sys
import os

# Add parent directory to path to import arxiv_wordcloud
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from arxiv_wordcloud import create_wordcloud_from_arxiv

def demo():
    """Run a simple demo"""
    print("🚀 Paper WordCloud Demo")
    
    # Demo with a few physics papers
    arxiv_ids = [
        "2211.02002",  # Quantum spin liquid
        "2302.10115",  # Non-Hermitian Dirac fermions
        "2409.18050",  # Superconductivity
    ]
    
    # Use example files
    mask_path = "mask.jpg"
    output_path = "demo_wordcloud.png"
    font_path = "../fonts/HardingTextRegular.ttf" if os.path.exists("../fonts/HardingTextRegular.ttf") else None
    
    print(f"📝 Processing {len(arxiv_ids)} papers...")
    print(f"🎭 Using mask: {mask_path}")
    print(f"🔤 Using font: {font_path or 'default'}")
    print(f"📸 Output: {output_path}")
    
    success = create_wordcloud_from_arxiv(
        arxiv_ids=arxiv_ids,
        mask_image=mask_path, 
        output_file=output_path,
        font_path=font_path
    )
    
    if success:
        print("✅ Demo completed successfully!")
        print(f"   Check your wordcloud: {output_path}")
    else:
        print("❌ Demo failed!")

if __name__ == "__main__":
    demo()