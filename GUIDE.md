# راهنمای ProtonVPN Scanner / ProtonVPN Scanner Guide

این فایل دو بخش دارد: **بخش فارسی** و **English section**. محتوای هر دو یکی است؛ هر کدام را که راحت‌ترید بخوانید.

Contents: [فارسی](#فارسی) · [English](#english)

---

## فارسی

### ۱. این برنامه چه کاری می‌کند؟

ProtonVPN سرورهای زیادی دارد، اما همه‌ی آن‌ها از جای شما یک سرعت ندارند. این برنامه فهرست سرورها را می‌گیرد، **پینگ** هر سرور را اندازه می‌گیرد و سرورهایی را که سریع جواب می‌دهند نشان می‌دهد. بعد برای هر سرور یک **کانفیگ WireGuard** می‌سازد؛ یعنی فایل تنظیماتی که برنامه‌ی WireGuard برای وصل شدن لازم دارد.

چند واژه‌ی کوتاه:

- **پینگ (ping):** زمانی که یک پیام کوتاه تا سرور می‌رود و جواب برمی‌گردد. بر حسب میلی‌ثانیه (ms) اندازه‌گیری می‌شود. عدد کمتر یعنی جواب سریع‌تر.
- **کانفیگ (config):** فایل تنظیمات اتصال.
- **IP:** نشانی عددی سرور، مثلاً `203.0.113.7`.
- **کلید خصوصی (private key):** یک رشته‌ی طولانی از حروف و عدد که هویت حساب شما را در اتصال مشخص می‌کند. مثل رمز عبور با آن رفتار کنید.

### ۲. قبل از شروع

- **VPN را کامل خاموش کنید.** این شامل برنامه‌ی Proton و هر VPN دیگری است. اگر VPN روشن باشد، پینگ‌ها واقعی نیستند.
- برنامه را طبق بخش «اجرا و تست روی macOS» در `README.md` اجرا کنید.

### ۳. مراحل کار با برنامه

1. **1. LOAD DATABASE** را بزنید. فهرست سرورها دانلود می‌شود. دفعه‌های بعد از فایل ذخیره‌شده (کش) استفاده می‌شود. اگر می‌خواهید فهرست تازه بگیرید، **RELOAD DATABASE** را بزنید.
2. نوع سرور را انتخاب کنید: **FREE** (رایگان)، **PREMIUM** (پولی) یا **ALL** (همه).
3. در صورت نیاز از **All Continents** قاره و از **All Countries** کشور را انتخاب کنید.
4. **2. START SCAN (500)** را بزنید. برنامه پینگ ۵۰۰ سرور را می‌گیرد. تا نوار پیشرفت تمام شود صبر کنید.
   - سرورهایی که پینگشان **زیر ۱۰ میلی‌ثانیه** است حذف می‌شوند، چون چنین جواب سریعی معمولاً واقعی نیست.
5. وقتی اسکن تمام شد، نتیجه‌ها از سریع‌ترین به کندترین نشان داده می‌شوند. برای ادامه‌ی فهرست، **NEXT 500** را بزنید (VPN باید خاموش بماند). برای شروع دوباره از اول، **RESET** را بزنید.
6. هر **کارت** یک سرور است و نام، پینگ و IP آن را نشان می‌دهد. دکمه‌های کارت:
   - **COPY IP**: فقط IP سرور را کپی می‌کند.
   - **COPY LINK**: یک لینک `wg://` برای همین سرور کپی می‌کند. این فرمت را Shadowrocket می‌خواند. برای بقیه‌ی برنامه‌ها، `SAVE .CONF` یا QR را استفاده کنید.
   - **COPY WG**: کانفیگ کامل WireGuard را کپی می‌کند.
   - **QR**: کد QR کانفیگ را نشان می‌دهد. با گوشی و برنامه‌ی WireGuard (گزینه‌ی *Create from QR code*) از روی صفحه اسکن کنید.
   - **SAVE .CONF**: فایل `.conf` را در پوشه‌ی `wireguard` ذخیره می‌کند.
7. **COPY wg:// LINKS** لینک همه‌ی سرورهای اسکن‌شده را کپی می‌کند، هر سرور در یک خط. محدوده‌ی آن کشور یا قاره‌ای است که در اسپینرها انتخاب کرده‌اید، یا همه‌ی کشورها اگر هیچ‌کدام انتخاب نشده باشد.
8. **EXPORT TOP 15 (.conf)** ۱۵ سرور برتر را به صورت فایل `.conf` ذخیره می‌کند. مسیر پوشه در نوار وضعیت پایین صفحه نشان داده می‌شود.

> **مهم:** کلید خصوصی را **قبل از** COPY، QR، SAVE یا EXPORT در کادر **WireGuard private key** وارد کنید. اگر کلید را بعد از ساختن فایل وارد کنید، آن فایل‌ها بدون کلید هستند (به جای کلید، `<PASTE_YOUR_PRIVATE_KEY>` می‌نویسند) و باید دوباره ساخته شوند.

### ۴. گرفتن کلید خصوصی از حساب Proton

> این مراحل بر اساس راهنمای Proton برای WireGuard است. اگر صفحه‌ها کمی با تصویر زیر فرق داشتند، دنبال همین اسم‌ها باشید: **Downloads** و **WireGuard configuration**. Proton ممکن است منوها را تغییر دهد.

1. مرورگر را باز کنید و به **account.protonvpn.com** بروید. با نام کاربری و رمز حساب Proton وارد شوید.
2. بخش **Downloads** را باز کنید و **WireGuard configuration** را انتخاب کنید.
3. **Platform** (پلتفرم) را انتخاب کنید. برای گرفتن کلید مهم این است که فایل دانلودشده خط `PrivateKey` داشته باشد. اگر نداشت، گزینه‌ی دیگری را امتحان کنید.
4. کانفیگ را بسازید و **همان لحظه** دانلودش کنید. کلید خصوصی فقط بعد از ساخت کانفیگ و برای مدت کوتاهی نمایش داده می‌شود. اگر بعداً فایل را دوباره دانلود کنید، کلید به صورت ستاره (`***`) دیده می‌شود.
5. فایل را با یک ویرایشگر متن باز کنید:
   - روی Mac: **TextEdit**
   - روی ویندوز: **Notepad**
6. خطی را پیدا کنید که با `PrivateKey =` شروع می‌شود. فقط **رشته‌ی بعد از علامت `=`** را کپی کنید. این رشته معمولاً حدود ۴۴ کاراکتر است و آخرش `=` دارد. خود عبارت `PrivateKey =` را کپی نکنید.
7. آن رشته را در کادر **WireGuard private key** برنامه بچسبانید.

**اگر فایل به جای کلید ستاره (`***`) نشان داد:** یک کانفیگ جدید بسازید، چند ثانیه صبر کنید و بعد دانلود کنید.

### ۵. امنیت کلید

- **کلید خصوصی را جایی منتشر نکنید:** نه در چت، نه در عکس صفحه، نه در فروم یا گیت‌هاب. هر کسی که کلید را داشته باشد می‌تواند از کانفیگ شما استفاده کند.
- فایل‌های `.conf`، لینک‌های `wg://`، کدهای QR و متنی که با COPY WG کپی می‌کنید، همه کلید دارند. آن‌ها را مثل رمز عبور نگه دارید.
- بعد از استفاده، کلیپ‌بورد را پاک کنید؛ مثلاً یک متن دلخواه دیگر را کپی کنید.
- اگر فکر می‌کنید کلید لو رفته، یک کانفیگ جدید از Proton بگیرید و از کانفیگ قبلی دیگر استفاده نکنید.

### ۶. کادر AmneziaWG

- به طور پیش‌فرض این کادر پر است: `Jc = 4`، `Jmin = 50`، `Jmax = 1000`، `S1 = 0`، `S2 = 0`، و `H1 = 1` تا `H4 = 4`.
- با این مقادیر فایل‌ها به صورت AmneziaWG ساخته می‌شوند و پسوند `_awg.conf` دارند.
- اگر می‌خواهید WireGuard ساده بسازید، **کل کادر را خالی کنید**.
- این مقادیر باید با تنظیمات **سروری** که به آن وصل می‌شوید یکی باشند. فقط تنظیم کلاینت کافی نیست؛ اگر سرور AmneziaWG را پشتیبانی نکند، اتصال برقرار نمی‌شود.
- کلید خصوصی را داخل این کادر نچسبانید.

### ۷. مشکل‌های رایج

- **همه‌ی سرورها dead یا fake هستند:** مطمئن شوید VPN کاملاً خاموش است. گزینه‌های Kill Switch یا Always-on را هم بررسی کنید.
- **فهرست لود نمی‌شود:** اینترنت یا فیلترینگ را بررسی کنید. اگر کش قدیمی وجود داشته باشد، برنامه از آن استفاده می‌کند.
- **کانفیگ وصل نمی‌شود:** کلید را دوباره کپی کنید و مطمئن شوید فاصله‌ی اضافه ندارد و آخرش `=` است. کادر AmneziaWG را بررسی کنید. اگر سرور AmneziaWG ندارد، کادر را خالی کنید.
- **چند نام با یک IP:** بعضی سرورها چند نام منطقی دارند (مثلاً `RO#9` و `RO#31`) که روی یک میزبان هستند. برنامه آن‌ها را یک بار نشان می‌دهد و نام‌های دیگر را کنارش می‌آورد، مثلاً `RO#9 (+3)`.
- **لینک `wg://` در برنامه‌ی من کار نمی‌کند:** فرمت این لینک با Shadowrocket آزمایش شده است. برای بقیه‌ی برنامه‌ها فایل `.conf` یا QR را امتحان کنید.

### ۸. محل فایل‌ها روی macOS

- کش فهرست سرورها: `~/Library/Application Support/protonscanner/cache_github.json`
- فایل‌های `.conf`: `~/Library/Application Support/protonscanner/wireguard/`

در Finder می‌توانید از منوی **Go > Go to Folder** این مسیرها را باز کنید.

---

## English

This guide has two parts: **فارسی** (above) and this **English section**. Both cover the same material.

### 1. What the app does

ProtonVPN has many servers, and they do not all respond at the same speed from where you are. This app downloads the server list, measures the **ping** of each server, and shows the ones that answer quickly. For each server it builds a **WireGuard config**: the settings file that the WireGuard app needs to connect.

Short definitions:

- **Ping:** the time a small message takes to reach a server and come back, in milliseconds (ms). Lower is faster.
- **Config:** a settings file for a connection.
- **IP:** a server's numeric address, for example `203.0.113.7`.
- **Private key:** a long string of letters and numbers that identifies your account in a connection. Treat it like a password.

### 2. Before you start

- **Turn the VPN off completely.** This includes the Proton app and any other VPN. If a VPN is on, the ping numbers are not real.
- Run the app as described in the "Run and test on macOS" section of `README.md`.

### 3. How to use the app

1. Press **1. LOAD DATABASE**. The server list is downloaded. Later runs use the saved copy (cache). To get a fresh list, press **RELOAD DATABASE**.
2. Choose the server type: **FREE**, **PREMIUM**, or **ALL**.
3. If you want, pick a continent in **All Continents** and a country in **All Countries**.
4. Press **2. START SCAN (500)**. The app measures the ping of 500 servers. Wait until the progress bar finishes.
   - Servers with a ping **under 10 ms** are removed, because such a fast reply is usually not real.
5. When the scan finishes, results are listed from fastest to slowest. To continue with the next group, press **NEXT 500** (keep the VPN off). To start again from the beginning, press **RESET**.
6. Each **card** is one server and shows its name, ping, and IP. The card buttons:
   - **COPY IP**: copies only the server's IP.
   - **COPY LINK**: copies a `wg://` link for this server. Shadowrocket reads this format. For other apps, use `SAVE .CONF` or the QR code.
   - **COPY WG**: copies the full WireGuard config.
   - **QR**: shows a QR code for the config. Scan it from the screen with your phone and the WireGuard app (*Create from QR code*).
   - **SAVE .CONF**: saves a `.conf` file to the `wireguard` folder.
7. **COPY wg:// LINKS** copies the links of all scanned servers, one per line. The scope is the country or continent you selected in the spinners, or all servers if none is selected.
8. **EXPORT TOP 15 (.conf)** saves the 15 best servers as `.conf` files. The folder path appears in the status bar at the bottom.

> **Important:** enter the private key in the **WireGuard private key** box **before** you use COPY, QR, SAVE, or EXPORT. If you enter it after a file was made, that file has no key (it contains `<PASTE_YOUR_PRIVATE_KEY>` instead), so make the file again.

### 4. Getting the private key from your Proton account

> These steps are based on Proton's WireGuard guidance. If a page looks a little different, look for the same names: **Downloads** and **WireGuard configuration**. Proton may change its menus.

1. Open your browser, go to **account.protonvpn.com**, and sign in with your Proton Account username and password.
2. Open **Downloads**, then choose **WireGuard configuration**.
3. Choose a **Platform**. What matters for the key is that the downloaded file contains a `PrivateKey` line. If it does not, try another platform option.
4. Create the config and **download it right away**. The private key is shown only briefly after the config is created. If you download the file again later, the key appears as asterisks (`***`).
5. Open the file in a plain text editor:
   - On Mac: **TextEdit**
   - On Windows: **Notepad**
6. Find the line that starts with `PrivateKey =`. Copy only **the text after the `=` sign**. It is usually about 44 characters and ends with `=`. Do not copy the `PrivateKey =` part itself.
7. Paste that text into the **WireGuard private key** box in the app.

**If the file shows asterisks (`***`) instead of the key:** create a new config, wait a few seconds, and download it again.

### 5. Keeping the key safe

- **Never share the private key:** not in a chat, not in a screenshot, not on a forum, and not on GitHub. Anyone who has it can use your config.
- The `.conf` files, `wg://` links, QR codes, and text copied with COPY WG all contain the key. Keep them as private as a password.
- After you use the clipboard, clear it, for example by copying some other harmless text.
- If you think the key was exposed, create a new config in Proton and stop using the old one.

### 6. The AmneziaWG box

- By default the box is filled with: `Jc = 4`, `Jmin = 50`, `Jmax = 1000`, `S1 = 0`, `S2 = 0`, and `H1 = 1` to `H4 = 4`.
- With these values, the files are built as AmneziaWG configs and get the `_awg.conf` suffix.
- For a plain WireGuard config, **clear the whole box**.
- These values must match the settings of the **server** you connect to. Changing only the client is not enough. If the server does not support AmneziaWG, the connection will not start.
- Never paste the private key into this box.

### 7. Common problems

- **All servers show as dead or fake:** make sure the VPN is completely off. Also check Kill Switch or Always-on settings.
- **The list does not load:** check your internet connection or filtering. If an old cache exists, the app uses it.
- **The config does not connect:** copy the key again. Make sure there are no extra spaces and that it ends with `=`. Check the AmneziaWG box. If the server does not support AmneziaWG, clear the box.
- **Several names with one IP:** some servers have more than one logical name (for example `RO#9` and `RO#31`) on the same host. The app scans that host once and shows the other names next to the main one, such as `RO#9 (+3)`.
- **The `wg://` link does not work in my app:** this link format was tested with Shadowrocket. For other apps, try the `.conf` file or the QR code.

### 8. Where the files are on macOS

- Server list cache: `~/Library/Application Support/protonscanner/cache_github.json`
- `.conf` files: `~/Library/Application Support/protonscanner/wireguard/`

In Finder, you can open these paths from **Go > Go to Folder**.
