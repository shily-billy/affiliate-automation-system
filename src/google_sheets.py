#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheets Integration Module

ماژول اتصال به Google Sheets برای ذخیره و مدیریت محصولات
"""

import logging
import os
from typing import List, Dict, Optional
from datetime import datetime

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ لطفاً پکیج‌های Google API را نصب کنید:")
    print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    raise

logger = logging.getLogger(__name__)


class GoogleSheetsManager:
    """مدیریت Google Sheets برای ذخیره محصولات"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    # ستون‌های جدول محصولات
    HEADERS = [
        'Product ID',
        'Platform',
        'Name',
        'Price (Toman)',
        'Price Formatted',
        'Image URL',
        'Product URL',
        'Category',
        'Status',
        'Last Updated',
        'Scraped At'
    ]
    
    def __init__(self, credentials_file: str, config: Optional[Dict] = None):
        """
        Args:
            credentials_file: مسیر فایل credentials.json
            config: تنظیمات اضافی
        """
        self.credentials_file = credentials_file
        self.config = config or {}
        self.service = None
        self.spreadsheet_id = self.config.get('spreadsheet_id')
        self.sheet_name = self.config.get('sheet_name', 'Products')
        
        # اتصال به Google Sheets
        self._authenticate()
        
        logger.info("✅ GoogleSheetsManager initialized")
    
    def _authenticate(self):
        """احراز هویت و ایجاد سرویس"""
        try:
            if not os.path.exists(self.credentials_file):
                logger.error(f"❌ فایل credentials پیدا نشد: {self.credentials_file}")
                logger.error("راهنمای ساخت credentials: docs/GOOGLE_SHEETS_SETUP.md")
                raise FileNotFoundError(f"credentials file not found: {self.credentials_file}")
            
            creds = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=self.SCOPES
            )
            
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("✅ اتصال به Google Sheets برقرار شد")
            
        except Exception as e:
            logger.error(f"❌ خطا در احراز هویت: {e}")
            raise
    
    def create_spreadsheet(self, title: str = "Affiliate Products") -> str:
        """
        ساخت Spreadsheet جدید
        
        Args:
            title: عنوان Spreadsheet
            
        Returns:
            ID سپردشیت ساخته شده
        """
        logger.info(f"📝 ساخت Spreadsheet جدید: {title}")
        
        try:
            spreadsheet = {
                'properties': {
                    'title': title,
                    'locale': 'fa_IR',
                    'timeZone': 'Asia/Tehran'
                },
                'sheets': [
                    {
                        'properties': {
                            'title': self.sheet_name,
                            'gridProperties': {
                                'frozenRowCount': 1  # ثابت نگه داشتن ردیف اول
                            }
                        }
                    }
                ]
            }
            
            result = self.service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId,spreadsheetUrl'
            ).execute()
            
            self.spreadsheet_id = result['spreadsheetId']
            spreadsheet_url = result['spreadsheetUrl']
            
            logger.info(f"✅ Spreadsheet ساخته شد: {spreadsheet_url}")
            logger.info(f"   ID: {self.spreadsheet_id}")
            
            # اضافه کردن هدرها
            self._write_headers()
            
            # فرمت کردن هدرها
            self._format_headers()
            
            return self.spreadsheet_id
            
        except HttpError as e:
            logger.error(f"❌ خطا در ساخت Spreadsheet: {e}")
            raise
    
    def _write_headers(self):
        """نوشتن هدرها در ردیف اول"""
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1",
                valueInputOption='RAW',
                body={'values': [self.HEADERS]}
            ).execute()
            
            logger.info("✅ هدرها اضافه شدند")
            
        except HttpError as e:
            logger.error(f"❌ خطا در نوشتن هدرها: {e}")
    
    def _format_headers(self):
        """فرمت کردن ردیف هدر (بولد، پس‌زمینه)"""
        try:
            requests = [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8},
                                'textFormat': {
                                    'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                                    'fontSize': 11,
                                    'bold': True
                                },
                                'horizontalAlignment': 'CENTER'
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                    }
                },
                {
                    'autoResizeDimensions': {
                        'dimensions': {
                            'sheetId': 0,
                            'dimension': 'COLUMNS',
                            'startIndex': 0,
                            'endIndex': len(self.HEADERS)
                        }
                    }
                }
            ]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
            logger.debug("✅ فرمت هدرها اعمال شد")
            
        except HttpError as e:
            logger.warning(f"⚠️ خطا در فرمت هدرها: {e}")
    
    def get_existing_products(self) -> Dict[str, List]:
        """
        دریافت محصولات موجود در Sheet
        
        Returns:
            دیکشنری با کلید product_id:
            {'product_id': [row_number, current_data]}
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A2:K"
            ).execute()
            
            values = result.get('values', [])
            
            # ساخت دیکشنری برای دسترسی سریع
            existing = {}
            for idx, row in enumerate(values, start=2):
                if len(row) > 0:
                    product_id = f"{row[1]}_{row[0]}" if len(row) > 1 else row[0]  # platform_productid
                    existing[product_id] = [idx, row]
            
            logger.info(f"✅ تعداد محصولات موجود: {len(existing)}")
            return existing
            
        except HttpError as e:
            logger.warning(f"⚠️ خطا در دریافت محصولات: {e}")
            return {}
    
    def upload_products(self, products: List[Dict], mode: str = 'update') -> Dict:
        """
        آپلود محصولات به Google Sheets
        
        Args:
            products: لیست محصولات
            mode: نوع آپلود
                - 'update': آپدیت محصولات موجود و اضافه جدیدها
                - 'replace': حذف همه و اضافه مجدد
                - 'append': فقط اضافه جدیدها
                
        Returns:
            دیکشنری آمار: {added, updated, unchanged}
        """
        if not self.spreadsheet_id:
            logger.error("❌ Spreadsheet ID تنظیم نشده. ابتدا create_spreadsheet را فراخوانی کنید.")
            return {'added': 0, 'updated': 0, 'unchanged': 0}
        
        logger.info(f"📤 شروع آپلود {len(products)} محصول (mode: {mode})")
        
        stats = {'added': 0, 'updated': 0, 'unchanged': 0}
        
        if mode == 'replace':
            # حذف همه داده‌ها
            self._clear_data()
            mode = 'append'
        
        # دریافت محصولات موجود
        existing = self.get_existing_products() if mode == 'update' else {}
        
        # آماده‌سازی داده‌ها برای آپلود
        rows_to_add = []
        rows_to_update = []
        
        for product in products:
            row = self._product_to_row(product)
            product_key = f"{product.get('platform', '')}_{product.get('product_id', '')}"
            
            if product_key in existing:
                # آپدیت محصول موجود
                row_number = existing[product_key][0]
                old_row = existing[product_key][1]
                
                # چک تغییرات (فقط قیمت)
                if len(old_row) > 3 and old_row[3] != row[3]:  # Price changed
                    rows_to_update.append({'range': f"{self.sheet_name}!A{row_number}", 'values': [row]})
                    stats['updated'] += 1
                else:
                    stats['unchanged'] += 1
            else:
                # محصول جدید
                rows_to_add.append(row)
                stats['added'] += 1
        
        # آپلود بچ محصولات جدید
        if rows_to_add:
            self._batch_append(rows_to_add)
        
        # آپدیت بچ محصولات موجود
        if rows_to_update:
            self._batch_update(rows_to_update)
        
        logger.info(f"✅ آپلود تمام شد: +{stats['added']} | ~{stats['updated']} | ={stats['unchanged']}")
        
        return stats
    
    def _product_to_row(self, product: Dict) -> List:
        """تبدیل دیکشنری محصول به ردیف Sheet"""
        return [
            product.get('product_id', ''),
            product.get('platform', ''),
            product.get('name', ''),
            product.get('price', 0),
            product.get('price_formatted', ''),
            product.get('image', ''),
            product.get('product_url', ''),
            product.get('category', ''),
            product.get('status', 'Active'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            product.get('scraped_at', '')
        ]
    
    def _batch_append(self, rows: List[List]):
        """اضافه بچ ردیف‌ها"""
        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A2",
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': rows}
            ).execute()
            
            logger.info(f"✅ {len(rows)} محصول جدید اضافه شد")
            
        except HttpError as e:
            logger.error(f"❌ خطا در اضافه ردیف‌ها: {e}")
    
    def _batch_update(self, data: List[Dict]):
        """آپدیت بچ ردیف‌ها"""
        try:
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'valueInputOption': 'RAW', 'data': data}
            ).execute()
            
            logger.info(f"✅ {len(data)} محصول آپدیت شد")
            
        except HttpError as e:
            logger.error(f"❌ خطا در آپدیت ردیف‌ها: {e}")
    
    def _clear_data(self):
        """حذف تمام داده‌ها (بجز هدرها)"""
        try:
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A2:K"
            ).execute()
            
            logger.info("✅ داده‌ها پاک شدند")
            
        except HttpError as e:
            logger.error(f"❌ خطا در پاک کردن داده‌ها: {e}")
    
    def get_spreadsheet_url(self) -> Optional[str]:
        """دریافت URL سپردشیت"""
        if self.spreadsheet_id:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"
        return None


if __name__ == '__main__':
    # تست سریع
    logging.basicConfig(level=logging.INFO)
    
    print("⚠️  برای تست این ماژول:")
    print("1. credentials.json را از Google Cloud دریافت کنید")
    print("2. راهنما: docs/GOOGLE_SHEETS_SETUP.md")
    print("3. python src/scraper.py --use-sheets")
