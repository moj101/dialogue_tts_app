      # Dialogue TTS App / نرم‌افزار تولید صدای گفتگو

## فارسی

### معرفی
این پروژه یک نرم‌افزار دسکتاپ مبتنی بر **Python + PyQt5 + SQLite** برای مدیریت و تولید صدای دیالوگ‌های چندشخصیتی است.  
کاربر می‌تواند متن دیالوگ را وارد کند، شخصیت‌های مختلف تعریف کند، برای هر خط شخصیت مناسب را انتخاب کند، خطوط را ویرایش کند و خروجی صوتی نهایی را تولید و ادغام نماید.

این نرم‌افزار برای سناریوهایی مانند:
- تولید محتوای آموزشی
- ساخت مکالمات آموزشی زبان
- تولید صدای چندشخصیتی
- آماده‌سازی فایل‌های گفتگومحور
مناسب است.

---

### قابلیت‌ها
- ایجاد، ذخیره، بارگذاری و حذف پروژه‌ها
- تعریف و مدیریت شخصیت‌ها
- تعیین صدا، سرعت و زبان برای هر شخصیت
- دریافت متن خام دیالوگ و تجزیه آن به خطوط مستقل
- ویرایش مستقیم متن خطوط در جدول
- انتخاب دستی شخصیت برای هر خط
- بازسازی فقط خطوط تغییرکرده
- تولید صدای یک خط یا همه خطوط
- پخش فایل صوتی هر خط
- ادغام فایل‌های صوتی تولیدشده
- ذخیره خروجی نهایی
- ثبت تراکنش‌ها و هزینه‌ها
- استعلام هزینه دقیق از AvalAI با استفاده از `x-request-id`
- امکان غیرفعال‌کردن کامل مدیریت هزینه
- راهنمای داخلی خوانده‌شده از فایل متنی خارجی
- رابط کاربری فارسی و راست‌به‌چپ

---

### فناوری‌های استفاده‌شده
- Python
- PyQt5
- SQLite
- Requests
- AvalAI API

---

### ساختار کلی پروژه
نمونه‌ای از فایل‌های اصلی پروژه:

```text
dialogue_tts_app/
│
├── main.py
├── ui_main.py
├── db.py
├── avalai_api.py
├── audio_utils.py
├── config.py
├── resources.py
├── help_content.txt
├── README.md
└── data/
       
  
  

نصب و اجرا
1) نصب وابستگی‌ها
ابتدا وابستگی‌های لازم را نصب کنید:
      pip install PyQt5 requests
  در صورت نیاز بسته‌های صوتی دیگر را هم نصب کنید.
2) اجرای
      python main.py
    تنظیمات لازم
برای استفاده از سرویس AvalAI باید در بخش تنظیمات AvalAI این موارد را وارد کنید:
API Key
Base URL
مدل TTS
صدای پیش‌فرض
سرعت پیش‌فرض
زبان پیش‌فرض
فرمت پیش‌فرض
مدیریت هزینه
این نرم‌افزار امکان ثبت و پیگیری هزینه درخواست‌ها را دارد.
طبق مستندات AvalAI، شناسه تراکنش از هدر پاسخ با نام x-request-id دریافت می‌شود و برای استعلام هزینه دقیق استفاده می‌شود.
نکات:
استعلام هزینه ممکن است تا حدود 30 ثانیه پس از درخواست اصلی آماده شود.
اگر استعلام هزینه باعث کندی یا خطا شود، می‌توان آن را به‌طور کامل در تنظیمات غیرفعال کرد.
تولید صدا مستقل از استعلام هزینه کار می‌کند.
نکات مهم
بهتر است نام گوینده در متن دقیقاً با نام شخصیت تعریف‌شده یکسان باشد.
اگر بخشی از UI تغییر اندازه پیدا کند، برای جلوگیری از مخفی شدن کامل بخش‌ها محدودیت حداقل ارتفاع اعمال شده است.
برای مشاهده راهنما، فایل help_content.txt باید در کنار فایل‌های اصلی پروژه قرار داشته باشد.
این پروژه برای توسعه و شخصی‌سازی بیشتر طراحی شده است.
طراح برنامه: مجتبی محمدی
ایمیل: mojsoft@hotmai.com


MIT License
English
Introduction
This project is a desktop application built with Python + PyQt5 + SQLite for managing and generating multi-speaker dialogue audio.
Users can enter raw dialogue text, define characters, assign a speaker to each line, edit lines directly, generate speech, and merge all audio files into a final output.
It is useful for:
educational content production
language learning conversations
multi-character voice generation
dialogue-based audio preparation
Features
Create, save, load, and delete projects
Define and manage characters
Assign voice, speed, and language per character
Parse raw dialogue text into separate lines
Direct line editing inside the table
Manual character selection for each line
Rebuild only modified lines
Generate audio for one line or all lines
Play generated audio per line
Merge generated audio files
Export final output
Store transactions and costs
Lookup exact cost from AvalAI using x-request-id
Fully disable cost management if needed
Built-in help dialog loaded from external text file
Persian RTL user interface
Technologies Used
Python
PyQt5
SQLite
Requests
AvalAI API
Project Structure:
 dialogue_tts_app/
│
├── main.py
├── ui_main.py
├── db.py
├── avalai_api.py
├── audio_utils.py
├── config.py
├── resources.py
├── help_content.txt
├── README.md
└── data/
    
    
  
  

Installation and Run

1) Install dependencies
      pip install PyQt5 requests

Install any additional audio-related packages if your environment requires them.
2) Run the application
      python main.py
Required Configuration
To use the AvalAI service, open AvalAI Settings and configure:
API Key
Base URL
TTS model
Default voice
Default speed
Default language
Default output format
Cost Management
The application supports transaction and cost tracking.
According to AvalAI documentation, the transaction identifier is read from the response header named x-request-id and then used for exact cost lookup.
Notes:
Cost lookup may become available up to 30 seconds after the original request.
If cost lookup becomes slow or unstable, it can be fully disabled from settings.
Speech generation works independently from cost lookup.
Important Notes
The speaker name in the raw text should match the defined character name as closely as possible.
Minimum UI section heights are enforced to prevent panels from collapsing completely.
The file help_content.txt should exist beside the main project files for the help dialog to work properly.
This project is designed to be extensible and customizable.
Designer
Mojtaba Mohammadi
Email: mojsoft@hotmai.com
License: MIT License
   

