"""متن‌های رابط کاربری به دو زبان. هر کلید باید در هر دو زبان وجود داشته باشد (تست‌ها این را بررسی می‌کنند)."""

import re

LANGUAGES = ('fa', 'en')
DEFAULT_LANGUAGE = 'fa'
LANGUAGE_NAMES = {'fa': 'فارسی', 'en': 'English'}

STRINGS = {
    'en': {
        'nav_scan': 'Scan',
        'nav_servers': 'Servers',
        'nav_servers_count': 'Servers ({count})',
        'nav_settings': 'Settings',
        'nav_guide': 'Guide',
        'app_name': 'ProtonVPN Scanner',

        'step_database': '1. Database',
        'btn_load': 'Load database',
        'btn_reload': 'Reload database',
        'db_none': 'No database loaded',
        'db_summary': '{count} hosts ({mode})',
        'mode_free': 'Free',
        'mode_paid': 'Premium',
        'mode_all': 'All',
        'continent_all': 'All continents',
        'country_all': 'All countries',

        'step_scan': '2. Scan',
        'vpn_warning': 'Turn your VPN OFF before scanning. Pings must be measured directly.',
        'btn_scan': 'Start scan (500)',
        'btn_next': 'Next 500',
        'btn_reset': 'Reset',
        'scan_progress': 'Scanning {total} servers…',
        'scan_none_in_scope': 'No servers match this filter.',
        'scan_end': 'Reached the end of the list.',
        'scan_found': 'Found {alive} alive. Showing the top {shown}.',
        'scan_all_dead': 'No usable reply from {total} servers (no reply, or faster than {ms} ms).',
        'scan_reset_done': 'Scanner reset. Ready to start again.',

        'load_loading': 'Loading database…',
        'load_done_cache': 'Loaded from the local cache.',
        'load_done_network': 'Downloaded a fresh database.',
        'load_done_stale': 'Network failed. Loaded an older offline copy.',
        'load_failed': 'Network error and no saved copy available.',
        'load_first': 'Load the database first.',

        'key_label': 'WireGuard private key',
        'key_hint': 'Kept only in this window. It is written only into the .conf files you save or export.',
        'provider_proton': 'Proton',
        'provider_surfshark': 'Surfshark',
        'provider_all': 'All providers',
        'surfshark_title': 'Surfshark key',
        'surfshark_label': 'Surfshark private key',
        'surfshark_hint': 'Only the private key from your Surfshark WireGuard config. It stays in this window and is not saved.',
        'surfshark_ready': 'Surfshark key is ready.',
        'surfshark_key_needed': 'Enter your Surfshark private key first.',
        'btn_export': 'Export top 15 (.conf)',
        'btn_export_untested': 'Export 15 without test (.conf)',
        'export_untested_hint': 'No check is made. The files are the current filter, in list order.',
        'settings_scan': 'Scan method',
        'scan_mode_key': 'With key (real test)',
        'scan_mode_keyless': 'No key (ping only)',
        'settings_scan_hint': 'With key, Surfshark servers are tested with a real WireGuard handshake, which needs your private key. Without a key only a ping is sent, so the result is not a WireGuard check. Proton is always a ping check.',
        'settings_threshold': 'Fake-reply threshold',
        'threshold_none': 'Off (keep every reply)',
        'settings_threshold_hint': 'Replies faster than this are treated as fake, because a local interceptor often answers instantly. Default: 10 ms.',
        'btn_fetch_ips': 'Get Surfshark IPs',
        'fetch_ips_hint': 'Turn the VPN ON, press this (once a day is enough), then turn the VPN OFF before scanning. The IPs are kept for 24 hours.',
        'fetch_ips_done': 'IPs found for {ok} of {total} hosts ({failed} failed).',
        'fetch_ips_none': 'No IP could be found. Check the VPN and your network.',
        'ip_cache_none': 'No saved Surfshark IPs yet.',
        'ip_cache_status': 'Saved IPs for {known} of {total} hosts.',
        'surfshark_no_ip_cache': 'No saved Surfshark IPs. Get them first with the VPN on, or DNS may give wrong answers under censorship.',
        'settings_ip_limit': 'IPs per Surfshark host',
        'settings_ip_limit_hint': 'Each host is tested on up to this many IPs. More IPs find more servers but take longer. Default: 4.',
        'ip_limit_option': '{n} IP',
        'btn_copy_links': 'Copy wg:// links',
        'results_header': 'Top {shown} of {total} alive',
        'results_empty': 'No results yet. Load the database and scan first.',
        'results_ready': '{alive} servers are alive. The top {shown} are ready in the Servers tab.',
        'btn_view_results': 'View results in Servers',
        'card_copy_ip': 'Copy IP',
        'card_copy_link': 'Copy link',
        'card_copy_wg': 'Copy WG',
        'card_qr': 'QR',
        'card_save': 'Save .conf',
        'copied': 'Copied.',
        'link_copied': 'Link copied for {name}.',
        'config_copied': 'Config copied.',
        'links_copied': 'Copied {count} wg:// links for {scope}.',
        'scope_all': 'all scanned servers',
        'saved_to': 'Saved to {path}',
        'exported': 'Exported {count} {kind} configs to {path}',
        'exported_hostname': 'Exported {count} {kind} configs to {path}. {hosts} use the host name because no IP was found.',
        'exported_partial': 'Exported {count} {kind} configs to {path}. {skipped} skipped (no public key, or a file with your key already exists).',
        'links_copied_partial': 'Copied {count} wg:// links for {scope}. {skipped} skipped (no public key).',
        'filter_title': 'Server type and region',
        'export_nothing': 'Nothing to export yet. Scan first.',
        'no_scope_servers': 'No scanned servers in this scope. Scan first.',

        'err_key_required': 'Enter your WireGuard private key first.',
        'err_key_invalid': 'That is not a valid WireGuard private key (44 characters, ending with =).',
        'err_awg_number': 'whole number, 0 or more',
        'err_awg_range': 'a number or a range like 1-5',
        'err_awg_order': 'Jmin must not be larger than Jmax',
        'err_qr_package': 'QR needs the qrcode package, which this build does not include.',
        'err_generic': 'Something went wrong: {error}',
        'err_no_public_key': 'This server has no WireGuard public key in the database.',
        'err_bad_public_key': 'The WireGuard public key of this server is invalid.',
        'err_bad_ip': 'The IP address of this server is invalid.',
        'err_key_file_exists': 'A config with your private key already exists in that folder, so it was not overwritten.',

        'qr_title': 'QR code · {name}',
        'qr_same_host': 'Same host, other names: {aliases}',
        'qr_mode_config': 'Config',
        'qr_mode_link': 'wg:// link',
        'qr_hint_config': 'Scan with AmneziaVPN on Android, or another app that reads WireGuard or AmneziaWG configs. The code contains your private key.',
        'qr_hint_link': 'Scan with an app that reads wg:// links, such as Shadowrocket. The code contains your private key.',
        'close': 'Close',

        'settings_language': 'Language',
        'settings_obfs': 'AmneziaWG obfuscation',
        'settings_obfs_switch': 'Enable obfuscation',
        'settings_obfs_on': 'On: configs include the AmneziaWG parameters below.',
        'settings_obfs_off': 'Off: plain WireGuard configs.',
        'settings_obfs_hint': 'These values must match the server you connect to. '
                              'The server has to support AmneziaWG too.',
        'settings_reset': 'Reset to suggested values',
        'settings_reset_done': 'Suggested values restored.',
        'about_title': 'About',
        'about_version': 'Version {version}',
        'about_disclaimer': 'Unofficial community tool. Not affiliated with Proton AG.',
        'open_telegram': 'Telegram',
        'open_x': 'X (Twitter)',
    },
    'fa': {
        'nav_scan': 'اسکن',
        'nav_servers': 'سرورها',
        'nav_servers_count': 'سرورها ({count})',
        'nav_settings': 'تنظیمات',
        'nav_guide': 'راهنما',
        'app_name': 'ProtonVPN Scanner',

        'step_database': '۱. دیتابیس',
        'btn_load': 'بارگذاری دیتابیس',
        'btn_reload': 'بارگذاری دوباره',
        'db_none': 'دیتابیسی بارگذاری نشده',
        'db_summary': '{count} میزبان ({mode})',
        'mode_free': 'رایگان',
        'mode_paid': 'پولی',
        'mode_all': 'همه',
        'continent_all': 'همه‌ی قاره‌ها',
        'country_all': 'همه‌ی کشورها',

        'step_scan': '۲. اسکن',
        'vpn_warning': 'قبل از اسکن VPN را کاملاً خاموش کنید. پینگ باید مستقیم اندازه‌گیری شود.',
        'btn_scan': 'شروع اسکن (۵۰۰)',
        'btn_next': '۵۰۰ بعدی',
        'btn_reset': 'شروع از نو',
        'scan_progress': 'در حال اسکن {total} سرور…',
        'scan_none_in_scope': 'سروری با این فیلتر پیدا نشد.',
        'scan_end': 'به انتهای فهرست رسیدیم.',
        'scan_found': '{alive} سرور فعال پیدا شد. {shown} سرور برتر نشان داده می‌شود.',
        'scan_all_dead': 'از {total} سرور پاسخ قابل‌قبولی نگرفتیم (بی‌پاسخ، یا سریع‌تر از {ms} میلی‌ثانیه).',
        'scan_reset_done': 'اسکنر ریست شد. آماده‌ی شروع دوباره است.',

        'load_loading': 'در حال بارگذاری دیتابیس…',
        'load_done_cache': 'از کش محلی بارگذاری شد.',
        'load_done_network': 'دیتابیس تازه دانلود شد.',
        'load_done_stale': 'اتصال به شبکه ناموفق بود. نسخه‌ی قدیمی آفلاین بارگذاری شد.',
        'load_failed': 'خطای شبکه و نسخه‌ی ذخیره‌شده‌ای برای استفاده وجود ندارد.',
        'load_first': 'ابتدا دیتابیس را بارگذاری کنید.',

        'key_label': 'کلید خصوصی WireGuard',
        'key_hint': 'فقط در همین پنجره نگه داشته می‌شود. فقط داخل فایل‌های .conf که ذخیره یا خروجی می‌گیرید نوشته می‌شود.',
        'provider_proton': 'Proton',
        'provider_surfshark': 'Surfshark',
        'provider_all': 'همه',
        'surfshark_title': 'کلید Surfshark',
        'surfshark_label': 'کلید خصوصی Surfshark',
        'surfshark_hint': 'فقط کلید خصوصی فایل WireGuard خودتان از Surfshark. فقط در همین پنجره می‌ماند و ذخیره نمی‌شود.',
        'surfshark_ready': 'کلید Surfshark آماده است.',
        'surfshark_key_needed': 'ابتدا کلید خصوصی Surfshark را وارد کنید.',
        'btn_export': 'خروجی ۱۵ سرور برتر (.conf)',
        'btn_export_untested': 'خروجی ۱۵ سرور بدون تست (.conf)',
        'export_untested_hint': 'هیچ تستی انجام نمی‌شود. فایل‌ها همان فیلتر فعلی‌اند، به ترتیب فهرست.',
        'settings_scan': 'روش اسکن',
        'scan_mode_key': 'با کلید (تست واقعی)',
        'scan_mode_keyless': 'بدون کلید (فقط پینگ)',
        'settings_scan_hint': 'با کلید، سرورهای Surfshark با یک Handshake واقعی WireGuard تست می‌شوند که کلید خصوصی لازم دارد. بدون کلید فقط پینگ فرستاده می‌شود و نتیجه تأیید WireGuard نیست. Proton همیشه فقط پینگ است.',
        'settings_threshold': 'آستانه‌ی پاسخ فیک',
        'threshold_none': 'خاموش (همه‌ی پاسخ‌ها نگه داشته شوند)',
        'settings_threshold_hint': 'پاسخ‌هایی که سریع‌تر از این مقدار باشند فیک حساب می‌شوند، چون یک واسطه‌ی محلی اغلب فوری جواب می‌دهد. پیش‌فرض: ۱۰ میلی‌ثانیه.',
        'btn_fetch_ips': 'گرفتن IP سرورهای Surfshark',
        'fetch_ips_hint': 'VPN را روشن کنید، این دکمه را بزنید (یک بار در روز کافی است)، سپس VPN را برای اسکن خاموش کنید. IPها ۲۴ ساعت نگه داشته می‌شوند.',
        'fetch_ips_done': 'IP برای {ok} میزبان از {total} پیدا شد ({failed} ناموفق).',
        'fetch_ips_none': 'هیچ IP پیدا نشد. VPN و شبکه را بررسی کنید.',
        'ip_cache_none': 'هنوز IP ذخیره‌شده‌ای برای Surfshark نیست.',
        'ip_cache_status': 'IP ذخیره‌شده برای {known} میزبان از {total}.',
        'surfshark_no_ip_cache': 'IP ذخیره‌شده‌ای برای Surfshark نیست. اول با VPN روشن بگیرید، وگرنه DNS در سانسور ممکن است پاسخ غلط بدهد.',
        'settings_ip_limit': 'تعداد IP برای هر میزبان Surfshark',
        'settings_ip_limit_hint': 'هر میزبان روی حداکثر این تعداد IP تست می‌شود. IP بیشتر سرور بیشتری پیدا می‌کند ولی زمان بیشتری می‌برد. پیش‌فرض: ۴.',
        'ip_limit_option': '{n} IP',
        'btn_copy_links': 'کپی لینک‌های wg://',
        'results_header': '{shown} سرور برتر از {total} سرور فعال',
        'results_empty': 'هنوز نتیجه‌ای نیست. ابتدا دیتابیس را بارگذاری و اسکن کنید.',
        'results_ready': '{alive} سرور فعال پیدا شد. {shown} سرور برتر در تب سرورها آماده است.',
        'btn_view_results': 'مشاهده نتایج در تب سرورها',
        'card_copy_ip': 'کپی IP',
        'card_copy_link': 'کپی لینک',
        'card_copy_wg': 'کپی WG',
        'card_qr': 'QR',
        'card_save': 'ذخیره .conf',
        'copied': 'کپی شد.',
        'link_copied': 'لینک {name} کپی شد.',
        'config_copied': 'کانفیگ کپی شد.',
        'links_copied': '{count} لینک wg:// برای {scope} کپی شد.',
        'scope_all': 'همه‌ی سرورهای اسکن‌شده',
        'saved_to': 'در {path} ذخیره شد',
        'exported': '{count} کانفیگ {kind} در {path} ذخیره شد',
        'exported_hostname': 'خروجی {count} کانفیگ {kind} در {path}. {hosts} کانفیگ به‌جای IP از نام میزبان استفاده می‌کند چون IP پیدا نشد.',
        'exported_partial': '{count} کانفیگ {kind} در {path} ذخیره شد. {skipped} مورد رد شد (کلید عمومی ندارد، یا فایلی با کلید شما از قبل هست).',
        'links_copied_partial': '{count} لینک wg:// برای {scope} کپی شد. {skipped} سرور رد شد (کلید عمومی ندارد).',
        'filter_title': 'نوع سرور و منطقه',
        'export_nothing': 'هنوز چیزی برای خروجی نیست. ابتدا اسکن کنید.',
        'no_scope_servers': 'در این محدوده سرور اسکن‌شده‌ای نیست. ابتدا اسکن کنید.',

        'err_key_required': 'ابتدا کلید خصوصی WireGuard را وارد کنید.',
        'err_key_invalid': 'این کلید خصوصی WireGuard معتبر نیست (۴۴ کاراکتر که با = تمام می‌شود).',
        'err_awg_number': 'عدد صحیح و صفر یا بیشتر',
        'err_awg_range': 'یک عدد یا بازه‌ای مثل 1-5',
        'err_awg_order': 'Jmin نباید از Jmax بزرگ‌تر باشد',
        'err_qr_package': 'برای QR بسته‌ی qrcode لازم است که در این نسخه نیست.',
        'err_generic': 'خطا: {error}',
        'err_no_public_key': 'این سرور کلید عمومی WireGuard در دیتابیس ندارد.',
        'err_bad_public_key': 'کلید عمومی WireGuard این سرور نامعتبر است.',
        'err_bad_ip': 'نشانی IP این سرور نامعتبر است.',
        'err_key_file_exists': 'در آن پوشه از قبل کانفیگی با کلید خصوصی شما هست، پس بازنویسی نشد.',

        'qr_title': 'کد QR · {name}',
        'qr_same_host': 'همان میزبان با نام‌های دیگر: {aliases}',
        'qr_mode_config': 'کانفیگ',
        'qr_mode_link': 'لینک wg://',
        'qr_hint_config': 'با AmneziaVPN روی اندروید، یا برنامه‌ای که کانفیگ WireGuard یا AmneziaWG را می‌خواند، اسکن کنید. این کد کلید خصوصی شما را دارد.',
        'qr_hint_link': 'با برنامه‌ای اسکن کنید که لینک wg:// را می‌خواند، مثل Shadowrocket. این کد کلید خصوصی شما را دارد.',
        'close': 'بستن',

        'settings_language': 'زبان',
        'settings_obfs': 'پنهان‌سازی AmneziaWG',
        'settings_obfs_switch': 'فعال‌سازی پنهان‌سازی',
        'settings_obfs_on': 'روشن: کانفیگ‌ها پارامترهای AmneziaWG زیر را دارند.',
        'settings_obfs_off': 'خاموش: کانفیگ WireGuard ساده.',
        'settings_obfs_hint': 'این مقادیر باید با تنظیمات سرور مقصد یکی باشند. '
                              'سرور هم باید AmneziaWG را پشتیبانی کند.',
        'settings_reset': 'بازگردانی مقادیر پیشنهادی',
        'settings_reset_done': 'مقادیر پیشنهادی برگردانده شد.',
        'about_title': 'درباره',
        'about_version': 'نسخه {version}',
        'about_disclaimer': 'ابزار غیررسمی و مستقل؛ ارتباطی با Proton AG ندارد.',
        'open_telegram': 'تلگرام',
        'open_x': 'X (توییتر)',
    },
}


def normalize_language(value):
    """زبان نامعتبر یا ناشناخته را به زبان پیش‌فرض برمی‌گرداند."""
    return value if value in LANGUAGES else DEFAULT_LANGUAGE


_ASCII_RUN = re.compile(r'[A-Za-z0-9_./:#=+\-]+(?:[ \t]+[A-Za-z0-9_./:#=+\-]+)*')


def isolate_ltr(text):
    """عبارت‌های لاتین با نقطه، دونقطه یا علامت مثل wg:// و .conf و «App Store.» را یک‌جا نگه می‌دارد.

    بدون این کار، پرانتزها و علامت‌ها داخل متن فارسی جای اشتباه می‌گیرند (مثلاً «conf.» به‌جای «.conf»
    یا «Store. App» به‌جای «App Store.»).
    """
    def wrap(match):
        run = match.group(0)
        if re.search(r'[A-Za-z0-9]', run) and re.search(r'[./:#=]', run):
            return f'\u2066{run}\u2069'
        return run
    return _ASCII_RUN.sub(wrap, text)


_PERSIAN_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def t(lang, key, **values):
    """متن کلید را در زبان داده‌شده می‌دهد؛ اگر نبود از انگلیسی استفاده می‌کند.

    در فارسی، عددهای داخل متن به رقم فارسی تبدیل می‌شوند تا کنار علامت‌های فارسی جابه‌جا نشوند.
    """
    lang = normalize_language(lang)
    table = STRINGS.get(lang, {})
    text = table.get(key) or STRINGS['en'][key]
    if lang == 'fa':  # فقط عدد‌ها؛ مسیر فایل و متن‌های دیگر دست نمی‌خورند
        values = {name: str(value).translate(_PERSIAN_DIGITS) if isinstance(value, int) and not isinstance(value, bool)
                  else value for name, value in values.items()}
    text = text.format(**values) if values else text
    return isolate_ltr(text) if lang == 'fa' else text
