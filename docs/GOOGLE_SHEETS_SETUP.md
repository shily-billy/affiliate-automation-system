# 📗 راهنمای نصب Google Sheets API

راهنمای گام‌به‌گام برای اتصال پروژه به Google Sheets

---

## 📋 مراحل کلی:

1. ساخت پروژه در Google Cloud
2. فعال کردن Google Sheets API
3. ساخت Service Account
4. دانلود فایل Credentials
5. تنظیمات پروژه
6. تست اتصال

---

## 🔧 مرحله 1: ساخت پروژه در Google Cloud

### 1.1 ورود به Google Cloud Console:
```
https://console.cloud.google.com/
```

### 1.2 ساخت پروژه جدید:
1. کلیک روی **"Select a project"** (بالای صفحه)
2. کلیک روی **"NEW PROJECT"**
3. نام پروژه: `Affiliate Automation`
4. کلیک روی **"CREATE"**
5. منتظر بمانید تا پروژه ساخته شود (10-20 ثانیه)

---

## 🔌 مرحله 2: فعال کردن Google Sheets API

### 2.1 رفتن به API Library:
1. از منوی سمت چپ: **"APIs & Services"** > **"Library"**
2. یا مستقیم: https://console.cloud.google.com/apis/library

### 2.2 فعال کردن Sheets API:
1. در جستجو تایپ کنید: `Google Sheets API`
2. کلیک روی **"Google Sheets API"**
3. کلیک روی **"ENABLE"**

### 2.3 فعال کردن Drive API (اختیاری ولی توصیه می‌شه):
1. برگردید به Library
2. جستجو: `Google Drive API`
3. کلیک و **"ENABLE"**

---

## 👤 مرحله 3: ساخت Service Account

### 3.1 رفتن به Credentials:
1. از منوی سمت چپ: **"APIs & Services"** > **"Credentials"**
2. یا مستقیم: https://console.cloud.google.com/apis/credentials

### 3.2 ساخت Service Account:
1. کلیک روی **"+ CREATE CREDENTIALS"** (بالای صفحه)
2. انتخاب **"Service account"**

### 3.3 جزئیات Service Account:
**Step 1: Service account details**
- Service account name: `affiliate-bot`
- Service account ID: (خودکار پر می‌شه)
- Description: `Bot for affiliate automation system`
- کلیک **"CREATE AND CONTINUE"**

**Step 2: Grant this service account access to project**
- Role: **"Editor"** (یا می‌تونید Basic > Editor رو انتخاب کنید)
- کلیک **"CONTINUE"**

**Step 3: Grant users access to this service account**
- این بخش رو خالی بذارید
- کلیک **"DONE"**

---

## 🔑 مرحله 4: دانلود Credentials File

### 4.1 یافتن Service Account:
1. در صفحه **Credentials**، پایین صفحه قسمت **"Service Accounts"** رو پیدا کنید
2. روی ایمیل Service Account کلیک کنید (مثل: `affiliate-bot@...`)

### 4.2 ساخت Key:
1. رفتن به تب **"KEYS"**
2. کلیک **"ADD KEY"** > **"Create new key"**
3. انتخاب **"JSON"**
4. کلیک **"CREATE"**

### 4.3 ذخیره فایل:
- فایل `credentials.json` خودکار دانلود می‌شه
- **مهم:** این فایل رو به کسی ندید! (مثل رمز عبور است)

---

## 📁 مرحله 5: تنظیمات پروژه

### 5.1 انتقال فایل Credentials:
```bash
# انتقال فایل دانلود شده به پوشه پروژه
mv ~/Downloads/credentials.json ~/projects/affiliate-automation-system/credentials.json

# چک کردن
cd ~/projects/affiliate-automation-system
ls -la credentials.json
```

### 5.2 ویرایش Config:
```bash
nano config.py
```

مقادیر زیر رو تنظیم کنید:
```python
GOOGLE_SHEETS_CONFIG = {
    'enabled': True,
    'credentials_file': 'credentials.json',
    'spreadsheet_id': '',  # خالی بذارید - خودکار ساخته می‌شه
    'sheet_name': 'Products',
}
```

---

## 🧪 مرحله 6: تست اتصال

### 6.1 اجرای تست:
```bash
cd ~/projects/affiliate-automation-system
python3 src/scraper.py
```

### 6.2 خروجی موفق:
```
✅ GoogleSheetsManager initialized
✅ اتصال به Google Sheets برقرار شد
📝 ساخت Spreadsheet جدید: Affiliate Products
✅ Spreadsheet ساخته شد: https://docs.google.com/spreadsheets/d/...
   ID: 1a2b3c4d5e...
✅ هدرها اضافه شدند
📤 شروع آپلود 25 محصول (mode: update)
✅ 25 محصول جدید اضافه شد
✅ آپلود تمام شد: +25 | ~0 | =0
```

### 6.3 بررسی Spreadsheet:
1. لینک Spreadsheet رو از خروجی کپی کنید
2. توی مرورگر باز کنید
3. باید محصولات رو ببینید!

---

## ⚙️ تنظیمات پیشرفته (اختیاری)

### استفاده از Spreadsheet موجود:

اگه می‌خواید به جای ساخت Spreadsheet جدید، از یکی موجود استفاده کنید:

1. Spreadsheet رو در Google Sheets باز کنید
2. از URL، قسمت ID رو کپی کنید:
   ```
   https://docs.google.com/spreadsheets/d/[این_بخش_ID_است]/edit
   ```

3. در `config.py` تنظیم کنید:
   ```python
   GOOGLE_SHEETS_CONFIG = {
       'spreadsheet_id': 'ID_که_کپی_کردید',
       ...
   }
   ```

4. **مهم:** باید Service Account رو به Spreadsheet دسترسی بدید:
   - روی **"Share"** کلیک کنید
   - ایمیل Service Account رو اضافه کنید (مثل: `affiliate-bot@...`)
   - سطح دسترسی: **"Editor"**
   - کلیک **"Send"**

---

## 🐛 عیب‌یابی

### خطا: "credentials.json not found"
```bash
# چک کنید فایل وجود داره
ls -la credentials.json

# اگه نیست، دوباره از Google Cloud دانلود کنید
```

### خطا: "Permission denied"
- مطمئن شوید Service Account به Spreadsheet دسترسی داره
- در صفحه Spreadsheet روی Share کلیک کنید و ایمیل Service Account رو اضافه کنید

### خطا: "API not enabled"
```
1. برید به: https://console.cloud.google.com/apis/library
2. Google Sheets API رو فعال کنید
3. Google Drive API رو هم فعال کنید
```

### خطا: "Invalid credentials"
- فایل credentials.json معتبر نیست
- دوباره از Google Cloud دانلود کنید
- مطمئن شوید فایل JSON سالم است (با `cat credentials.json`)

---

## 📚 منابع بیشتر:

- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Python Quickstart](https://developers.google.com/sheets/api/quickstart/python)

---

## ✅ Checklist نهایی:

- [ ] پروژه در Google Cloud ساخته شد
- [ ] Google Sheets API فعال شد
- [ ] Service Account ساخته شد
- [ ] فایل credentials.json دانلود و در پوشه پروژه قرار گرفت
- [ ] config.py تنظیم شد
- [ ] تست موفق بود
- [ ] محصولات در Spreadsheet نمایش داده می‌شوند

---

🎉 تبریک! Google Sheets Integration آماده است!
