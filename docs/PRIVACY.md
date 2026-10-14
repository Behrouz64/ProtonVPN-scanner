# سیاست حریم خصوصی ProtonVPN Scanner

این برنامه غیررسمی است و ارتباطی با Proton AG ندارد. این صفحه می‌گوید چه داده‌ای ذخیره یا ارسال می‌شود.

## داده‌هایی که روی دستگاه ذخیره می‌شوند

| داده | کجا ذخیره می‌شود | توضیح |
| --- | --- | --- |
| زبان و تنظیمات AmneziaWG | تنظیمات محلی برنامه | کلید خصوصی در آن ذخیره نمی‌شود |
| کش فهرست سرورها | `~/.protonvpn-scanner/cache_github.json` | برای اجرای سریع‌تر، حدود یک ساعت اعتبار دارد |
| کانفیگ‌های صادرشده | `~/.protonvpn-scanner/wireguard/` | با مجوز فقط برای خودتان (۰۶۰۰)، هر فایل کلید خصوصی شما را دارد |

روی موبایل، این پوشه همان پوشه‌ی داده‌ی خصوصی برنامه است که سیستم عامل تعیین می‌کند.

## کلید خصوصی

- کلید فقط در حافظه‌ی همان اجرای برنامه نگه داشته می‌شود و با بستن برنامه پاک می‌شود.
- برای Surfshark، متن فایل `.conf` که می‌چسبانید پس از خوانده شدن از کادر پاک می‌شود. فقط بخش `[Interface]` خوانده می‌شود و هیچ‌جا ذخیره نمی‌شود.
- وقتی کانفیگ، لینک `wg://` یا کد QR می‌سازید، کلید داخل آن قرار می‌گیرد. هر کسی به آن دسترسی داشته باشد می‌تواند از آن استفاده کند.
- اگر فکر می‌کنید کلید لو رفته، آن را در حساب Proton خود دوباره بسازید.

## اتصال‌های شبکه

- **دانلود فهرست سرورها** از منبع ثالث `tn3w/ProtonVPN-IPs` از این آدرس‌ها:
  - `https://fastly.jsdelivr.net/gh/tn3w/ProtonVPN-IPs@master/protonvpn_logicals.json`
  - `https://raw.githubusercontent.com/tn3w/ProtonVPN-IPs/refs/heads/master/protonvpn_logicals.json`
  - `https://gh-proxy.com/https://raw.githubusercontent.com/tn3w/ProtonVPN-IPs/refs/heads/master/protonvpn_logicals.json`
- **پینگ** به IP سرورهای Proton روی TCP 443 و UDP 80.
- **تست Surfshark:** یک پیام Handshake WireGuard با کلید خودتان به پورت UDP 51820 سرورهای Surfshark. هیچ ورود به حساب Surfshark و هیچ خواندن API انجام نمی‌شود. فهرست سرورهای Surfshark از فایل همراه برنامه خوانده می‌شود و از اینترنت دانلود نمی‌شود.
- **باز کردن لینک‌ها** (راهنما، کانال Telegram، صفحه‌ی X) فقط با مرورگر شما انجام می‌شود.

## آنچه جمع‌آوری یا ارسال نمی‌شود

- هیچ telemetry، آمار استفاده، گزارش کرش یا تبلیغاتی وجود ندارد.
- به جز درخواست‌های بالا، هیچ داده‌ای به نویسنده یا سرور دیگری ارسال نمی‌شود.

## حذف داده‌ها

- حذف برنامه داده‌های داخل برنامه را پاک می‌کند.
- روی مک، پوشه‌ی `~/.protonvpn-scanner` پس از حذف برنامه باقی می‌ماند. اگر کانفیگ‌ها را نمی‌خواهید، آن را خودتان پاک کنید.

---

## Privacy (English summary)

ProtonVPN Scanner stores your language and AmneziaWG settings, a one-hour server-list cache, and any config files you export (these contain your private key, with owner-only permissions). The private key is never written to the settings store and is kept in memory only while the app runs.

The app downloads the server list from a third-party repository (`tn3w/ProtonVPN-IPs`), pings server IPs on TCP 443 and UDP 80, and opens links only in your browser. It has no telemetry, analytics or crash reporting, and sends no data to the author.
