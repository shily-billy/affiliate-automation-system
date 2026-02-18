#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mihanstore Storefront Scraper

اسکریپت واقعی برای دریافت محصولات از فروشگاه میهن استور
بر اساس ساختار واقعی: product.php?id=XXXX
"""

import logging
import time
import re
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse, parse_qs

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("لطفاً requirements.txt را نصب کنید")

logger = logging.getLogger(__name__)


class MihanstoreScraper:
    """اسکریپر واقعی برای فروشگاه میهن استور"""
    
    def __init__(self, store_url: str = "https://dot-shop.mihanstore.net", config: Optional[Dict] = None):
        """
        Args:
            store_url: آدرس فروشگاه شما در میهن استور
            config: تنظیمات اضافی
        """
        self.store_url = store_url.rstrip('/')
        self.config = config or {}
        
        # Fallback domains اگر دسترسی مستقیم به فروشگاه نداشتیم
        self.fallback_domains = [
            "https://mihanstore.net",
            "https://www3.mihanstore.net",
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fa,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        logger.info(f"✅ MihanstoreScraper initialized for: {self.store_url}")
    
    def _clean_price(self, price_text: str) -> int:
        """
        تبدیل قیمت به عدد
        مثال: "1,698,000 تومان" -> 1698000
        
        Args:
            price_text: متن قیمت
            
        Returns:
            قیمت به صورت عدد صحیح (تومان)
        """
        if not price_text:
            return 0
        
        # حذف کاراکترهای غیرعددی (جز ممیز و نقطه)
        numbers = re.sub(r'[^0-9]', '', price_text)
        
        try:
            return int(numbers) if numbers else 0
        except ValueError:
            logger.warning(f"⚠️ خطا در تبدیل قیمت: {price_text}")
            return 0
    
    def _fetch_page(self, url: str, use_fallback: bool = True) -> Optional[BeautifulSoup]:
        """
        دریافت و parse کردن صفحه
        
        Args:
            url: آدرس صفحه
            use_fallback: استفاده از دامنه‌های جایگزین در صورت خطا
            
        Returns:
            BeautifulSoup object یا None
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            logger.warning(f"⚠️ خطا در دریافت {url}: {e}")
            
            # تلاش با fallback domains
            if use_fallback and 'product.php' in url:
                product_id = self._extract_product_id(url)
                if product_id:
                    for fallback_domain in self.fallback_domains:
                        try:
                            fallback_url = f"{fallback_domain}/product.php?id={product_id}"
                            logger.info(f"🔄 تلاش با: {fallback_url}")
                            response = self.session.get(fallback_url, timeout=30)
                            response.raise_for_status()
                            return BeautifulSoup(response.content, 'lxml')
                        except:
                            continue
            
            return None
    
    def _extract_product_id(self, url: str) -> Optional[str]:
        """استخراج ID محصول از URL"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            return params.get('id', [None])[0]
        except:
            return None
    
    def discover_product_links(self, max_products: int = 50) -> Set[str]:
        """
        کشف لینک‌های محصولات از صفحه اصلی فروشگاه
        
        Args:
            max_products: حداکثر تعداد محصول
            
        Returns:
            مجموعه لینک‌های محصولات
        """
        logger.info(f"🔍 شروع جستجوی محصولات از: {self.store_url}")
        
        product_links = set()
        
        # دریافت صفحه اصلی
        soup = self._fetch_page(self.store_url)
        if not soup:
            logger.error("❌ دسترسی به صفحه اصلی فروشگاه ممکن نیست")
            return product_links
        
        # پیدا کردن تمام لینک‌های product.php?id=
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # چک کردن اینکه product.php?id= داره
            if 'product.php' in href and 'id=' in href:
                # ساخت URL کامل
                full_url = urljoin(self.store_url, href)
                product_links.add(full_url)
                
                if len(product_links) >= max_products:
                    break
        
        logger.info(f"✅ {len(product_links)} محصول پیدا شد")
        return product_links
    
    def scrape_product(self, product_url: str) -> Optional[Dict]:
        """
        استخراج اطلاعات یک محصول
        
        Args:
            product_url: لینک محصول
            
        Returns:
            دیکشنری اطلاعات محصول
        """
        product_id = self._extract_product_id(product_url)
        if not product_id:
            logger.warning(f"⚠️ ID محصول پیدا نشد: {product_url}")
            return None
        
        logger.debug(f"🔍 در حال scraping محصول ID: {product_id}")
        
        # دریافت صفحه محصول
        soup = self._fetch_page(product_url, use_fallback=True)
        if not soup:
            logger.warning(f"⚠️ دسترسی به محصول {product_id} ممکن نیست")
            return None
        
        try:
            # استخراج نام محصول
            name = None
            # تلاش 1: از title صفحه
            if soup.title:
                name = soup.title.get_text(strip=True)
                # حذف "میهن استور" یا عبارات اضافی از آخر
                name = re.sub(r'\s*[-|]\s*(میهن استور|خرید پستی).*$', '', name, flags=re.IGNORECASE)
            
            # تلاش 2: از h1
            if not name:
                h1 = soup.find('h1')
                if h1:
                    name = h1.get_text(strip=True)
            
            # تلاش 3: از هر عنصر با class حاوی "product" و "title"
            if not name:
                title_elem = soup.find(class_=re.compile(r'product.*title|title.*product', re.I))
                if title_elem:
                    name = title_elem.get_text(strip=True)
            
            if not name:
                logger.warning(f"⚠️ نام محصول {product_id} پیدا نشد")
                return None
            
            # استخراج قیمت
            price = 0
            # جستجو برای الگوی قیمت: عدد + کاما + "تومان"
            price_pattern = r'([0-9,]+)\s*تومان'
            price_matches = soup.find_all(text=re.compile(price_pattern))
            
            if price_matches:
                # گرفتن اولین قیمت پیدا شده
                price_text = str(price_matches[0])
                price = self._clean_price(price_text)
            else:
                # تلاش با سلکتورهای معمول
                price_selectors = ['.price', '.product-price', '[class*="price"]', 'span.price']
                for selector in price_selectors:
                    price_elem = soup.select_one(selector)
                    if price_elem:
                        price = self._clean_price(price_elem.get_text())
                        if price > 0:
                            break
            
            # استخراج تصویر اصلی محصول
            image_url = None
            
            # تلاش 1: تصویر با id یا class خاص محصول
            img_elem = soup.select_one('img[class*="product"], img[id*="product"], .product-image img')
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
            
            # تلاش 2: اولین تصویر بزرگ در محتوا
            if not image_url:
                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src')
                    if src and not any(x in src.lower() for x in ['logo', 'icon', 'banner', 'button']):
                        image_url = src
                        break
            
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(self.store_url, image_url)
            
            # ساخت لینک محصول روی فروشگاه خودتون
            product_link = f"{self.store_url}/product.php?id={product_id}"
            
            product_data = {
                'product_id': product_id,
                'name': name.strip(),
                'price': price,
                'price_formatted': f"{price:,} تومان" if price > 0 else "تماس بگیرید",
                'image': image_url or '',
                'product_url': product_link,
                'platform': 'mihanstore',
                'store': self.store_url,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            logger.debug(f"✅ محصول {product_id}: {name[:50]}... - {price:,} تومان")
            return product_data
            
        except Exception as e:
            logger.error(f"❌ خطا در استخراج محصول {product_id}: {e}")
            return None
    
    def scrape_all_products(self, max_products: int = 30) -> List[Dict]:
        """
        دریافت تمام محصولات فروشگاه
        
        Args:
            max_products: حداکثر تعداد محصول
            
        Returns:
            لیست محصولات
        """
        logger.info(f"🚀 شروع scraping فروشگاه: {self.store_url}")
        
        # کشف لینک‌های محصولات
        product_links = self.discover_product_links(max_products)
        
        if not product_links:
            logger.warning("⚠️ هیچ محصولی پیدا نشد!")
            return []
        
        # Scrape کردن هر محصول
        products = []
        total = len(product_links)
        
        for idx, link in enumerate(product_links, 1):
            logger.info(f"[{idx}/{total}] در حال پردازش...")
            
            product = self.scrape_product(link)
            if product:
                products.append(product)
            
            # تاخیر بین درخواست‌ها
            if idx < total:
                time.sleep(1)
        
        logger.info(f"\n✅ تعداد کل محصولات دریافت شده: {len(products)}")
        return products


if __name__ == '__main__':
    # تست سریع
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # تست با فروشگاه dot-shop
    scraper = MihanstoreScraper(store_url="https://dot-shop.mihanstore.net")
    products = scraper.scrape_all_products(max_products=10)
    
    print(f"\n\n📦 تعداد کل: {len(products)} محصول")
    if products:
        print("\n👇 نمونه محصول اول:")
        import json
        print(json.dumps(products[0], ensure_ascii=False, indent=2))
