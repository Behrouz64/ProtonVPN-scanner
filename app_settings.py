"""تنظیمات برنامه: زبان، پنهان‌سازی AmneziaWG، روش اسکن و آستانه‌ی پاسخ فیک.

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
        'obfuscation_enabled': True,
        'obfuscation': dict(core.DEFAULT_OBFUSCATION),
        'scan_mode': core.SCAN_WITH_KEY,
        'fake_threshold_ms': core.MIN_PLAUSIBLE_PING_MS,
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
    if isinstance(data.get('obfuscation_enabled'), bool):
        settings['obfuscation_enabled'] = data['obfuscation_enabled']
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
    return settings


def dump_settings(settings):
    payload = {
        'version': SETTINGS_VERSION,
        'language': i18n.normalize_language(settings['language']),
        'obfuscation_enabled': bool(settings['obfuscation_enabled']),
        'obfuscation': settings['obfuscation'],
        'scan_mode': settings.get('scan_mode', core.SCAN_WITH_KEY),
        'fake_threshold_ms': settings.get('fake_threshold_ms', core.MIN_PLAUSIBLE_PING_MS),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def reset_obfuscation(settings):
    """پارامترهای AmneziaWG را به مقادیر پیشنهادی برمی‌گرداند؛ زبان و روشن/خاموش بودن دست نمی‌خورد."""
    return {**settings, 'obfuscation': dict(core.DEFAULT_OBFUSCATION)}


def obfuscation_for_build(settings):
    """پارامترهایی که باید به کانفیگ اضافه شوند، یا None برای WireGuard ساده."""
    if not settings['obfuscation_enabled']:
        return None
    params, errors = core.check_obfuscation(settings['obfuscation'])
    if errors:
        raise ValueError('obfuscation settings are invalid')
    return params
