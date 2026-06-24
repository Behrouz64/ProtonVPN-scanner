[app]

# (str) عنوان برنامه شما که روی گوشی نصب می‌شود
title = Proton Scanner

# (str) نام پکیج برنامه (فقط حروف کوچک انگلیسی و بدون فاصله)
package.name = protonscanner

# (str) دامنه برنامه (برای ساخت شناسه یکتا مثل org.behrouz.protonscanner)
package.domain = org.behrouz

# (str) مسیر فایل‌های سورس (نقطه یعنی همین پوشه فعلی)
source.dir = .

# (list) پسوندهای مجازی که باید داخل APK قرار بگیرند
source.include_exts = py,png,jpg,kv,atlas,json

# (str) نسخه برنامه
version = 0.0.2

# (list) کتابخانه‌های مورد نیاز پایتون (بسیار مهم)
requirements = python3,kivy==2.3.0,requests

# (str) جهت صفحه نمایش گوشی (portrait = عمودی)
orientation = portrait

# (bool) آیا برنامه تمام‌صفحه (بدون نوار ساعت و باتری بالای گوشی) باشد؟
fullscreen = 0

# (list) دسترسی‌های اندروید (مجوز اینترنت برای اسکنر کاملاً حیاتی است)
android.permissions = INTERNET

# (int) نسخه API هدف اندروید (33 برای اندروید 13 بسیار پایدار است)
android.api = 33

# (int) حداقل نسخه اندروید برای نصب برنامه (21 یعنی اندروید 5 به بالا)
android.minapi = 21

# (str) معماری‌های پردازنده گوشی (پشتیبانی از اکثر گوشی‌های جدید و قدیمی)
android.archs = arm64-v8a, armeabi-v7a

# (bool) اجازه بکاپ‌گیری خودکار توسط اندروید
android.allow_backup = True

# 🎯 (بسیار مهم برای گیت‌هاب اکشن) تأیید خودکار لایسنس‌های گوگل برای جلوگیری از فریز شدن سرور
android.accept_sdk_license = True


[buildozer]

# (int) سطح نمایش لاگ‌ها (2 یعنی نمایش کامل جزئیات در تب Actions گیت‌هاب)
log_level = 2

# (int) نمایش اخطار در صورت اجرای بیلدوزر با دسترسی روت
warn_on_root = 1
