"""Configuration file template

تمام تنظیمات پروژه در این فایل قرار دارد.
برای استفاده:
1. این فایل را کپی کنید: cp config.example.py config.py
2. مقادیر واقعی را جایگزین کنید
3. config.py در .gitignore است و commit نمی‌شود
"""

# ==================== GOOGLE SHEETS ====================
GOOGLE_SHEETS_CONFIG = {
    'credentials_file': 'credentials.json',  # فایل credentials از Google Cloud
    'spreadsheet_id': 'YOUR_SPREADSHEET_ID_HERE',  # ID گوگل شیت
    'sheet_name': 'Products',  # نام sheet
}

# ==================== SCRAPING SETTINGS ====================
SCRAPING_CONFIG = {
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'delay_between_requests': 2,  # تاخیر بین درخواست‌ها (ثانیه)
    'max_retries': 3,  # تعداد تلاش مجدد
    'timeout': 30,  # timeout درخواست (ثانیه)
}

# ==================== AFFILIATE PLATFORMS ====================

# میهن استور
MIHANSTORE_CONFIG = {
    'enabled': True,
    'store_url': 'https://dot-shop.mihanstore.net',  # آدرس فروشگاه شما
    'max_products': 30,  # تعداد محصول
}

# دیجی‌کالا
DIGIKALA_CONFIG = {
    'enabled': False,
    'affiliate_id': 'YOUR_AFFILIATE_ID',
    'categories': [
        'mobile',
        'laptop',
        'headphone',
    ],
    'max_products': 50,  # تعداد محصول هر دسته
}

# خانومی
KHANOMI_CONFIG = {
    'enabled': False,
    'affiliate_id': 'YOUR_AFFILIATE_ID',
    'categories': [],
}

# تکنولایف
TECHNOLIFE_CONFIG = {
    'enabled': False,
    'affiliate_id': 'YOUR_AFFILIATE_ID',
    'categories': [],
}

# ==================== SCHEDULER ====================
SCHEDULER_CONFIG = {
    'enabled': True,
    'run_time': '06:00',  # زمان اجرای روزانه (24-hour format)
    'timezone': 'Asia/Tehran',
}

# ==================== LOGGING ====================
LOGGING_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'log_file': 'logs/scraper.log',
    'max_file_size': 10 * 1024 * 1024,  # 10 MB
    'backup_count': 5,
}

# ==================== NOTIFICATIONS ====================
NOTIFICATIONS_CONFIG = {
    'telegram': {
        'enabled': False,
        'bot_token': 'YOUR_BOT_TOKEN',
        'chat_id': 'YOUR_CHAT_ID',
    },
    'email': {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'your-email@gmail.com',
        'password': 'your-app-password',
        'recipient': 'recipient@example.com',
    },
}
