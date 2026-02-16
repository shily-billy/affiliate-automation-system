#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affiliate Product Scraper

اسکریپت اصلی برای دریافت اطلاعات محصولات از پلتفرم‌های افیلیت
"""

import logging
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ لطفاً ابتدا وابستگی‌ها را نصب کنید: pip install -r requirements.txt")
    exit(1)

# Import platform scrapers
try:
    from platforms.mihanstore import MihanstoreScraper
except ImportError:
    print("⚠️ ماژول platforms پیدا نشد. مطمئن شوید در مسیر صحیح هستید.")
    MihanstoreScraper = None

# Setup Logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AffiliateProductScraper:
    """کلاس اصلی برای دریافت محصولات"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: دیکشنری تنظیمات
        """
        self.config = config or self._load_config()
        
        # Initialize platform scrapers
        self.scrapers = {}
        
        if MihanstoreScraper:
            mihanstore_config = self.config.get('MIHANSTORE_CONFIG', {})
            if mihanstore_config.get('enabled', True):
                self.scrapers['mihanstore'] = MihanstoreScraper(
                    affiliate_id=mihanstore_config.get('affiliate_id', 'dotshop'),
                    config=mihanstore_config
                )
                logger.info("✅ Mihanstore scraper loaded")
        
        logger.info(f"✅ AffiliateProductScraper initialized with {len(self.scrapers)} platform(s)")
    
    def _load_config(self) -> Dict:
        """بارگذاری تنظیمات"""
        try:
            import config
            return {
                'MIHANSTORE_CONFIG': config.MIHANSTORE_CONFIG,
                'DIGIKALA_CONFIG': config.DIGIKALA_CONFIG,
                'SCRAPING_CONFIG': config.SCRAPING_CONFIG,
            }
        except ImportError:
            logger.warning("⚠️ config.py not found. Using default settings.")
            return {
                'MIHANSTORE_CONFIG': {'enabled': True, 'affiliate_id': 'dotshop'},
                'DIGIKALA_CONFIG': {'enabled': False},
                'SCRAPING_CONFIG': {},
            }
    
    def scrape_mihanstore(self, max_products: int = 30) -> List[Dict]:
        """
        دریافت محصولات از میهن استور
        
        Args:
            max_products: حداکثر تعداد محصول
            
        Returns:
            لیست محصولات
        """
        if 'mihanstore' not in self.scrapers:
            logger.error("❌ Mihanstore scraper not available")
            return []
        
        logger.info("🔍 Starting Mihanstore scraping...")
        return self.scrapers['mihanstore'].scrape_popular_products(max_products)
    
    def scrape_all_platforms(self) -> Dict[str, List[Dict]]:
        """
        دریافت محصولات از تمام پلتفرم‌های فعال
        
        Returns:
            دیکشنری شامل محصولات هر پلتفرم
        """
        logger.info("🚀 Starting scraping from all platforms...")
        results = {}
        
        # Mihanstore
        if 'mihanstore' in self.scrapers:
            try:
                config = self.config.get('MIHANSTORE_CONFIG', {})
                max_products = config.get('max_products', 30)
                results['mihanstore'] = self.scrape_mihanstore(max_products)
            except Exception as e:
                logger.error(f"❌ Mihanstore error: {e}")
                results['mihanstore'] = []
        
        # TODO: Add other platforms (Digikala, etc.)
        
        total = sum(len(v) for v in results.values())
        logger.info(f"✅ Scraping completed. Total products: {total}")
        
        return results
    
    def save_to_json(self, data: Dict, filepath: str = 'data/products.json'):
        """ذخیره داده‌ها در فایل JSON"""
        # Create data directory if not exists
        Path(filepath).parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Data saved to {filepath}")
    
    def generate_summary(self, data: Dict) -> Dict:
        """تولید خلاصه آماری"""
        summary = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'platforms': {},
            'total_products': 0,
        }
        
        for platform, products in data.items():
            if products:
                summary['platforms'][platform] = {
                    'count': len(products),
                    'avg_price': sum(p.get('price', 0) for p in products) / len(products),
                    'categories': list(set(p.get('category', 'N/A') for p in products)),
                }
                summary['total_products'] += len(products)
        
        return summary


def main():
    """تابع اصلی"""
    logger.info("="*70)
    logger.info("🚀 Affiliate Automation System - Phase 1: Data Collection")
    logger.info("="*70)
    
    # ایجاد instance از scraper
    scraper = AffiliateProductScraper()
    
    # دریافت محصولات
    products = scraper.scrape_all_platforms()
    
    # تولید خلاصه
    summary = scraper.generate_summary(products)
    
    # ذخیره در JSON
    scraper.save_to_json(products, 'data/products.json')
    scraper.save_to_json(summary, 'data/summary.json')
    
    # نمایش خلاصه
    logger.info("\n" + "="*70)
    logger.info("📊 SUMMARY")
    logger.info("="*70)
    logger.info(f"Total Products: {summary['total_products']}")
    for platform, stats in summary['platforms'].items():
        logger.info(f"  • {platform.upper()}: {stats['count']} products")
        logger.info(f"    Average Price: {stats['avg_price']:,.0f} تومان")
    logger.info("="*70)
    
    logger.info("✅ Process completed successfully!")


if __name__ == '__main__':
    main()
