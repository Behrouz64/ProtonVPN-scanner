# یادداشت‌های ساخت برای Flet (نتیجه‌ی این پروژه)

این فایل نکاتی است که در ساخت و تست برنامه روی Android و iOS به دست آمد. برای پروژه‌های Flet بعدی هم همین روش را دنبال کنید.

## ساختار برنامه

- `ft.run(main, assets_dir=...)` را در سطح ماژول صدا بزنید، نه داخل `if __name__ == "__main__"`. روی موبایل ماژول با نام دیگری بارگذاری می‌شود.
- اگر import ماژول‌ها خطا بدهد، بدون `try` کل برنامه قبل از ساخت صفحه متوقف می‌شود و صفحه سیاه می‌ماند. import‌ها را داخل `try` بگذارید و خطا را روی صفحه نشان دهید.
- ساخت شیء اصلی برنامه (`ScannerApp(page)`) را هم داخل `try` بگذارید.
- محتوای اصلی را داخل `ft.SafeArea` بگذارید. بدون آن، هدر زیر ساعت و جزیره‌ی دوربین آیفون قرار می‌گیرد.
- فونت فارسی را در `assets/fonts` بگذارید و در `page.fonts` معرفی کنید.
- همه‌ی فایل‌های داخل `assets/` داخل برنامه‌ی نهایی قرار می‌گیرند. یادداشت‌ها و فایل‌های غیرضروری را اینجا نگذارید.

## Android

- پروژه را با `flet build apk --yes --arch <arch>` بسازید.
- نسخه‌های تأییدشده روی گوشی ۶۴ بیتی: `arm64-v8a` و `universal` (`arm64-v8a x86_64`).
- نسخه‌ی `armeabi-v7a` (۳۲ بیتی) کرش کرد: Python داخل APK کتابخانه‌ی `lib_ctypes.so` را پیدا نکرد. اگر به پشتیبانی ۳۲ بیتی نیاز دارید، ابتدا بسته‌بندی را بررسی کنید.
- معماری گوشی را بررسی کنید:
  - `adb shell getprop ro.product.cpu.abi`
  - `adb shell dumpsys package <package> | grep primaryCpuAbi`
- لاگ Python روی Android با تگ `flet.python` ثبت می‌شود. برای گرفتن لاگ فقط از برنامه:
  - `adb logcat -c`
  - برنامه را باز کنید و چند ثانیه صبر کنید.
  - `adb logcat -d --pid=$(adb shell pidof -s <package>) > app.txt`

## iOS

- `flet build ipa` پرچم `--no-codesign` ندارد. بدون پروفایل امضا، خروجی یک `.xcarchive` بدون امضا است.
- برای ساخت IPA قابل نصب با Sideloadly، `Runner.app` را از داخل `.xcarchive/Products/Applications` بردارید، در پوشه‌ای به نام `Payload` بگذارید و زیپ کنید، بعد پسوند را به `.ipa` تغییر دهید.
- روی CI (macOS runner) بسازید. ساخت محلی روی مک نیازمند Xcode کامل است (حدود ۱۰ تا ۱۵ گیگابایت).
- نصب با Apple ID رایگان: Sideloadly را روی مک یا ویندوز اجرا کنید، IPA را بکشید و Apple ID را وارد کنید. نصب هر ۷ روز تمدید می‌شود و با Auto Refresh خودکار است.
- روی آیفون:
  - Developer Mode را در Settings → Privacy & Security روشن کنید (iOS 16 به بعد).
  - بعد از نصب، در Settings → General → VPN & Device Management به توسعه‌دهنده اعتماد کنید.
- اگر Privacy & Security را پیدا نکردید، Developer Mode را با اتصال گوشی به ابزار توسعه و تلاش برای نصب یک برنامه فعال کنید.

## CI (GitHub Actions)

- یک workflow با ورودی‌های boolean (`build_android`، `build_windows`، `build_ios`) بسازید. ورودی‌های پرهزینه (Windows و iOS) پیش‌فرض خاموش باشند.
- Flutter را روی نسخه‌ی ثابت بگذارید (در این پروژه `3.44.8`) و `flet-cli` را با نسخه‌ی `flet` یکی کنید (`1.0.4`).
- job تست را جدا کنید و بقیه‌ی job‌ها را `needs: tests` بگذارید.
- برای Windows: `PYTHONUTF8=1` و `FLET_CLI_NO_RICH_OUTPUT=1` را در مرحله‌ی build بگذارید. کل پوشه‌ی `build/windows` را زیپ کنید، نه فقط یک زیرپوشه.
- بعد از هر تغییر، یک build روی همان commit اجرا کنید و نتیجه‌ی job‌ها و حجم artifact را بررسی کنید.

## تست و بررسی محلی

- تست‌های واحد با `unittest` باشند. CI فقط `requests` و `qrcode` نصب می‌کند، پس تست‌ها نباید `flet` را import کنند.
- برای تست رابط بدون گوشی: یک runner وب با Flet بسازید و با Playwright مرورگر را باز کنید. در این محیط از `executable_path='/opt/pw-browsers/chromium'` استفاده کنید.
- Flet 1.0.4 را روی همه‌ی محیط‌ها (محلی، CI، و `flet-cli`) یکسان نگه دارید.

## Git و امنیت

- فقط روی branch تعیین‌شده commit و push کنید. PR را فقط وقتی بسازید که کاربر بخواهد.
- کلیدهای خصوصی و کانفیگ‌های واقعی را هرگز commit نکنید.
- در پیام commit نام مدل زبانی را ننویسید.
