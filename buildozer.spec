[app]
# (str) Title of your application
title = Proton Scanner

# (str) Package name
package.name = protonscanner

# (str) Package domain (needed for android/ios packaging)
package.domain = org.behrouz

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning
version = 0.0.1

# (list) Application requirements
# مهم‌ترین بخش: کتابخانه‌های مورد نیاز برنامه شما
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,idna,charset-normalizer

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
# مجوز دسترسی به اینترنت برای اسکن سرورها
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (str) Android architecture to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
