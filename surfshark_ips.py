"""نشانی IPv4 میزبان‌های Surfshark: کش محلی، فهرست همراه برنامه و ترتیب انتخاب.

ترتیب انتخاب برای هر میزبان: کش تازه (تا CACHE_TTL_S)، سپس فهرست همراه برنامه، و در آخر DNS زنده.
DNS زنده در شبکه‌ی سانسورشده ممکن است پاسخ جعلی بدهد؛ به همین دلیل کش را با VPN روشن می‌سازند.
این ماژول فقط کتابخانه‌ی استاندارد را استفاده می‌کند و به رابط گرافیکی وابسته نیست.
"""
import ipaddress
import json
import os

CACHE_TTL_S = 24 * 3600
CACHE_FILE = 'surfshark_ips.json'
CACHE_VERSION = 1


def is_public_ipv4(value):
    """IPv4 عمومی است. نشانی‌های خصوصی، لوپ‌بک و بازه‌های ساختگی (مثل پاسخ sinkhole فیلترینگ) رد می‌شوند."""
    if not isinstance(value, str):
        return False
    try:
        return ipaddress.IPv4Address(value).is_global
    except ValueError:
        return False


def _valid_ips(values):
    """فقط IPv4 عمومی، بدون تکرار و با حفظ ترتیب."""
    ips = []
    for value in values:
        if not is_public_ipv4(value):
            continue
        ip = str(ipaddress.IPv4Address(value))
        if ip not in ips:
            ips.append(ip)
    return ips


def _read_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def load_cache(path):
    """{میزبان: {'ips': [...], 'at': ثانیه}}؛ فایل نبودن یا خراب بودنش یعنی کش خالی."""
    data = _read_json(path)
    hosts = data.get('hosts') if isinstance(data, dict) else None
    if not isinstance(hosts, dict):
        return {}
    cache = {}
    for host, entry in hosts.items():
        if not isinstance(entry, dict):
            continue
        at = entry.get('at')
        if isinstance(at, bool) or not isinstance(at, (int, float)):
            continue
        cache[host] = {'ips': _valid_ips(entry.get('ips') or []), 'at': at}
    return cache


def save_cache(path, entries):
    """فایل کش را اتمیک جایگزین می‌کند. کلید یا اطلاعات حساب در آن نوشته نمی‌شود."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump({'version': CACHE_VERSION, 'hosts': entries}, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def load_bundled(path):
    """فهرست IP همراه برنامه: {میزبان: [ip, ...]}؛ نبودن فایل یعنی فهرست خالی."""
    data = _read_json(path)
    hosts = data.get('hosts') if isinstance(data, dict) else None
    if not isinstance(hosts, dict):
        return {}
    return {host: _valid_ips(ips) for host, ips in hosts.items() if isinstance(ips, list)}


def fresh_ips(cache, host, now, ttl=CACHE_TTL_S):
    """IPهای کش برای میزبان اگر هنوز تازه باشند؛ وگرنه فهرست خالی."""
    entry = cache.get(host)
    if not entry or not 0 <= now - entry['at'] <= ttl:
        return []
    return _valid_ips(entry['ips'])


def refresh(hosts, resolver, now, limit):
    """DNS همه‌ی میزبان‌ها را حل می‌کند. برمی‌گرداند (ورودی‌های تازه، میزبان‌های بی‌پاسخ)."""
    fresh, failed = {}, []
    for host in hosts:
        ips = _valid_ips(resolver(host, limit))
        if ips:
            fresh[host] = {'ips': ips, 'at': now}
        else:
            failed.append(host)
    return fresh, failed


def merge_cache(old, fresh):
    """ورودی‌های تازه جای قدیمی‌ها را می‌گیرند؛ میزبان بی‌پاسخ همان ورودی قبلی را نگه می‌دارد."""
    return {**old, **fresh}


def ip_source(cache, bundled, resolver, now, limit):
    """تابع host -> فهرست IP برای اسکن و کانفیگ: کش تازه، سپس فهرست همراه، سپس DNS زنده."""
    # کش یا فهرست همراه و DNS زنده، هر دو نامزدند؛ کش آلوده نباید پاسخ سالم DNS را پنهان کند
    def ips_for(host):
        stored = (fresh_ips(cache, host, now) or _valid_ips(bundled.get(host, [])))[:limit]
        live = _valid_ips(resolver(host, limit))[:limit]
        return list(dict.fromkeys(stored + live))
    return ips_for
