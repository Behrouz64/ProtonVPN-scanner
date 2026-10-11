# ProtonVPN Scanner 1.0.2

ابزاری برای پیدا کردن سرورهای ProtonVPN که از نظر پینگ واقعاً در دسترس هستند، همراه با خروجی کانفیگ WireGuard و AmneziaWG. رابط دو زبانه است (فارسی و English) و راهنمای کامل داخل خود برنامه، در تب **راهنما**، هست.

> ابزاری غیررسمی است و ارتباطی با Proton AG ندارد.

## اجرا روی macOS

### ۱. نصب Python 3.11

```bash
brew install python@3.11
python3.11 --version
```

خروجی آخر باید `Python 3.11.x` باشد. دستورهای این راهنما را بدون توضیح کنار آن‌ها کپی کنید. zsh (پوسته‌ی پیش‌فرض macOS) توضیح‌های `#` را به‌طور پیش‌فرض نادیده نمی‌گیرد و آن‌ها را دستور حساب می‌کند، و در نتیجه `cd` یا `pip` بدون اجرای درست می‌ماند.

### ۲. محیط مجازی و وابستگی‌ها

```bash
cd ProtonVPN-scanner
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

از `python -m pip` استفاده کنید، نه `pip` تنها. `requirements-dev.txt` این‌ها را نصب می‌کند:

| بسته | کاربرد |
| --- | --- |
| `flet==1.0.4` و `flet-desktop==1.0.4` | رابط گرافیکی |
| `requests` | دانلود دیتابیس سرورها |
| `qrcode` | ساختن کد QR (بدون نیاز به zbar یا Homebrew) |

### ۳. تست‌ها

```bash
python -m unittest -v
```

آخر خروجی باید `OK` باشد. اگر تست‌های QR با `skipped 'qrcode is not installed'` رد شدند، مرحله‌ی ۲ را دوباره اجرا کنید.

### ۴. اجرای برنامه

```bash
python main.py
```

اولین اجرا کلاینت دسکتاپ Flet را از GitHub دانلود می‌کند، پس اینترنت لازم است.

## کار با برنامه (خلاصه)

کامل‌ترین توضیح در تب **راهنما** است. خلاصه:

1. **دیتابیس**: `بارگذاری دیتابیس` فهرست سرورها را می‌گیرد. دکمه‌ی بارگذاری دوباره، فهرست تازه می‌گیرد.
2. **فیلتر**: نوع سرور (رایگان، پولی، همه) و در صورت نیاز قاره و کشور.
3. **اسکن**: VPN را کامل خاموش کنید، سپس `شروع اسکن (۵۰۰)` را بزنید. سرورهایی که پینگشان زیر ۱۰ میلی‌ثانیه است حذف می‌شوند.
4. **سرورها**: کلید خصوصی WireGuard را وارد کنید. برای هر سرور می‌توانید IP، لینک `wg://`، کانفیگ، کد QR یا فایل `.conf` بگیرید.
5. **تنظیمات**: زبان، روشن یا خاموش بودن پنهان‌سازی AmneziaWG و بازگردانی مقادیر پیشنهادی.

سروری که «سالم» نشان داده می‌شود فقط از غربالگری پینگ اولیه گذشته است. برای اطمینان، لینک‌ها یا فایل‌های `.conf` را در یک کلاینت واقعی مثل Shadowrocket یا AmneziaVPN تست کنید. لینک‌های این برنامه‌ها و توضیح بیشتر در تب **راهنما** است.

کلید خصوصی فقط در همان پنجره نگه داشته می‌شود و برنامه آن را ذخیره یا منتشر نمی‌کند. کلید را در چت، عکس صفحه یا فروم نفرستید.

## ساختار پروژه

| فایل | کاربرد |
| --- | --- |
| `main.py` | رابط Flet، وضعیت برنامه و دکمه‌ها |
| `ui_parts.py` | رنگ‌ها، دکمه‌ها، کارت سرور، کد QR و بلوک‌های راهنما |
| `i18n.py` | متن‌های فارسی و انگلیسی و تبدیل جهت متن لاتین |
| `guide_content.py` | متن راهنمای داخلی به دو زبان |
| `app_settings.py` | ذخیره‌ی تنظیمات (زبان و AmneziaWG) بدون کلید خصوصی |
| `scanner_core.py` | منطق بدون وابستگی به رابط: دیتابیس، فیلترها، پینگ، کانفیگ، لینک و QR |
| `assets/fonts/` | فونت وزیرمتن (SIL OFL) برای حروف فارسی |
| `tests/` | تست‌های واحد |
| `pyproject.toml` | نسخه و تنظیمات `flet build` |

## ساخت APK

workflow با نام `Build Android APK` را به صورت دستی اجرا کنید. این workflow با `flet build apk` ساخته شده و هنوز اجرا نشده است؛ اگر خطا داد، لاگ آن را نگه دارید.

## نسخه ۱.۰.۲

- رابط از Kivy به Flet منتقل شد و ظاهر تیره‌ی بنفش ProtonVPN را دارد.
- راهنمای داخلی دو زبانه در تب راهنما اضافه شد.
- تنظیمات AmneziaWG (روشن/خاموش و بازگردانی مقادیر پیشنهادی) به صورت فرم است و دیگر کادر متنی نیست.
- پیام‌های خطا با کد ثابت ساخته می‌شوند و به زبان انتخاب‌شده نمایش داده می‌شوند.

---

## English summary

ProtonVPN Scanner finds ProtonVPN servers that answer quickly from your network, then builds WireGuard or AmneziaWG configs, `wg://` links and QR codes for them. The interface is bilingual (فارسی / English), and the full guide, including how to get your WireGuard private key from Proton, is in the **Guide** tab inside the app.

Run it on macOS:

```bash
python3.11 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest -v
python main.py
```

A server shown as alive has only passed the first ping screen. Test the configs in a real client such as Shadowrocket or AmneziaVPN; the Guide tab has the links.

Turn the VPN off before scanning. Never share your private key. This is an unofficial tool and is not affiliated with Proton AG.
