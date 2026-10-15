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


def _valid_ips(values):
    """فقط IPv4 معتبر، بدون تکرار و با حفظ ترتیب."""
    ips = []
    for value in values:
        if not isinstance(value, str):
            continue
        try:
            ip = str(ipaddress.IPv4Address(value))
        except ValueError:
            continue
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
    def ips_for(host):
        ips = fresh_ips(cache, host, now) or _valid_ips(bundled.get(host, []))
        if not ips:
            ips = _valid_ips(resolver(host, limit))
        return ips[:limit]
    return ips_for
