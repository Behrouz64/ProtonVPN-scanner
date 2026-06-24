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

# (list) Application requirements
requirements = python3,kivy==2.3.0,requests,urllib3==1.26.15,certifi,idna,charset-normalizer

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

# استفاده از نسخه رسمی و همخوان NDK
android.ndk = 25c

# (str) Android architecture to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature
android.allow_backup = True

# تایید خودکار لایسنس‌ها
android.accept_sdk_license = True

# 🎯 تغییر بنیادین مهندسی: قفل کردن موتور اندروید روی نسخه پایدار سال 2024 جهت فرار از پایتون 3.14
p4a.branch = v2024.01.21

[buildozer]

# (int) Log level (2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
