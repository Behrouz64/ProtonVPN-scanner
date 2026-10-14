"""ساخت assets/surfshark/servers.json از فهرست سرورهای Surfshark.

فقط فهرست `servers` خوانده می‌شود. بخش `user_interface` (کلید خصوصی، آدرس و DNS یک حساب) عمداً
نادیده گرفته می‌شود تا هیچ کلید خصوصی وارد برنامه یا مخزن نشود.

استفاده:
    python tools/build_surfshark_catalog.py path/to/surfshark_servers.json
    curl -s <URL> | python tools/build_surfshark_catalog.py -
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'surfshark', 'servers.json')
PUBLIC_KEY_RE = re.compile(r'[A-Za-z0-9+/]{43}=')
COUNTRY_CODE_RE = re.compile(r'[A-Z]{2}')
HOST_SUFFIX = '.surfshark.com'
DEFAULT_PORT = 51820


def build(raw_text):
    """یک رشته‌ی JSON خام را به فهرست سرورهای معتبر تبدیل می‌کند."""
    data = json.loads(raw_text)
    servers = []
    for item in data.get('servers', []):
        host = item.get('hostname', '')
        code = item.get('country_code', '')
        public_key = item.get('public_key', '')
        if not host.endswith(HOST_SUFFIX):
            continue
        if not COUNTRY_CODE_RE.fullmatch(code):
            continue
        if not PUBLIC_KEY_RE.fullmatch(public_key):
            continue
        servers.append({
            'hostname': host,
            'country': item.get('country', ''),
            'country_code': code,
            'city': item.get('city', ''),
            'port': int(item.get('port') or DEFAULT_PORT),
            'public_key': public_key,
        })
    return {'source': 'Surfshark server list', 'count': len(servers), 'servers': servers}


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    raw = sys.stdin.read() if argv[1] == '-' else open(argv[1], encoding='utf-8').read()
    catalog = build(raw)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(f"wrote {catalog['count']} servers to {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
