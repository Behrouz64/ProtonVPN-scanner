"""تنظیمات برنامه: زبان، قالب کانفیگ‌ها، پارامترهای AmneziaWG، روش اسکن و آستانه‌ی پاسخ فیک.

فقط منطق خالص است و به رابط گرافیکی وابسته نیست؛ ذخیره‌سازی واقعی در main.py انجام می‌شود.
کلید خصوصی WireGuard عمداً در تنظیمات نیست و هیچ‌وقت ذخیره نمی‌شود.
"""
import json

import i18n
import scanner_core as core

SETTINGS_VERSION = 1


def default_settings():
    return {
        'language': i18n.DEFAULT_LANGUAGE,
        'export_formats': core.EXPORT_BOTH,
        'obfuscation': dict(core.DEFAULT_OBFUSCATION),
        'scan_mode': core.SCAN_WITH_KEY,
        'fake_threshold_ms': core.MIN_PLAUSIBLE_PING_MS,
        'surfshark_ip_limit': core.SURFSHARK_IP_DEFAULT,
        'bulk_count': core.BULK_COUNT_DEFAULT,
    }


def load_settings(text):
    """متن JSON ذخیره‌شده را می‌خواند. هر بخش نامعتبر به مقدار پیش‌فرض برمی‌گردد."""
    settings = default_settings()
    try:
        data = json.loads(text) if text else {}
    except (TypeError, ValueError):
        return settings
    if not isinstance(data, dict):
        return settings

    settings['language'] = i18n.normalize_language(data.get('language'))
    if data.get('export_formats') in core.EXPORT_FORMATS:
        settings['export_formats'] = data['export_formats']
    elif isinstance(data.get('obfuscation_enabled'), bool):
        # نسخه‌ی قبلی فقط یک کلید روشن/خاموش داشت: روشن یعنی هر دو قالب، خاموش یعنی WireGuard استاندارد
        settings['export_formats'] = core.EXPORT_BOTH if data['obfuscation_enabled'] else core.EXPORT_WG
    raw = data.get('obfuscation')
    if isinstance(raw, dict):
        params, errors = core.check_obfuscation(raw)
        if not errors:
            settings['obfuscation'] = params
    if data.get('scan_mode') in core.SCAN_MODES:
        settings['scan_mode'] = data['scan_mode']
    threshold = data.get('fake_threshold_ms')
    if isinstance(threshold, int) and not isinstance(threshold, bool) and threshold in core.FAKE_THRESHOLD_CHOICES:
        settings['fake_threshold_ms'] = threshold
    ip_limit = data.get('surfshark_ip_limit')
    if isinstance(ip_limit, int) and not isinstance(ip_limit, bool) and ip_limit in core.SURFSHARK_IP_CHOICES:
        settings['surfshark_ip_limit'] = ip_limit
    # نام قبلی این تنظیم untested_export_count بود؛ مقدار ذخیره‌شده‌ی آن هم خوانده می‌شود
    count = data.get('bulk_count', data.get('untested_export_count'))
    if isinstance(count, int) and not isinstance(count, bool) and count in core.BULK_COUNT_CHOICES:
        settings['bulk_count'] = count
    return settings


def dump_settings(settings):
    payload = {
        'version': SETTINGS_VERSION,
        'language': i18n.normalize_language(settings['language']),
        'export_formats': settings.get('export_formats', core.EXPORT_BOTH),
        'obfuscation': settings['obfuscation'],
        'scan_mode': settings.get('scan_mode', core.SCAN_WITH_KEY),
        'fake_threshold_ms': settings.get('fake_threshold_ms', core.MIN_PLAUSIBLE_PING_MS),
        'surfshark_ip_limit': settings.get('surfshark_ip_limit', core.SURFSHARK_IP_DEFAULT),
        'bulk_count': settings.get('bulk_count', core.BULK_COUNT_DEFAULT),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def reset_obfuscation(settings):
    """پارامترهای AmneziaWG را به مقادیر پیشنهادی برمی‌گرداند؛ زبان و روشن/خاموش بودن دست نمی‌خورد."""
    return {**settings, 'obfuscation': dict(core.DEFAULT_OBFUSCATION)}


def awg_params(settings):
    """پارامترهای AmneziaWG معتبر از تنظیمات؛ خطا اگر مقدارها نامعتبر باشند."""
    params, errors = core.check_obfuscation(settings['obfuscation'])
    if errors:
        raise ValueError('obfuscation settings are invalid')
    return params


def card_obfuscation(settings):
    """پارامترهای AmneziaWG برای کارت‌های سرور (کپی، QR، ذخیره‌ی تکی) و لینک wg://.

    فقط در حالت AmneziaWG مقدار دارد؛ در بقیه‌ی حالت‌ها WireGuard استاندارد است.
    """
    if settings.get('export_formats') != core.EXPORT_AWG:
        return None
    return awg_params(settings)


def export_obfuscations(settings):
    """برای هر فایل خروجی یک مدخل: None یعنی WireGuard استاندارد، دیکشنری یعنی AmneziaWG."""
    formats = settings.get('export_formats', core.EXPORT_BOTH)
    plain = [None] if formats in (core.EXPORT_WG, core.EXPORT_BOTH) else []
    awg = [awg_params(settings)] if formats in (core.EXPORT_AWG, core.EXPORT_BOTH) else []
    return plain + awg
