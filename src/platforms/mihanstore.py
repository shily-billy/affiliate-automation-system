#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mihanstore Scraper Module

ماژول دریافت محصولات از میهن استور
"""

import logging
import time
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("لطفاً requirements.txt را نصب کنید")

logger = logging.getLogger(__name__)


class MihanstoreScraper:
    """کلاس scraper برای میهن استور"""
    
    BASE_URL = "https://mihanstore.net"
    AFFILIATE_URL = "https://affiliate-marketing.mihanstore.net"
    
    def __init__(self, affiliate_id: str = None, config: Optional[Dict] = None):
        """
        Args:
            affiliate_id: شناسه افیلیت شما
            config: تنظیمات اضافی
        """
        self.affiliate_id = affiliate_id or "dotshop"
        self.config = config or {}
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fa,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        logger.info(f"✅ MihanstoreScraper initialized with affiliate_id: {self.affiliate_id}")
    
    def _clean_price(self, price_text: str) -> int:
        """
        پاکسازی و تبدیل قیمت به عدد
        
        Args:
            price_text: متن قیمت (مثل: "248,000 تومان")
            
        Returns:
            قیمت به صورت عدد صحیح (تومان)
        """
        if not price_text:
            return 0
        
        # حذف کاراکترهای غیرعددی
        numbers = re.sub(r'[^0-9]', '', price_text)
        
        try:
            return int(numbers) if numbers else 0
        except ValueError:
            logger.warning(f"⚠️ خطا در تبدیل قیمت: {price_text}")
            return 0
    
    def _build_affiliate_link(self, product_url: str) -> str:
        """
        ساخت لینک افیلیت
        
        Args:
            product_url: لینک اصلی محصول
            
        Returns:
            لینک افیلیت کامل
        """
        if '?' in product_url:
            return f"{product_url}&ref={self.affiliate_id}"
        else:
            return f"{product_url}?ref={self.affiliate_id}"
    
    def scrape_category(self, category_url: str, max_products: int = 50) -> List[Dict]:
        """
        دریافت محصولات از یک دسته‌بندی
        
        Args:
            category_url: لینک دسته‌بندی
            max_products: حداکثر تعداد محصول
            
        Returns:
            لیست محصولات
        """
        logger.info(f"🔍 Scraping category: {category_url}")
        products = []
        
        try:
            # درخواست به صفحه دسته‌بندی
            response = self.session.get(category_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # پیدا کردن عناصر محصول
            # میهن استور معمولاً از ساختار product-card استفاده می‌کند
            product_cards = soup.select('.product-card, .product-item, .product, article.product')
            
            if not product_cards:
                logger.warning("⚠️ محصولی پیدا نشد. ساختار HTML تغییر کرده.")
                # تلاش با ساختار دیگر
                product_cards = soup.find_all('div', class_=re.compile(r'product', re.I))
            
            logger.info(f"✅ Found {len(product_cards)} products")
            
            for idx, card in enumerate(product_cards[:max_products], 1):
                try:
                    product = self._extract_product_info(card)
                    if product:
                        products.append(product)
                        logger.info(f"  [{idx}/{min(max_products, len(product_cards))}] {product['name'][:50]}...")
                    
                    # تاخیر بین درخواست‌ها
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"❌ خطا در استخراج محصول {idx}: {e}")
                    continue
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطای شبکه: {e}")
        except Exception as e:
            logger.error(f"❌ خطای ناشناخته: {e}")
        
        logger.info(f"✅ Scraped {len(products)} products from category")
        return products
    
    def _extract_product_info(self, card) -> Optional[Dict]:
        """
        استخراج اطلاعات محصول از کارت
        
        Args:
            card: عنصر BeautifulSoup کارت محصول
            
        Returns:
            دیکشنری اطلاعات محصول
        """
        try:
            # نام محصول
            name_elem = card.select_one('h3, h2, .product-title, .title, a[title]')
            name = name_elem.get_text(strip=True) if name_elem else None
            if not name and name_elem:
                name = name_elem.get('title', '').strip()
            
            if not name:
                return None
            
            # لینک محصول
            link_elem = card.select_one('a[href]')
            link = link_elem.get('href', '') if link_elem else ''
            
            if link and not link.startswith('http'):
                link = urljoin(self.BASE_URL, link)
            
            # قیمت
            price_elem = card.select_one('.price, .product-price, .price-current, span[class*="price"]')
            price_text = price_elem.get_text(strip=True) if price_elem else '0'
            price = self._clean_price(price_text)
            
            # تصویر
            img_elem = card.select_one('img')
            image = ''
            if img_elem:
                image = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src') or ''
                if image and not image.startswith('http'):
                    image = urljoin(self.BASE_URL, image)
            
            # ساخت لینک افیلیت
            affiliate_link = self._build_affiliate_link(link) if link else ''
            
            # دسته‌بندی (اگر موجود باشد)
            category_elem = card.select_one('.category, .product-category')
            category = category_elem.get_text(strip=True) if category_elem else 'Fashion'
            
            product_data = {
                'name': name,
                'price': price,
                'price_formatted': f"{price:,} تومان",
                'image': image,
                'link': link,
                'affiliate_link': affiliate_link,
                'category': category,
                'platform': 'mihanstore',
                'commission_rate': 10,  # نرخ کمیسیون پیش‌فرض 10%
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            return product_data
            
        except Exception as e:
            logger.error(f"❌ خطا در استخراج اطلاعات: {e}")
            return None
    
    def scrape_popular_products(self, max_products: int = 30) -> List[Dict]:
        """
        دریافت محصولات محبوب/پرفروش
        
        Args:
            max_products: حداکثر تعداد محصول
            
        Returns:
            لیست محصولات
        """
        logger.info("🔥 Scraping popular products...")
        return self.scrape_category(self.BASE_URL, max_products)
    
    def scrape_by_categories(self, categories: List[str], max_per_category: int = 20) -> Dict[str, List[Dict]]:
        """
        دریافت محصولات بر اساس دسته‌بندی‌ها
        
        Args:
            categories: لیست لینک دسته‌بندی‌ها
            max_per_category: حداکثر تعداد محصول هر دسته
            
        Returns:
            دیکشنری شامل محصولات هر دسته
        """
        results = {}
        
        for category_url in categories:
            try:
                category_name = category_url.split('/')[-1] or 'main'
                logger.info(f"\n📂 Processing category: {category_name}")
                
                products = self.scrape_category(category_url, max_per_category)
                results[category_name] = products
                
                # تاخیر بین دسته‌بندی‌ها
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ خطا در پردازش دسته {category_url}: {e}")
                results[category_url] = []
        
        total = sum(len(prods) for prods in results.values())
        logger.info(f"\n✅ Total products scraped: {total}")
        
        return results


if __name__ == '__main__':
    # تست سریع
    logging.basicConfig(level=logging.INFO)
    
    scraper = MihanstoreScraper(affiliate_id='dotshop')
    products = scraper.scrape_popular_products(max_products=10)
    
    print(f"\n\n📦 Total: {len(products)} products")
    if products:
        print("\n👇 Sample product:")
        import json
        print(json.dumps(products[0], ensure_ascii=False, indent=2))
