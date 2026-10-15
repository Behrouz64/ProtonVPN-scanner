"""منطق بدون وابستگی به رابط گرافیکی: دریافت دیتابیس، فیلترها، پینگ و خروجی WireGuard.

این ماژول عمداً فقط از کتابخانه‌های استاندارد و requests استفاده می‌کند تا
بتوان آن را بدون رابط گرافیکی تست کرد.
"""
import ipaddress
import json
import os
import re
import socket
import time
from contextlib import closing
from urllib.parse import quote
from dataclasses import dataclass, field

import requests

import surfshark_core
import surfshark_ips

try:
    import qrcode
except ImportError:  # qrcode فقط برای نمایش QR لازم است
    qrcode = None

APP_VERSION = '1.0.3'

# لینک‌های ضد فیلتر و کمکی برای دانلود از گیت‌هاب در ایران
GITHUB_MIRRORS = [
    "https://fastly.jsdelivr.net/gh/tn3w/ProtonVPN-IPs@master/protonvpn_logicals.json",
    "https://raw.githubusercontent.com/tn3w/ProtonVPN-IPs/refs/heads/master/protonvpn_logicals.json",
    "https://gh-proxy.com/https://raw.githubusercontent.com/tn3w/ProtonVPN-IPs/refs/heads/master/protonvpn_logicals.json",
]

CACHE_FILE = "cache_github.json"
CACHE_MAX_AGE_S = 3600
DOWNLOAD_TIMEOUT_S = 10

ALL_CONTINENTS = 'All Continents'
ALL_COUNTRIES = 'All Countries'
UNKNOWN_CC = 'UNK'

BATCH_SIZE = 500
SCAN_WORKERS = 8
TOP_N = 15
# پینگ‌های زیر 10 میلی‌ثانیه رد می‌شوند
MIN_PLAUSIBLE_PING_MS = 10
# گزینه‌های آستانه‌ی پاسخ فیک در تنظیمات؛ ۰ یعنی هیچ پاسخی حذف نشود
FAKE_THRESHOLD_CHOICES = (0, 5, 10, 20, 50)
EXPORT_WG = 'wg'
EXPORT_AWG = 'awg'
EXPORT_BOTH = 'both'
EXPORT_FORMATS = (EXPORT_BOTH, EXPORT_WG, EXPORT_AWG)
BULK_COUNT_CHOICES = (5, 10, 15, 25, 50)
BULK_COUNT_DEFAULT = 15

PROTON_UDP_PROBE = b'\x38\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

# ---------- WireGuard ----------
WG_PORT = 51820
WG_ADDRESS = '10.2.0.2/32'
WG_DNS = '10.2.0.1, 2a07:b944::2:1'
WG_ALLOWED_IPS = '0.0.0.0/0, ::/0'
PRIVATE_KEY_PLACEHOLDER = '<PASTE_YOUR_PRIVATE_KEY>'
_WG_KEY_RE = re.compile(r'[A-Za-z0-9+/]{43}=')

# ---------- سرویس‌ها ----------
PROVIDER_PROTON = 'proton'
PROVIDER_SURFSHARK = 'surfshark'
# نشانه‌ی هر سرویس در نام کانفیگ‌ها: فقط ایموجی، بدون نام یا لوگوی برند
PROVIDER_MARKERS = {PROVIDER_PROTON: '🟣', PROVIDER_SURFSHARK: '🦈'}
# روش اسکن: با کلید = تست واقعی WireGuard (برای Surfshark نیاز به کلید)، بدون کلید = فقط پینگ
SCAN_WITH_KEY = 'key'
SCAN_WITHOUT_KEY = 'keyless'
SCAN_MODES = (SCAN_WITH_KEY, SCAN_WITHOUT_KEY)
SURFSHARK_CATALOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'surfshark', 'servers.json')
SURFSHARK_IPS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'surfshark', 'ips.json')
SURFSHARK_IP_CHOICES = (1, 2, 4, 8)
SURFSHARK_IP_DEFAULT = 4
SURFSHARK_IP_MAX = max(SURFSHARK_IP_CHOICES)
# آدرس و DNS پیش‌فرض تونل Surfshark؛ فقط کلید خصوصی از کاربر گرفته می‌شود
SURFSHARK_ADDRESS = '10.14.0.2/16'
SURFSHARK_DNS = '162.252.172.57, 149.154.159.92'

CC_TO_NAME = {
    'US': 'United States', 'CA': 'Canada', 'MX': 'Mexico', 'CR': 'Costa Rica', 'PA': 'Panama', 'PR': 'Puerto Rico',
    'DE': 'Germany', 'NL': 'Netherlands', 'CH': 'Switzerland', 'FR': 'France', 'UK': 'United Kingdom', 'GB': 'Great Britain',
    'SE': 'Sweden', 'IT': 'Italy', 'ES': 'Spain', 'PL': 'Poland', 'RO': 'Romania', 'IS': 'Iceland', 'DK': 'Denmark',
    'NO': 'Norway', 'FI': 'Finland', 'IE': 'Ireland', 'PT': 'Portugal', 'AT': 'Austria', 'CZ': 'Czechia', 'SK': 'Slovakia',
    'HU': 'Hungary', 'GR': 'Greece', 'BG': 'Bulgaria', 'RS': 'Serbia', 'MD': 'Moldova', 'UA': 'Ukraine', 'EE': 'Estonia',
    'LV': 'Latvia', 'LT': 'Lithuania', 'BE': 'Belgium', 'LU': 'Luxembourg', 'AL': 'Albania', 'MK': 'North Macedonia',
    'JP': 'Japan', 'SG': 'Singapore', 'HK': 'Hong Kong', 'KR': 'South Korea', 'TW': 'Taiwan', 'IL': 'Israel', 'AE': 'UAE',
    'IN': 'India', 'MY': 'Malaysia', 'VN': 'Vietnam', 'TH': 'Thailand', 'ID': 'Indonesia', 'PH': 'Philippines', 'KH': 'Cambodia',
    'MN': 'Mongolia', 'GE': 'Georgia', 'CY': 'Cyprus', 'TR': 'Turkey', 'KZ': 'Kazakhstan',
    'BR': 'Brazil', 'AR': 'Argentina', 'CO': 'Colombia', 'CL': 'Chile', 'PE': 'Peru', 'EC': 'Ecuador', 'VE': 'Venezuela',
    'UY': 'Uruguay', 'PY': 'Paraguay',
    'ZA': 'South Africa', 'EG': 'Egypt', 'NG': 'Nigeria', 'KE': 'Kenya', 'MA': 'Morocco', 'DZ': 'Algeria', 'TN': 'Tunisia',
    'AD': 'Andorra', 'AM': 'Armenia', 'AZ': 'Azerbaijan', 'BA': 'Bosnia and Herzegovina', 'BS': 'Bahamas',
    'HR': 'Croatia', 'MM': 'Myanmar', 'SI': 'Slovenia',
    'AU': 'Australia', 'NZ': 'New Zealand', 'UNK': 'Unknown'
}

CONTINENTS = {
    'North America': ['US', 'CA', 'MX', 'CR', 'PA', 'PR', 'BS'],
    'Europe': ['DE', 'NL', 'CH', 'FR', 'UK', 'GB', 'SE', 'IT', 'ES', 'PL', 'RO', 'IS', 'DK', 'NO', 'FI', 'IE', 'PT', 'AT', 'CZ', 'SK', 'HU', 'GR', 'BG', 'RS', 'MD', 'UA', 'EE', 'LV', 'LT', 'BE', 'LU', 'AL', 'MK', 'AD', 'BA', 'HR', 'SI'],
    'Asia': ['JP', 'SG', 'HK', 'KR', 'TW', 'IL', 'AE', 'IN', 'MY', 'VN', 'TH', 'ID', 'PH', 'KH', 'MN', 'GE', 'CY', 'TR', 'KZ', 'AM', 'AZ', 'MM'],
    'South America': ['BR', 'AR', 'CO', 'CL', 'PE', 'EC', 'VE', 'UY', 'PY'],
    'Africa': ['ZA', 'EG', 'NG', 'KE', 'MA', 'DZ', 'TN'],
    'Oceania': ['AU', 'NZ']
}


# ---------- دیتابیس ----------
def download_database(urls=GITHUB_MIRRORS, timeout=DOWNLOAD_TIMEOUT_S):
    """اولین آینه‌ای که پاسخ معتبر بدهد را برمی‌گرداند؛ در غیر این صورت None."""
    for url in urls:
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code != 200:
                continue
            data = resp.json()
        except (requests.RequestException, ValueError):
            continue
        servers = data.get("LogicalServers") if isinstance(data, dict) else data
        if isinstance(servers, list):
            return servers
    return None


def _cache_age(path, now):
    try:
        return now - os.path.getmtime(path)
    except OSError:
        return None


def _read_cache(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, list) else None  # کش خراب نباید وارد برنامه شود


def _write_cache(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except OSError:
        pass  # کش اختیاری است؛ نبودنش نباید برنامه را متوقف کند


def load_database(cache_path=CACHE_FILE, urls=GITHUB_MIRRORS, max_age=CACHE_MAX_AGE_S, now=None):
    """برمی‌گرداند (داده_خام, منبع). منبع: 'cache' | 'network' | 'stale-cache' | 'error'."""
    now = time.time() if now is None else now

    age = _cache_age(cache_path, now)
    if age is not None and age < max_age:
        data = _read_cache(cache_path)
        if data is not None:
            return data, 'cache'

    data = download_database(urls)
    if data is not None:
        _write_cache(cache_path, data)
        return data, 'network'

    data = _read_cache(cache_path)
    if data is not None:
        return data, 'stale-cache'
    return None, 'error'


# ---------- سرورها و فیلترها ----------
def country_code(name):
    match = re.match(r'^([A-Z]{2})', name.upper())
    return match.group(1) if match else UNKNOWN_CC


def _is_ipv4(value):
    if not isinstance(value, str):
        return False
    try:
        ipaddress.IPv4Address(value)
    except ValueError:
        return False
    return True


def extract_servers(raw_data):
    """تبدیل داده خام به لیست سرورهای فعال با IP ورودی و کلید عمومی WireGuard.

    ردیف‌هایی که نام یا IP معتبر ندارند کنار گذاشته می‌شوند تا یک ردیف خراب کل اسکن را خراب نکند.
    """
    servers = []
    for item in raw_data or []:
        if not isinstance(item, dict) or item.get('Status') != 1:
            continue
        try:
            entry = item['Servers'][0]
            ip = entry['EntryIP']
        except (KeyError, IndexError, TypeError):
            continue

        name = item.get('Name', 'Unknown')
        if not isinstance(name, str) or not _is_ipv4(ip):
            continue
        servers.append({
            'name': name,
            'ip': ip,
            'cc': country_code(name),
            'city': item.get('City', '') or '',
            'free': item.get('Tier', 0) == 0,
            'wg_key': entry.get('X25519PublicKey', '') or '',
            'port': WG_PORT,
            'provider': PROVIDER_PROTON,
        })
    return servers


def dedupe_endpoints(servers):
    """یک سرور فیزیکی ممکن است چند نام منطقی داشته باشد (مثلاً RO#1 تا RO#4) با همان IP و کلید.

    هر (IP, کلید عمومی) فقط یک بار نگه داشته می‌شود؛ نام‌های دیگر در aliases می‌آیند.
    در دیتابیس فعلی، همه‌ی IPهای تکراری کلید عمومی و سطح یکسان دارند، پس ادغام بی‌خطر است.
    """
    groups = {}
    for server in servers:
        identity = (server['ip'], server['wg_key'])
        if identity not in groups:
            groups[identity] = {**server, 'aliases': []}
        else:
            groups[identity]['aliases'].append(server['name'])
    return list(groups.values())


# ---------- حساب کاربر و فهرست Surfshark ----------
@dataclass(frozen=True)
class WgIdentity:
    """کلید خصوصی و آدرس تونل یک حساب. برای Proton فقط کلید وارد می‌شود؛ آدرس و DNS پیش‌فرض است."""
    private_key: str
    address: str = WG_ADDRESS
    dns: str = WG_DNS


_HOST_RE = re.compile(r'(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}')


def _is_hostname(value):
    return isinstance(value, str) and len(value) <= 253 and _HOST_RE.fullmatch(value) is not None


def load_surfshark_catalog(path=SURFSHARK_CATALOG_FILE):
    """فهرست سرورهای Surfshark از فایل همراه برنامه. فقط نام میزبان و کلید عمومی سرور در آن است."""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    servers = []
    for item in data.get('servers', []):
        host = item.get('hostname', '')
        key = item.get('public_key', '')
        code = item.get('country_code', '')
        if not _is_hostname(host) or not is_valid_wg_key(key) or not re.fullmatch(r'[A-Z]{2}', code):
            continue
        city = item.get('city', '') or ''
        servers.append({
            'name': f"{code}-{city}" if city else code,
            'hostname': host,
            'ip': '',
            'cc': code,
            'city': city,
            'free': False,
            'wg_key': key,
            'port': int(item.get('port') or WG_PORT),
            'provider': PROVIDER_SURFSHARK,
        })
    return servers


def surfshark_identity(private_key):
    """حساب Surfshark فقط با کلید خصوصی ساخته می‌شود؛ آدرس و DNS تونل همان مقادیر پیش‌فرض Surfshark است."""
    key = (private_key or '').strip()
    if not is_valid_wg_key(key):
        raise ConfigError('bad_private_key', 'WireGuard private key is invalid (44 base64 characters)')
    return WgIdentity(private_key=key, address=SURFSHARK_ADDRESS, dns=SURFSHARK_DNS)


def filter_by_tier(servers, mode):
    if mode == 'free':
        return [s for s in servers if s['free']]
    if mode == 'paid':
        return [s for s in servers if not s['free']]
    return list(servers)


@dataclass
class RegionIndex:
    cc_counts: dict = field(default_factory=dict)
    active_map: dict = field(default_factory=dict)
    cont_counts: dict = field(default_factory=dict)


def build_region_index(servers):
    cc_counts = {}
    for s in servers:
        cc_counts[s['cc']] = cc_counts.get(s['cc'], 0) + 1

    index = RegionIndex(cc_counts=cc_counts)
    for cont, cc_list in CONTINENTS.items():
        found = [c for c in cc_list if c in cc_counts]
        if found:
            index.active_map[cont] = found
            index.cont_counts[cont] = sum(cc_counts[c] for c in found)
    return index


def continent_choices(index):
    return sorted(index.active_map, key=lambda c: index.cont_counts.get(c, 0), reverse=True)


def country_choices(index, continent):
    if continent == ALL_CONTINENTS:
        codes = [c for c in index.cc_counts if c != UNKNOWN_CC]
    else:
        codes = index.active_map.get(continent, [])
    ordered = sorted(codes, key=lambda c: index.cc_counts.get(c, 0), reverse=True)
    return [ALL_COUNTRIES] + [label_for_cc(c) for c in ordered]


def label_for_cc(cc):
    if cc in (UNKNOWN_CC, ALL_COUNTRIES):
        return cc
    return f"{CC_TO_NAME.get(cc, cc)} ({cc})"


def cc_from_label(label):
    if label in (ALL_COUNTRIES, UNKNOWN_CC):
        return label
    match = re.search(r'\(([A-Z]{2})\)$', label)
    return match.group(1) if match else label


def filter_servers(servers, continent, country, active_map):
    """continent و country همان مقادیر نمایشی اسپینرها هستند (country کد کشور یا ALL_COUNTRIES)."""
    result = []
    for s in servers:
        if continent != ALL_CONTINENTS and s['cc'] not in active_map.get(continent, []):
            continue
        if country != ALL_COUNTRIES and s['cc'] != country:
            continue
        result.append(s)
    return result


# ---------- پینگ ----------
def _tcp_rtt(ip, timeout):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.settimeout(timeout)
        start = time.monotonic()
        if s.connect_ex((ip, 443)) == 0:
            return int((time.monotonic() - start) * 1000)
    return None


def _udp_rtt(ip, timeout):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
        s.settimeout(timeout)
        start = time.monotonic()
        try:
            s.sendto(PROTON_UDP_PROBE, (ip, 80))
            s.recvfrom(1024)
        except OSError:
            return None
        return int((time.monotonic() - start) * 1000)


def smart_ping(ip, timeout=1.5):
    """بهترین پینگ از بین TCP:443 و UDP:80 را برمی‌گرداند؛ (ms, proto) یا (None, None)."""
    candidates = []
    try:
        tcp = _tcp_rtt(ip, timeout)
        if tcp is not None:
            candidates.append((tcp, 'TCP:443'))
    except OSError:
        pass
    try:
        udp = _udp_rtt(ip, timeout)
        if udp is not None:
            candidates.append((udp, 'UDP:80'))
    except OSError:
        pass

    if not candidates:
        return None, None
    return min(candidates)


def probe_server(server, private_key='', mode=SCAN_WITH_KEY):
    """(ms, برچسب) برای یک سرور؛ server['ip'] باید IPv4 باشد.

    با کلید: Handshake واقعی WireGuard با کلید حساب کاربر و کلید عمومی همان سرور، برای Proton و Surfshark.
    بدون کلید: فقط پینگ TCP/UDP؛ این نتیجه تأیید WireGuard نیست.
    """
    if mode == SCAN_WITHOUT_KEY:
        return smart_ping(server['ip'])
    return surfshark_core.handshake_rtt(server['ip'], server.get('wg_key', ''), private_key,
                                        port=server.get('port', WG_PORT))


def resolve_ipv4(host, limit=SURFSHARK_IP_DEFAULT):
    """حداکثر limit نشانی IPv4 یکتای نام میزبان (مثل dig A). خطای DNS یعنی فهرست خالی."""
    try:
        infos = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
    except OSError:
        return []
    ips = []
    for info in infos:
        ip = info[4][0]
        if ip not in ips and surfshark_ips.is_public_ipv4(ip):
            ips.append(ip)
    return ips[:limit]


def scan_server(server, private_key='', mode=SCAN_WITH_KEY, threshold=MIN_PLAUSIBLE_PING_MS, ips_for=None):
    """بهترین سرور پاسخ‌دهنده یا None.

    Surfshark فقط نام میزبان دارد: نشانی‌های IPv4 آن حل می‌شود و هر IP جداگانه سنجیده می‌شود.
    Proton همان IP خودش را دارد. خروجی همان سرور با IP پاسخ‌دهنده، ping و proto است.
    """
    if server.get('provider') == PROVIDER_SURFSHARK:
        ips = ips_for(server['hostname']) if ips_for else resolve_ipv4(server['hostname'])
    else:
        ips = [server['ip']]
    best = None
    for ip in ips:
        candidate = {**server, 'ip': ip}
        ping, proto = probe_server(candidate, private_key, mode)
        if is_usable_reply(ping, threshold) and (best is None or ping < best[0]):
            best = (ping, proto, candidate)
    if best is None:
        return None
    ping, proto, candidate = best
    return {**candidate, 'ping': ping, 'proto': proto}


def config_ready(servers, ips_for=None):
    """(سرورهای آماده‌ی کانفیگ، نام سرورهایی که به‌جای IP نام میزبان گرفتند).

    Surfshark اگر IP عمومی پیدا نشود، با نام میزبان نوشته می‌شود؛ کلاینت WireGuard خودش نام را حل می‌کند.
    """
    ready, by_name = [], []
    for server in servers:
        if server.get('provider') != PROVIDER_SURFSHARK or _is_ipv4(server.get('ip', '')):
            ready.append(server)
            continue
        ips = ips_for(server['hostname']) if ips_for else resolve_ipv4(server['hostname'], limit=1)
        if ips:
            ready.append({**server, 'ip': ips[0]})
        else:
            ready.append({**server, 'ip': server['hostname']})
            by_name.append(server['name'])
    return ready, by_name


def is_usable_reply(ping, threshold):
    """پاسخی معتبر است که وجود داشته باشد و کمتر از آستانه‌ی پاسخ فیک نباشد."""
    return ping is not None and ping >= threshold


# ---------- نتایج ----------
def merge_results(existing, new):
    """نتایج را بر اساس میزبان (IP + کلید) یکتا می‌کند؛ مقدار جدیدتر جایگزین می‌شود."""
    merged = {(s['ip'], s['wg_key']): s for s in existing}
    merged.update({(s['ip'], s['wg_key']): s for s in new})
    return list(merged.values())


def top_results(servers, limit=TOP_N):
    return sorted(servers, key=lambda s: s['ping'])[:limit]


BROWSE_PAGE = 40
STATE_ALIVE = 'alive'
STATE_NO_REPLY = 'no_reply'
STATE_UNTESTED = 'untested'


def endpoint_id(server):
    """شناسه‌ی ثابت یک سرور برای تشخیص تست‌شده بودن.

    IP سرورهای Surfshark قبل از اسکن خالی است، پس نام میزبان (یا IP برای Proton) مبنا قرار می‌گیرد.
    """
    return (server.get('provider', PROVIDER_PROTON), server.get('hostname') or server.get('ip', ''),
            server.get('wg_key', ''))


def browse_order(scope, alive, tested_ids):
    """[(وضعیت، سرور)] به ترتیب: پاسخ‌دهنده‌ها بر اساس پینگ، سپس تست‌شده‌های بی‌پاسخ، سپس تست‌نشده‌ها.

    ترتیب فهرست در هر گروه حفظ می‌شود.
    """
    alive_by_id = {endpoint_id(s): s for s in alive}
    rows = []
    for server in scope:
        ident = endpoint_id(server)
        if ident in alive_by_id:
            hit = alive_by_id[ident]
            rows.append((0, hit['ping'], STATE_ALIVE, hit))
        elif ident in tested_ids:
            rows.append((1, 0, STATE_NO_REPLY, server))
        else:
            rows.append((2, 0, STATE_UNTESTED, server))
    rows.sort(key=lambda row: (row[0], row[1]))
    return [(state, server) for _, _, state, server in rows]


# ---------- WireGuard ----------
def is_valid_wg_key(key):
    return bool(key) and _WG_KEY_RE.fullmatch(key) is not None


# ---------- AmneziaWG (پنهان‌سازی ترافیک) ----------
# این پارامترها باید دقیقاً با سروری که به آن وصل می‌شوید یکی باشند؛
# سرور باید AmneziaWG را پشتیبانی کند، وگرنه handshake برقرار نمی‌شود.
AWG_KEYS = ('Jc', 'Jmin', 'Jmax', 'S1', 'S2', 'H1', 'H2', 'H3', 'H4')
# مقادیر پیش‌فرض از یک کانفیگ AmneziaWG کارکرده. H1-H4 همان نوع پیام‌های استاندارد
# WireGuard هستند و S1/S2 صفر است؛ پس تفاوت اصلی با WireGuard ساده، بسته‌های junk (Jc) است.
DEFAULT_OBFUSCATION = {'Jc': 4, 'Jmin': 50, 'Jmax': 1000, 'S1': 0, 'S2': 0,
                       'H1': 1, 'H2': 2, 'H3': 3, 'H4': 4}


AWG_H_KEYS = ('H1', 'H2', 'H3', 'H4')
AWG_UINT32_MAX = 2 ** 32 - 1
_AWG_UINT_RE = re.compile(r'\d{1,9}')  # حد طول، هم از تبدیل عدد خیلی بزرگ جلوگیری می‌کند هم از پیام خطای کتابخانه
_AWG_H_RE = re.compile(r'(\d{1,10})(?:-(\d{1,10}))?')
PERSISTENT_KEEPALIVE = 25


class ConfigError(ValueError):
    """خطای سرور یا کلید. code ثابت است و UI متن زبان کاربر را از روی آن می‌سازد."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def check_obfuscation(values):
    """پارامترهای AmneziaWG را از فرم تنظیمات بررسی می‌کند.

    values نگاشتی از نام پارامتر به عدد یا رشته است. برمی‌گرداند (params, errors):
    params مقادیر نرمال‌شده‌ی همه‌ی AWG_KEYS است و فقط وقتی معتبر است که errors خالی باشد.
    errors نگاشت نام پارامتر به یکی از کدهای زیر است:
      'number'  عدد صحیح و غیرمنفی نیست
      'range'   مقدار H عدد یا بازه‌ی «a-b» نیست یا خارج از محدوده است
      'order'   Jmin از Jmax بزرگ‌تر است
    """
    params, errors = {}, {}
    for key in AWG_KEYS:
        raw = str(values.get(key, '')).strip()
        if key in AWG_H_KEYS:
            match = _AWG_H_RE.fullmatch(raw)
            low = int(match.group(1)) if match else 0
            high = int(match.group(2)) if match and match.group(2) else low
            if not match or low > high or high > AWG_UINT32_MAX:
                errors[key] = 'range'
            else:
                params[key] = f'{low}-{high}' if match.group(2) else str(low)
        elif _AWG_UINT_RE.fullmatch(raw):
            params[key] = int(raw)
        else:
            errors[key] = 'number'
    if not errors and params['Jmin'] > params['Jmax']:
        errors['Jmin'] = 'order'
    return params, errors


def build_wireguard_config(server, private_key='', address=WG_ADDRESS, dns=WG_DNS, obfuscation=None):
    """ساخت متن فایل .conf برای یک سرور.

    کلید خصوصی به حساب Proton وابسته است و از دیتابیس عمومی به دست نمی‌آید؛
    اگر ورودی داده نشود، جای آن placeholder قرار می‌گیرد.
    obfuscation (خروجی check_obfuscation) اگر داده شود، پارامترهای AmneziaWG به [Interface] اضافه می‌شود.
    """
    public_key = server.get('wg_key', '')
    if not public_key:
        raise ConfigError('no_public_key', f"{server['name']}: no WireGuard public key in the database")
    if not is_valid_wg_key(public_key):
        raise ConfigError('bad_public_key', f"{server['name']}: WireGuard public key is invalid")
    _check_server_host(server)
    if private_key and not is_valid_wg_key(private_key):
        raise ConfigError('bad_private_key', 'WireGuard private key is invalid (44 base64 characters)')

    interface = [
        '[Interface]',
        f'PrivateKey = {private_key or PRIVATE_KEY_PLACEHOLDER}',
        f'Address = {address}',
        f'DNS = {dns}',
    ]
    if obfuscation:
        interface += [f'{key} = {obfuscation[key]}' for key in AWG_KEYS]

    lines = interface + [
        '',
        '[Peer]',
        f'PublicKey = {public_key}',
        f'AllowedIPs = {WG_ALLOWED_IPS}',
        f'Endpoint = {server["ip"]}:{server.get("port", WG_PORT)}',
        f'PersistentKeepalive = {PERSISTENT_KEEPALIVE}',
        '',
    ]
    return '\n'.join(lines)


def _check_server_host(server):
    """IPv4 برای Proton و نام میزبان برای Surfshark (در Endpoint همان مقدار استفاده می‌شود)."""
    valid = _is_ipv4(server['ip']) or (server.get('provider') == PROVIDER_SURFSHARK and _is_hostname(server['ip']))
    if not valid:
        raise ConfigError('bad_ip', f"{server['name']}: server address is invalid")


def config_file_stem(server, suffix=''):
    """نام فایل کانفیگ: پیشوند سرویس به نام اضافه می‌شود تا کانفیگ‌های دو سرویس با هم قاطی نشوند."""
    provider = server.get('provider', PROVIDER_PROTON)
    return f"{provider}_{safe_filename(server['name'])}{suffix}"


def safe_filename(name):
    return re.sub(r'[^A-Za-z0-9_-]+', '_', name).strip('_') or 'server'


PRIVATE_FILE_MODE = 0o600
PRIVATE_DIR_MODE = 0o700


def _holds_private_key(path):
    """True اگر فایل از قبل کلید خصوصی واقعی داشته باشد (نه جای‌نگهدار)."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        return False
    match = re.search(r'^PrivateKey = (.+)$', text, re.MULTILINE)
    return bool(match) and match.group(1).strip() != PRIVATE_KEY_PLACEHOLDER


def _write_private_file(path, text):
    """فایل را فقط برای صاحب حساب قابل خواندن می‌نویسد، چون کلید خصوصی داخل آن است."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, PRIVATE_FILE_MODE)
    with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    os.chmod(path, PRIVATE_FILE_MODE)  # اگر فایل از قبل با مجوز بازتر ساخته شده بود، اصلاح می‌شود


def write_wireguard_config(server, directory, private_key='', obfuscation=None,
                           address=WG_ADDRESS, dns=WG_DNS):
    os.makedirs(directory, mode=PRIVATE_DIR_MODE, exist_ok=True)
    os.chmod(directory, PRIVATE_DIR_MODE)
    conf = build_wireguard_config(server, private_key, address=address, dns=dns, obfuscation=obfuscation)
    path = os.path.join(directory, config_file_stem(server, '_awg' if obfuscation else '') + '.conf')
    # بدون کلید، فایل جای‌نگهدار می‌گیرد؛ اگر نسخه‌ی کلیددار از قبل هست، آن را پاک نمی‌کنیم
    if not private_key and _holds_private_key(path):
        raise ConfigError('key_file_exists',
                          f"{server['name']}: a config with a private key already exists and was not overwritten")
    _write_private_file(path, conf)
    return path


def export_wireguard_configs(servers, directory, private_key='', obfuscation=None,
                             address=WG_ADDRESS, dns=WG_DNS):
    """برمی‌گرداند (مسیرهای نوشته‌شده, نام سرورهای رد‌شده)."""
    written, skipped = [], []
    for server in servers:
        try:
            written.append(write_wireguard_config(server, directory, private_key, obfuscation,
                                                  address=address, dns=dns))
        except ValueError:
            skipped.append(server['name'])
    return written, skipped


# ---------- لینک wg:// و QR ----------
# فرمت لینک مثل کلاینت‌هایی مثل Shadowrocket: host:port و پارامترها در query، نام در fragment.
# کلیدهای عمومی و خصوصی با / و = داخل لینک دست نخورده می‌مانند؛ بقیه‌ی کاراکترها escape می‌شوند.
WG_LINK_PREFIX = 'wg://'
WG_LINK_MTU = 1280
WG_LINK_ADDRESS = WG_ADDRESS.split('/')[0]


def country_flag(cc):
    code = 'GB' if cc == 'UK' else cc
    if len(code) != 2 or not code.isalpha():
        return ''
    return ''.join(chr(0x1F1E6 + ord(letter) - ord('A')) for letter in code.upper())


def server_label(server):
    """نام نمایشی لینک: نشانه‌ی سرویس، پرچم و مکان، مثل: 🦈 🇩🇪 Germany — Berlin (de-ber.prod.surfshark.com)"""
    marker = PROVIDER_MARKERS.get(server.get('provider', PROVIDER_PROTON), '')
    country = CC_TO_NAME.get(server['cc'], server['cc'])
    place = f"{country} — {server['city']}" if server.get('city') else country
    return f"{marker} {country_flag(server['cc'])} {place} ({server['ip']})".strip()


def build_wg_link(server, private_key, obfuscation=None, address=WG_ADDRESS, dns=WG_DNS):
    """لینک wg:// یک سرور. obfuscation (خروجی check_obfuscation) اگر باشد، AmneziaWG هم اضافه می‌شود."""
    if not is_valid_wg_key(private_key):
        raise ConfigError('bad_private_key', 'WireGuard private key is invalid')
    public_key = server.get('wg_key', '')
    if not is_valid_wg_key(public_key):
        raise ConfigError('bad_public_key', f"{server['name']}: WireGuard public key is missing or invalid")
    _check_server_host(server)

    params = [
        ('publicKey', public_key),
        ('privateKey', private_key),
        ('ip', address.split('/')[0]),
        ('dns', dns),
        ('mtu', WG_LINK_MTU),
        ('udp', 1),
        ('keepalive', PERSISTENT_KEEPALIVE),
    ]
    if obfuscation:
        values = {key.lower(): str(obfuscation[key]) for key in AWG_KEYS}
        params += [('obfs', 'amneziawg'), ('obfsParam', json.dumps(values, separators=(',', ':')))]

    query = '&'.join(f"{key}={quote(str(value), safe='/')}" for key, value in params)
    return (f"{WG_LINK_PREFIX}{server['ip']}:{server.get('port', WG_PORT)}?{query}"
            f"#{quote(server_label(server), safe='')}")


def qr_available():
    return qrcode is not None


def qr_cells(matrix, side):
    """مربع‌های تیره‌ی QR روی بوم مربعی به ضلع side پیکسل.

    برمی‌گرداند (cell, rects) که rects فهرستی از (x, y, cell) با مختصات بالا-چپ است.
    اندازه‌ی مربع‌ها عدد صحیح است تا لبه‌ها تار نشوند و دوربین بهتر بخواند؛ شکل وسط بوم می‌نشیند.
    """
    modules = len(matrix)
    cell = max(1, side // modules)
    offset = (side - cell * modules) // 2
    rects = [(offset + col * cell, offset + row * cell, cell)
             for row, cells in enumerate(matrix) for col, dark in enumerate(cells) if dark]
    return cell, rects


def qr_matrix(text):
    """ماتریس بولی QR (True = مربع تیره) شامل حاشیه‌ی سفید؛ برای رسم در رابط گرافیکی."""
    if qrcode is None:
        raise RuntimeError('qrcode package is not installed')
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
    qr.add_data(text)
    qr.make(fit=True)
    return qr.get_matrix()
