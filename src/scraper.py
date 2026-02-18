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
import sys
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

# Import Google Sheets (optional)
try:
    from google_sheets import GoogleSheetsManager
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ Google Sheets غیرفعال - پکیج‌های Google API نصب نشده")

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
                store_url = mihanstore_config.get('store_url', 'https://dot-shop.mihanstore.net')
                self.scrapers['mihanstore'] = MihanstoreScraper(
                    store_url=store_url,
                    config=mihanstore_config
                )
                logger.info(f"✅ Mihanstore scraper loaded for: {store_url}")
        
        # Initialize Google Sheets (if enabled)
        self.sheets_manager = None
        sheets_config = self.config.get('GOOGLE_SHEETS_CONFIG', {})
        
        if SHEETS_AVAILABLE and sheets_config.get('enabled', False):
            try:
                credentials_file = sheets_config.get('credentials_file', 'credentials.json')
                self.sheets_manager = GoogleSheetsManager(
                    credentials_file=credentials_file,
                    config=sheets_config
                )
                
                # ساخت Spreadsheet اگر وجود نداره
                if not sheets_config.get('spreadsheet_id'):
                    spreadsheet_id = self.sheets_manager.create_spreadsheet()
                    logger.info(f"✅ Spreadsheet جدید ساخته شد")
                    logger.info(f"🔗 URL: {self.sheets_manager.get_spreadsheet_url()}")
                    logger.info(f"⚠️  لطفاً ID را در config.py ذخیره کنید: {spreadsheet_id}")
                
                logger.info("✅ Google Sheets Integration فعال")
                
            except Exception as e:
                logger.error(f"❌ خطا در راه‌اندازی Google Sheets: {e}")
                logger.info("راهنما: docs/GOOGLE_SHEETS_SETUP.md")
                self.sheets_manager = None
        
        logger.info(f"✅ AffiliateProductScraper initialized with {len(self.scrapers)} platform(s)")
    
    def _load_config(self) -> Dict:
        """بارگذاری تنظیمات"""
        try:
            import config
            return {
                'MIHANSTORE_CONFIG': config.MIHANSTORE_CONFIG,
                'DIGIKALA_CONFIG': getattr(config, 'DIGIKALA_CONFIG', {'enabled': False}),
                'GOOGLE_SHEETS_CONFIG': getattr(config, 'GOOGLE_SHEETS_CONFIG', {'enabled': False}),
                'SCRAPING_CONFIG': getattr(config, 'SCRAPING_CONFIG', {}),
            }
        except ImportError:
            logger.warning("⚠️ config.py not found. Using default settings.")
            return {
                'MIHANSTORE_CONFIG': {
                    'enabled': True, 
                    'store_url': 'https://dot-shop.mihanstore.net',
                    'max_products': 30
                },
                'DIGIKALA_CONFIG': {'enabled': False},
                'GOOGLE_SHEETS_CONFIG': {'enabled': False},
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
        return self.scrapers['mihanstore'].scrape_all_products(max_products)
    
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
    
    def save_to_sheets(self, data: Dict) -> bool:
        """
        ذخیره داده‌ها در Google Sheets
        
        Args:
            data: دیکشنری محصولات
            
        Returns:
            True اگر موفق بود
        """
        if not self.sheets_manager:
            logger.warning("⚠️ Google Sheets غیرفعال - فقط در JSON ذخیره می‌شود")
            return False
        
        try:
            # تبدیل dict به list
            all_products = []
            for platform, products in data.items():
                all_products.extend(products)
            
            if not all_products:
                logger.warning("⚠️ هیچ محصولی برای آپلود وجود ندارد")
                return False
            
            # آپلود به Sheets
            stats = self.sheets_manager.upload_products(all_products, mode='update')
            
            logger.info(f"📊 Google Sheets Stats:")
            logger.info(f"   ➕ Added: {stats['added']}")
            logger.info(f"   🔄 Updated: {stats['updated']}")
            logger.info(f"   🟢 Unchanged: {stats['unchanged']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در آپلود Google Sheets: {e}")
            return False
    
    def generate_summary(self, data: Dict) -> Dict:
        """تولید خلاصه آماری"""
        summary = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'platforms': {},
            'total_products': 0,
        }
        
        for platform, products in data.items():
            if products:
                prices = [p.get('price', 0) for p in products if p.get('price', 0) > 0]
                summary['platforms'][platform] = {
                    'count': len(products),
                    'avg_price': sum(prices) / len(prices) if prices else 0,
                    'min_price': min(prices) if prices else 0,
                    'max_price': max(prices) if prices else 0,
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
    
    # ذخیره در Google Sheets (اگر فعال باشه)
    scraper.save_to_sheets(products)
    
    # نمایش خلاصه
    logger.info("\n" + "="*70)
    logger.info("📊 SUMMARY")
    logger.info("="*70)
    logger.info(f"Total Products: {summary['total_products']}")
    for platform, stats in summary['platforms'].items():
        logger.info(f"  • {platform.upper()}: {stats['count']} products")
        if stats['avg_price'] > 0:
            logger.info(f"    Average Price: {stats['avg_price']:,.0f} تومان")
            logger.info(f"    Price Range: {stats['min_price']:,.0f} - {stats['max_price']:,.0f} تومان")
    
    # نمایش لینک Google Sheets
    if scraper.sheets_manager:
        url = scraper.sheets_manager.get_spreadsheet_url()
        if url:
            logger.info(f"\n🔗 Google Sheets: {url}")
    
    logger.info("="*70)
    
    logger.info("✅ Process completed successfully!")


if __name__ == '__main__':
    main()
