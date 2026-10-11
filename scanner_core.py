"""منطق بدون وابستگی به Kivy: دریافت دیتابیس، فیلترها، پینگ و خروجی WireGuard.

این ماژول عمداً فقط از کتابخانه‌های استاندارد و requests استفاده می‌کند تا
بتوان آن را بدون رابط گرافیکی تست کرد.
"""
import base64
import hashlib
import hmac
import ipaddress
import json
import os
import re
import socket
import struct
import time
from contextlib import closing
from dataclasses import dataclass, field

import requests

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
except ImportError:  # cryptography فقط برای بررسی handshake لازم است
    serialization = X25519PrivateKey = X25519PublicKey = ChaCha20Poly1305 = None

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
# 🎯 پینگ‌های زیر 100 میلی‌ثانیه تقلبی در نظر گرفته می‌شوند
MIN_PLAUSIBLE_PING_MS = 100

PROTON_UDP_PROBE = b'\x38\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

# ---------- WireGuard ----------
WG_PORT = 51820
WG_ADDRESS = '10.2.0.2/32'
WG_DNS = '10.2.0.1'
WG_ALLOWED_IPS = '0.0.0.0/0, ::/0'
PRIVATE_KEY_PLACEHOLDER = '<PASTE_YOUR_PRIVATE_KEY>'
_WG_KEY_RE = re.compile(r'[A-Za-z0-9+/]{43}=')

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
    'AU': 'Australia', 'NZ': 'New Zealand', 'UNK': 'Unknown'
}

CONTINENTS = {
    'North America': ['US', 'CA', 'MX', 'CR', 'PA', 'PR'],
    'Europe': ['DE', 'NL', 'CH', 'FR', 'UK', 'GB', 'SE', 'IT', 'ES', 'PL', 'RO', 'IS', 'DK', 'NO', 'FI', 'IE', 'PT', 'AT', 'CZ', 'SK', 'HU', 'GR', 'BG', 'RS', 'MD', 'UA', 'EE', 'LV', 'LT', 'BE', 'LU', 'AL', 'MK'],
    'Asia': ['JP', 'SG', 'HK', 'KR', 'TW', 'IL', 'AE', 'IN', 'MY', 'VN', 'TH', 'ID', 'PH', 'KH', 'MN', 'GE', 'CY', 'TR', 'KZ'],
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
        return data.get("LogicalServers", data) if isinstance(data, dict) else data
    return None


def _cache_age(path, now):
    try:
        return now - os.path.getmtime(path)
    except OSError:
        return None


def _read_cache(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


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


def extract_servers(raw_data):
    """تبدیل داده خام به لیست سرورهای فعال با IP ورودی و کلید عمومی WireGuard."""
    servers = []
    for item in raw_data or []:
        if item.get('Status') != 1:
            continue
        try:
            entry = item['Servers'][0]
            ip = entry['EntryIP']
        except (KeyError, IndexError, TypeError):
            continue

        name = item.get('Name', 'Unknown')
        servers.append({
            'name': name,
            'ip': ip,
            'cc': country_code(name),
            'free': item.get('Tier', 0) == 0,
            'wg_key': entry.get('X25519PublicKey', '') or '',
        })
    return servers


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


# ---------- نتایج ----------
def merge_results(existing, new):
    """نتایج را بر اساس نام یکتا می‌کند؛ مقدار جدیدتر جایگزین می‌شود."""
    merged = {s['name']: s for s in existing}
    merged.update({s['name']: s for s in new})
    return list(merged.values())


def top_results(servers, limit=TOP_N):
    return sorted(servers, key=lambda s: s['ping'])[:limit]


# ---------- WireGuard ----------
def is_valid_wg_key(key):
    return bool(key) and _WG_KEY_RE.fullmatch(key) is not None


# ---------- AmneziaWG (پنهان‌سازی ترافیک) ----------
# این پارامترها باید دقیقاً با سروری که به آن وصل می‌شوید یکی باشند؛
# سرور باید AmneziaWG را پشتیبانی کند، وگرنه handshake برقرار نمی‌شود.
AWG_KEYS = ('Jc', 'Jmin', 'Jmax', 'S1', 'S2', 'H1', 'H2', 'H3', 'H4')
AWG_REQUIRED_KEYS = ('Jc', 'Jmin', 'Jmax', 'H1', 'H2', 'H3', 'H4')
AWG_DEFAULTS = {'S1': 0, 'S2': 0}
# مقادیر پیش‌فرض از یک کانفیگ AmneziaWG کارکرده. H1-H4 همان نوع پیام‌های استاندارد
# WireGuard هستند و S1/S2 صفر است؛ پس تفاوت اصلی با WireGuard ساده، بسته‌های junk (Jc) است.
DEFAULT_OBFUSCATION = {'Jc': 4, 'Jmin': 50, 'Jmax': 1000, 'S1': 0, 'S2': 0,
                       'H1': 1, 'H2': 2, 'H3': 3, 'H4': 4}


def format_obfuscation(params):
    """متن قابل چسباندن برای کادر پارامترهای AmneziaWG (خروجی parse_obfuscation را برمی‌گرداند)."""
    return '\n'.join(f'{key} = {params[key]}' for key in AWG_KEYS)
AWG_H_KEYS = ('H1', 'H2', 'H3', 'H4')
AWG_UINT32_MAX = 2 ** 32 - 1
_AWG_UINT_RE = re.compile(r'\d+')
_AWG_H_RE = re.compile(r'(\d+)(?:-(\d+))?')
PERSISTENT_KEEPALIVE = 25


def _parse_obfuscation_value(key, value, lineno):
    if key in AWG_H_KEYS:
        match = _AWG_H_RE.fullmatch(value)
        if not match:
            raise ValueError(f'خط {lineno}: مقدار {key} باید عدد یا بازه «a-b» باشد')
        low = int(match.group(1))
        high = int(match.group(2)) if match.group(2) else low
        if low > high or high > AWG_UINT32_MAX:
            raise ValueError(f'خط {lineno}: مقدار {key} خارج از محدوده است')
        return f'{low}-{high}' if match.group(2) else str(low)

    if not _AWG_UINT_RE.fullmatch(value):
        raise ValueError(f'خط {lineno}: مقدار {key} باید عدد صحیح و غیرمنفی باشد')
    return int(value)


def parse_obfuscation(text):
    """پارامترهای AmneziaWG را از متن چسبانده‌شده می‌خواند.

    متن خالی یعنی WireGuard ساده و None برمی‌گردد. فقط خط‌های «Key = value» با کلیدهای
    AWG_KEYS قبول می‌شوند. هیچ خطایی متن ورودی را تکرار نمی‌کند، چون ممکن است
    کلید خصوصی باشد که کاربر اشتباهی چسبانده؛ فقط شماره خط گزارش می‌شود.
    """
    if not text or not text.strip():
        return None

    params = {}
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        if '=' not in line:
            raise ValueError(f'خط {lineno}: باید به شکل «نام = مقدار» باشد')
        key, value = (part.strip() for part in line.split('=', 1))
        if key not in AWG_KEYS:
            raise ValueError(
                f'خط {lineno}: پارامتر پشتیبانی‌نشده. فقط ' + ', '.join(AWG_KEYS) + ' مجازند')
        if key in params:
            raise ValueError(f'خط {lineno}: {key} تکراری است')
        params[key] = _parse_obfuscation_value(key, value, lineno)

    missing = [key for key in AWG_REQUIRED_KEYS if key not in params]
    if missing:
        raise ValueError('پارامترهای AmneziaWG ناقص‌اند: ' + ', '.join(missing))
    params = {**AWG_DEFAULTS, **params}
    if params['Jmin'] > params['Jmax']:
        raise ValueError('Jmin نباید از Jmax بزرگ‌تر باشد')
    return params


def build_wireguard_config(server, private_key='', address=WG_ADDRESS, dns=WG_DNS, obfuscation=None):
    """ساخت متن فایل .conf برای یک سرور.

    کلید خصوصی به حساب Proton وابسته است و از دیتابیس عمومی به دست نمی‌آید؛
    اگر ورودی داده نشود، جای آن placeholder قرار می‌گیرد.
    obfuscation (خروجی parse_obfuscation) اگر داده شود، پارامترهای AmneziaWG به [Interface] اضافه می‌شود.
    """
    public_key = server.get('wg_key', '')
    if not public_key:
        raise ValueError(f"{server['name']}: کلید عمومی WireGuard در دیتابیس موجود نیست")
    if not is_valid_wg_key(public_key):
        raise ValueError(f"{server['name']}: کلید عمومی WireGuard نامعتبر است")
    try:
        ipaddress.IPv4Address(server['ip'])
    except ValueError:
        raise ValueError(f"{server['name']}: آدرس IP سرور نامعتبر است")
    if private_key and not is_valid_wg_key(private_key):
        raise ValueError('کلید خصوصی WireGuard نامعتبر است (باید ۴۴ کاراکتر base64 باشد)')

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
        f'Endpoint = {server["ip"]}:{WG_PORT}',
        f'PersistentKeepalive = {PERSISTENT_KEEPALIVE}',
        '',
    ]
    return '\n'.join(lines)


def safe_filename(name):
    return re.sub(r'[^A-Za-z0-9_-]+', '_', name).strip('_') or 'server'


def write_wireguard_config(server, directory, private_key='', obfuscation=None):
    os.makedirs(directory, exist_ok=True)
    conf = build_wireguard_config(server, private_key, obfuscation=obfuscation)
    suffix = '_awg' if obfuscation else ''
    path = os.path.join(directory, safe_filename(server['name']) + suffix + '.conf')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(conf)
    return path


def export_wireguard_configs(servers, directory, private_key='', obfuscation=None):
    """برمی‌گرداند (مسیرهای نوشته‌شده, نام سرورهای رد‌شده)."""
    written, skipped = [], []
    for server in servers:
        try:
            written.append(write_wireguard_config(server, directory, private_key, obfuscation))
        except ValueError:
            skipped.append(server['name'])
    return written, skipped


# ---------- بررسی handshake با کلید خصوصی ----------
# یک پیام initiation واقعی WireGuard (Noise IKpsk2) می‌فرستد. سرور فقط وقتی جواب
# می‌دهد که کلید عمومی ما را بشناسد؛ پس پاسخ معتبر یعنی کلید کار می‌کند.
HANDSHAKE_TIMEOUT_S = 2.0
_WG_CONSTRUCTION = b'Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s'
_WG_IDENTIFIER = b'WireGuard v1 zx2c4 Jason@zx2c4.com'
_WG_LABEL_MAC1 = b'mac1----'
_WG_ZERO_NONCE = b'\x00' * 12
_WG_INIT_TYPE = 1
_WG_RESPONSE_TYPE = 2
_WG_RESPONSE_LEN = 92


def handshake_supported():
    return X25519PrivateKey is not None


def _wg_hash(*parts):
    digest = hashlib.blake2s()
    for part in parts:
        digest.update(part)
    return digest.digest()


def _wg_kdf(chaining_key, data, count):
    tau = hmac.new(chaining_key, data, hashlib.blake2s).digest()
    outputs, previous = [], b''
    for index in range(1, count + 1):
        previous = hmac.new(tau, previous + bytes([index]), hashlib.blake2s).digest()
        outputs.append(previous)
    return outputs


def _wg_public_bytes(private):
    return private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _wg_tai64n():
    now = time.time()
    return struct.pack('>QI', int(now) + 0x400000000000000a, int((now % 1) * 1e9))


def build_handshake_initiation(private_key, peer_public_key, sender=None, timestamp=None):
    """پیام initiation (۱۴۸ بایت) را می‌سازد. برمی‌گرداند (packet, sender, public_key_ما)."""
    own_private = X25519PrivateKey.from_private_bytes(base64.b64decode(private_key))
    own_public = _wg_public_bytes(own_private)
    peer_public = base64.b64decode(peer_public_key)
    peer = X25519PublicKey.from_public_bytes(peer_public)
    ephemeral = X25519PrivateKey.generate()
    ephemeral_public = _wg_public_bytes(ephemeral)

    chaining = _wg_hash(_WG_CONSTRUCTION)
    digest = _wg_hash(_wg_hash(chaining, _WG_IDENTIFIER), peer_public)
    chaining = _wg_kdf(chaining, ephemeral_public, 1)[0]
    digest = _wg_hash(digest, ephemeral_public)

    chaining, key = _wg_kdf(chaining, ephemeral.exchange(peer), 2)
    encrypted_static = ChaCha20Poly1305(key).encrypt(_WG_ZERO_NONCE, own_public, digest)
    digest = _wg_hash(digest, encrypted_static)

    chaining, key = _wg_kdf(chaining, own_private.exchange(peer), 2)
    encrypted_timestamp = ChaCha20Poly1305(key).encrypt(
        _WG_ZERO_NONCE, timestamp or _wg_tai64n(), digest)

    sender = sender or os.urandom(4)
    body = struct.pack('<I', _WG_INIT_TYPE) + sender + ephemeral_public + encrypted_static + encrypted_timestamp
    mac1 = hashlib.blake2s(body, key=_wg_hash(_WG_LABEL_MAC1, peer_public), digest_size=16).digest()
    return body + mac1 + b'\x00' * 16, sender, own_public


def _is_handshake_response(packet, sender, mac_key):
    if len(packet) != _WG_RESPONSE_LEN:
        return False
    if struct.unpack('<I', packet[:4])[0] != _WG_RESPONSE_TYPE or packet[8:12] != sender:
        return False
    expected = hashlib.blake2s(packet[:60], key=mac_key, digest_size=16).digest()
    return hmac.compare_digest(packet[60:76], expected)


def verify_handshake(server, private_key, timeout=HANDSHAKE_TIMEOUT_S, port=None):
    """True اگر سرور با این کلید خصوصی پاسخ handshake معتبر بدهد؛ در غیر این صورت False.

    False یعنی «این کلید پذیرفته نشد یا سرور در دسترس نیست»؛ این دو حالت را از هم جدا
    نمی‌کند، چون WireGuard به کلید ناشناخته هیچ پاسخی نمی‌دهد.
    """
    if not handshake_supported():
        raise RuntimeError('برای بررسی کلید بسته‌ی cryptography لازم است')
    if not is_valid_wg_key(private_key):
        raise ValueError('کلید خصوصی WireGuard نامعتبر است')
    if not is_valid_wg_key(server.get('wg_key', '')):
        raise ValueError(f"{server['name']}: کلید عمومی WireGuard نامعتبر یا موجود نیست")
    try:
        ipaddress.IPv4Address(server['ip'])
    except ValueError:
        return False

    packet, sender, own_public = build_handshake_initiation(private_key, server['wg_key'])
    mac_key = _wg_hash(_WG_LABEL_MAC1, own_public)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(packet, (server['ip'], port or WG_PORT))
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            sock.settimeout(remaining)
            try:
                response, source = sock.recvfrom(2048)
            except socket.timeout:
                return False
            # فقط پاسخ از خود سرور قبول می‌شود، نه هر میزبانی که بسته‌ای برگرداند
            if source[0] == server['ip'] and _is_handshake_response(response, sender, mac_key):
                return True
    except OSError:
        return False
    finally:
        sock.close()
