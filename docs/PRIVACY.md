# سیاست حریم خصوصی ProtonVPN Scanner

این برنامه غیررسمی است و ارتباطی با Proton AG ندارد. این صفحه می‌گوید چه داده‌ای ذخیره یا ارسال می‌شود.

## داده‌هایی که روی دستگاه ذخیره می‌شوند

| داده | کجا ذخیره می‌شود | توضیح |
| --- | --- | --- |
| زبان، تنظیمات AmneziaWG، روش اسکن و آستانه‌ی پاسخ فیک | تنظیمات محلی برنامه | کلید خصوصی در آن ذخیره نمی‌شود |
| کش فهرست سرورها | `~/.protonvpn-scanner/cache_github.json` | برای اجرای سریع‌تر، حدود یک ساعت اعتبار دارد |
| IP سرورهای Surfshark | `~/.protonvpn-scanner/surfshark_ips.json` | فقط نام میزبان و IPهای عمومی؛ ۲۴ ساعت اعتبار دارد |
| کانفیگ‌های صادرشده | `~/.protonvpn-scanner/wireguard/` | با مجوز فقط برای خودتان (۰۶۰۰)، هر فایل کلید خصوصی شما را دارد |

روی موبایل، این پوشه همان پوشه‌ی داده‌ی خصوصی برنامه است که سیستم عامل تعیین می‌کند.

## کلید خصوصی

- کلید فقط در حافظه‌ی همان اجرای برنامه نگه داشته می‌شود و با بستن برنامه پاک می‌شود.
- برای Surfshark فقط کلید خصوصی وارد می‌شود؛ آدرس و DNS تونل مقادیر پیش‌فرض Surfshark است. کلید هیچ‌جا ذخیره نمی‌شود.
- وقتی کانفیگ، لینک `wg://` یا کد QR می‌سازید، کلید داخل آن قرار می‌گیرد. هر کسی به آن دسترسی داشته باشد می‌تواند از آن استفاده کند.
- اگر فکر می‌کنید کلید لو رفته، آن را در حساب Proton خود دوباره بسازید.

## اتصال‌های شبکه

- **دانلود فهرست سرورها** از منبع ثالث `tn3w/ProtonVPN-IPs` از این آدرس‌ها:
  - `https://fastly.jsdelivr.net/gh/tn3w/ProtonVPN-IPs@master/protonvpn_logicals.json`
  - `https://raw.githubusercontent.com/tn3w/ProtonVPN-IPs/refs/heads/master/protonvpn_logicals.json`
  - `https://gh-proxy.com/https://raw.githubusercontent.com/tn3w/ProtonVPN-IPs/refs/heads/master/protonvpn_logicals.json`
- **پینگ و Handshake Proton:** در روش «با کلید» یک پیام Handshake WireGuard با کلید خودتان به پورت UDP 51820 سرورهای Proton فرستاده می‌شود؛ در روش «بدون کلید» فقط پینگ TCP 443 و UDP 80 فرستاده می‌شود. در حالت Surfshark بدون کلید، نام میزبان هر سرور از DNS سیستم شما به IP تبدیل می‌شود و همین پینگ فرستاده می‌شود؛ کلید فرستاده نمی‌شود.
- **تست Surfshark با کلید (پیش‌فرض):** یک پیام Handshake WireGuard با کلید خودتان به پورت UDP 51820 سرورهای Surfshark. نام میزبان هر سرور از DNS سیستم شما به حداکثر دو IP تبدیل می‌شود. هیچ ورود به حساب Surfshark و هیچ خواندن API انجام نمی‌شود. فهرست سرورهای Surfshark از فایل همراه برنامه خوانده می‌شود و از اینترنت دانلود نمی‌شود.
- **DNS سرورهای Surfshark:** نام میزبان‌ها با DNS سیستم شما حل می‌شوند؛ هنگام «گرفتن IP» و هنگام اسکن (وقتی کش تازه نیست). اگر VPN روشن باشد، این درخواست‌ها از تونل می‌روند.
- **باز کردن لینک‌ها** (راهنما، کانال Telegram، صفحه‌ی X) فقط با مرورگر شما انجام می‌شود.

## آنچه جمع‌آوری یا ارسال نمی‌شود

- هیچ telemetry، آمار استفاده، گزارش کرش یا تبلیغاتی وجود ندارد.
- به جز درخواست‌های بالا، هیچ داده‌ای به نویسنده یا سرور دیگری ارسال نمی‌شود.

## حذف داده‌ها

- حذف برنامه داده‌های داخل برنامه را پاک می‌کند.
- روی مک، پوشه‌ی `~/.protonvpn-scanner` پس از حذف برنامه باقی می‌ماند. اگر کانفیگ‌ها را نمی‌خواهید، آن را خودتان پاک کنید.

---

## Privacy (English summary)

ProtonVPN Scanner stores your language, AmneziaWG, scan-method and fake-reply threshold settings, a one-hour server-list cache, a 24-hour cache of Surfshark public IP addresses, and any config files you export (these contain your private key, with owner-only permissions). The private key is never written to the settings store and is kept in memory only while the app runs.

The app downloads the server list from a third-party repository (`tn3w/ProtonVPN-IPs`), pings server IPs on TCP 443 and UDP 80, and, with the with-key scan method (default), sends a WireGuard handshake with your key to UDP 51820 for ProtonVPN and Surfshark servers; the no-key method only pings; Surfshark hostnames are resolved with the system DNS. It opens links only in your browser. It has no telemetry, analytics or crash reporting, and sends no data to the author.
