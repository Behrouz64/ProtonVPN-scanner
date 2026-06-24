[app]

# (str) Title of your application
title = Proton Scanner

# (str) Package name
package.name = protonscanner

# (str) Package domain (needed for android/ios packaging)
package.domain = org.behrouz

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning
version = 0.0.1

# 🎯 قفل کردن پایتون هدف روی نسخه 3.11 جهت انطباق با پایتون سرور گیت‌هاب
requirements = python3==3.11,kivy==2.3.0,requests,urllib3==1.26.15,certifi,idna,charset-normalizer

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# 🎯 استفاده از نسخه رسمی و تست‌شده NDK 25c برای سازگاری کامل با فرآیند بیلد Kivy 2.3.0
android.ndk = 25c

# (str) Android architecture to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature
android.allow_backup = True

# تایید خودکار لایسنس‌ها در سطح بیلدوزر
android.accept_sdk_license = True

[buildozer]

# (int) Log level (2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
