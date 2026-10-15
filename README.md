# ProtonVPN Scanner 1.0.2

ابزاری برای پیدا کردن سرورهای ProtonVPN که از نظر پینگ واقعاً در دسترس هستند، همراه با خروجی کانفیگ WireGuard و AmneziaWG. رابط دو زبانه است (فارسی و English) و راهنمای کامل داخل خود برنامه، در تب **راهنما**، هست.

> ابزاری غیررسمی است و ارتباطی با Proton AG ندارد.

## منابع رسمی و هشدار

- منبع رسمی این برنامه فقط همین مخزن GitHub است: `https://github.com/Behrouz64/ProtonVPN-scanner`. فایل‌ها را فقط از build‌های بخش Actions همین مخزن دانلود کنید.
- نسخه‌هایی که با همین نام از جای دیگری پخش می‌شوند ممکن است تغییر کرده یا ناامن باشند. نویسنده مسئول آن‌ها نیست.
- [سیاست حریم خصوصی](docs/PRIVACY.md) و [گزارش امنیتی](.github/SECURITY.md).

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
2. **محدوده**: سرویس (ProtonVPN، Surfshark یا همه) را در تب اسکن یا تب سرورها انتخاب کنید. در تب سرورها نوع سرور، قاره و کشور هم هست. فهرست محدوده بدون اسکن نشان داده می‌شود و اسکن از همان محدوده شروع می‌شود.
3. **اسکن**: VPN را کامل خاموش کنید، سپس `شروع اسکن (۵۰۰)` را بزنید. سرورهایی که پاسخشان زیر «آستانه‌ی پاسخ فیک» باشد حذف می‌شوند. این آستانه در تب **تنظیمات** است؛ پیش‌فرضش ۱۰ میلی‌ثانیه است و می‌توانید آن را خاموش کنید یا ۵، ۲۰ و ۵۰ میلی‌ثانیه بگذارید.
4. **سرورها**: خروجی و کپی گروهی در بالای تب است. زیر آن محدوده را انتخاب کنید و فهرست سرورها را پیش از اسکن با IP و وضعیت تست ببینید. هر کارت کپی IP، لینک `wg://`، کپی WG، QR و فایل `.conf` دارد. سرورهای پاسخ‌دهنده بالای فهرست و بر اساس پینگ مرتب می‌شوند.
5. **تنظیمات**: زبان، روشن یا خاموش بودن پنهان‌سازی AmneziaWG، **روش اسکن** (با کلید یا بدون کلید)، **آستانه‌ی پاسخ فیک**، **تعداد IP برای هر میزبان Surfshark** (پیش‌فرض ۴) و بازگردانی مقادیر پیشنهادی.
6. **Surfshark**: سرویس **Surfshark** را در تب اسکن یا تب سرورها انتخاب کنید (در نوع سرور، «همه» خودکار انتخاب می‌شود). کلید خصوصی WireGuard را در کارت کلید Surfshark در تب **تنظیمات** وارد کنید؛ مثل ProtonVPN. کلید فقط در حافظه‌ی برنامه می‌ماند و ذخیره نمی‌شود. آدرس و DNS تونل از مقادیر پیش‌فرض Surfshark (`10.14.0.2/16`) گرفته می‌شود. **قبل از اسکن:** VPN را روشن کنید و دکمه‌ی «گرفتن IP سرورهای Surfshark» را در تب تنظیمات بزنید (یک بار در روز کافی است)، سپس VPN را خاموش کنید و اسکن کنید. IPها ۲۴ ساعت ذخیره می‌شوند و در فهرست سرورها نمایش داده می‌شوند. برنامه همیشه IPهای ذخیره‌شده و DNS زنده را امتحان می‌کند و IPهای خصوصی یا ساختگی را کنار می‌گذارد. اگر هیچ IP عمومی پیدا نشود، کانفیگ با نام میزبان نوشته می‌شود. در روش **با کلید** (پیش‌فرض)، برنامه برای هر IP یک پیام Handshake واقعی WireGuard به پورت UDP 51820 می‌فرستد و فقط سرورهایی که پاسخ بدهند نشان داده می‌شوند. در روش **بدون کلید** کلید لازم نیست و فقط پینگ TCP 443 و UDP 80 فرستاده می‌شود؛ این نتیجه تأیید WireGuard نیست و برای ساخت کانفیگ همچنان کلید لازم است.

در نام کانفیگ‌ها و لینک‌های `wg://` نشانه‌ی سرویس می‌آید: 🟣 یعنی Proton و 🦈 یعنی Surfshark. پرچم هر کشور هم کنار سرور نمایش داده می‌شود.

سروری که «سالم» نشان داده می‌شود فقط از غربالگری پینگ اولیه گذشته است. برای اطمینان، لینک‌ها یا فایل‌های `.conf` را در یک کلاینت واقعی مثل Shadowrocket یا AmneziaVPN تست کنید. لینک‌های این برنامه‌ها (از جمله Hiddify برای Android، Windows، macOS و iPhone) و توضیح بیشتر در تب **راهنما** است.

کلید خصوصی در تنظیمات برنامه ذخیره نمی‌شود و فقط در حافظه‌ی همان اجرا نگه داشته می‌شود. تنها وقتی کانفیگ یا فایل `.conf` صادر کنید، کلید داخل آن فایل نوشته می‌شود؛ آن فایل را منتشر نکنید و کلید را در چت، عکس صفحه یا فروم نفرستید.

## ساختار پروژه

| فایل | کاربرد |
| --- | --- |
| `main.py` | رابط Flet، وضعیت برنامه و دکمه‌ها |
| `ui_parts.py` | رنگ‌ها، دکمه‌ها، کارت سرور، کد QR و بلوک‌های راهنما |
| `i18n.py` | متن‌های فارسی و انگلیسی و تبدیل جهت متن لاتین |
| `guide_content.py` | متن راهنمای داخلی به دو زبان |
| `app_settings.py` | ذخیره‌ی تنظیمات (زبان و AmneziaWG) بدون کلید خصوصی |
| `scanner_core.py` | منطق بدون وابستگی به رابط: دیتابیس، فیلترها، پینگ، کانفیگ، لینک و QR |
| `surfshark_core.py` | تست UDP سرورهای Surfshark با پیام Handshake واقعی |
| `wg_crypto.py` | ساخت پیام Handshake با کتابخانه‌ی استاندارد پایتون (بدون وابستگی به `cryptography`) |
| `assets/surfshark/servers.json` | فهرست سرورهای Surfshark (فقط کلید عمومی و نام میزبان) |
| `assets/flags/` | پرچم کشورها به صورت PNG (مجوز MIT، از `flag-icons`) |
| `tools/` | ابزارهای توسعه برای ساخت فهرست Surfshark و پرچم‌ها (داخل برنامه نمی‌آید) |
| `assets/` | فایل‌های داخل برنامه: فونت وزیرمتن (SIL OFL) و آیکون |
| `docs/` | سیاست حریم خصوصی و یادداشت‌های ساخت (داخل بسته‌ی برنامه نمی‌آید) |
| `tests/` | تست‌های واحد |
| `pyproject.toml` | نسخه و تنظیمات `flet build` |

## ساخت APK

workflow با نام `Build apps` را از تب Actions به صورت دستی اجرا کنید و گزینه‌ی `build_android` را روشن بگذارید. دو فایل APK ساخته می‌شود:

- `android-modern-64bit`: برای گوشی‌های اندروید ۶۴ بیتی (arm64).
- `android-universal`: همان ۶۴ بیتی به‌همراه x86_64 (مثلاً شبیه‌ساز).

نسخه‌ی ۳۲ بیتی (armeabi-v7a) پشتیبانی نمی‌شود؛ روی گوشی‌های تست‌شده اجرا نشد.

## نسخه ۱.۰.۲

- رابط از Kivy به Flet منتقل شد و ظاهر تیره‌ی بنفش ProtonVPN را دارد.
- راهنمای داخلی دو زبانه در تب راهنما اضافه شد.
- تنظیمات AmneziaWG (روشن/خاموش و بازگردانی مقادیر پیشنهادی) به صورت فرم است و دیگر کادر متنی نیست.
- پیام‌های خطا با کد ثابت ساخته می‌شوند و به زبان انتخاب‌شده نمایش داده می‌شوند.

---

## English summary

ProtonVPN Scanner finds ProtonVPN servers that answer quickly from your network, then builds WireGuard or AmneziaWG configs, `wg://` links and QR codes for them. The interface is bilingual (فارسی / English), and the full guide, including how to get your WireGuard private key from Proton, is in the **Guide** tab inside the app.

**Official source:** this repository only (`https://github.com/Behrouz64/ProtonVPN-scanner`). Download builds only from its Actions runs. Modified copies published under the same name may be unsafe, and the author is not responsible for them.

Run it on macOS:

```bash
python3.11 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest -v
python main.py
```

A server shown as alive has only passed the first ping screen. Test the configs in a real client such as Shadowrocket, AmneziaVPN or Hiddify; the Guide tab has the links.

| Android build | Phones |
| --- | --- |
| `android-modern-64bit` | 64-bit (arm64) |
| `android-universal` | arm64 and x86_64 (emulators) |

32-bit (armeabi-v7a) is not supported.

**Surfshark:** choose Surfshark in the scan or Servers tab, then enter only your Surfshark WireGuard private key in the Surfshark key card on the Settings tab, the same way as ProtonVPN. The key stays in memory and is not saved. The tunnel address and DNS use Surfshark's default values (`10.14.0.2/16`). Surfshark and ProtonVPN entries are marked 🦈 and 🟣 in config names and `wg://` links, and country flags are shown next to each server. Servers are listed with their IP before any scan. **Get IPs first (optional but recommended):** with the VPN on, press *Get Surfshark IPs* on the Settings tab (once a day is enough), then turn the VPN off to scan. Saved IPs last 24 hours. The app always tries the saved IPs and live DNS and drops private or fake addresses, so DNS poisoning under censorship cannot hide a working server. If no public IP is found, configs are written with the host name. **Number of IPs per host (Settings, default 4):** each host is tested on up to that many IPs and the fastest usable one is kept. **Scan method (Settings tab):** *with key* (default) sends a real WireGuard handshake to each Surfshark IP on UDP 51820; *no key* needs no key and only pings TCP 443 and UDP 80, which is not a WireGuard check, and configs still need the key. **Fake-reply threshold (Settings tab, default 10 ms):** replies faster than the chosen value are dropped; it can also be turned off. **Export and copy in bulk** sit at the top of the Servers tab and use the count set in Settings.

Turn the VPN off before scanning. Never share your private key; exported `.conf` files contain it. The app has no telemetry. See [docs/PRIVACY.md](docs/PRIVACY.md) and [.github/SECURITY.md](.github/SECURITY.md). This is an unofficial tool and is not affiliated with Proton AG.
