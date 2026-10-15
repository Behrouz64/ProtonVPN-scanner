"""ساخت assets/surfshark/ips.json: فهرست IPهای میزبان‌های Surfshark برای نسخه‌ی همراه برنامه.

این فایل فقط زمانی لازم است که کاربر نتواند IP را با DNS خودش بگیرد. ترتیب استفاده‌ی برنامه:
کش محلی تازه، سپس همین فهرست، و در آخر DNS زنده.

باید روی یک شبکه‌ی بدون آلودگی DNS اجرا شود (مثلاً با VPN روشن) و خروجی را پیش از انتشار بازبینی کنید.
استفاده:
    python tools/build_surfshark_ips.py
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import scanner_core as core  # noqa: E402
import surfshark_ips  # noqa: E402


def main():
    servers = core.load_surfshark_catalog(core.SURFSHARK_CATALOG_FILE)
    hosts = sorted({server['hostname'] for server in servers})
    now = time.time()
    fresh, failed = surfshark_ips.refresh(hosts, core.resolve_ipv4, now, core.SURFSHARK_IP_MAX)
    data = {
        'source': 'system DNS on the build machine; review before publishing',
        'generated_at': int(now),
        'hosts': {host: entry['ips'] for host, entry in sorted(fresh.items())},
    }
    os.makedirs(os.path.dirname(core.SURFSHARK_IPS_FILE), exist_ok=True)
    with open(core.SURFSHARK_IPS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'IPs for {len(fresh)} of {len(hosts)} hosts written to {core.SURFSHARK_IPS_FILE}')
    for host in failed:
        print(f'  no answer: {host}')
    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(main())
