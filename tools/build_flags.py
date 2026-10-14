"""ساخت assets/flags/<cc>.png برای همه‌ی کشورهای برنامه.

منبع: مخزن lipis/flag-icons با مجوز MIT (پرچم‌های 4x3). SVG با ImageMagick به PNG تبدیل می‌شود.
این اسکریپت فقط برای توسعه است و هنگام اجرای برنامه لازم نیست.

نیازمندی: دستور `convert` (ImageMagick) روی مسیر سیستم.
استفاده:
    python tools/build_flags.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import scanner_core as core  # noqa: E402

SOURCE = 'https://raw.githubusercontent.com/lipis/flag-icons/master'
OUT_DIR = os.path.join(ROOT, 'assets', 'flags')
WIDTH, HEIGHT = 96, 72
# کدهایی که با ISO یکی نیستند
CODE_ALIASES = {'UK': 'gb'}
SKIP_CODES = {core.UNKNOWN_CC, core.ALL_COUNTRIES}


def country_codes():
    codes = set(core.CC_TO_NAME)
    codes |= {s['cc'] for s in core.load_surfshark_catalog()}
    return sorted(c for c in codes if c not in SKIP_CODES)


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def main():
    if shutil.which('convert') is None:
        print('ImageMagick (convert) is required')
        return 2
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, 'LICENSE.txt'), 'wb') as f:
        f.write(b'Flag images: https://github.com/lipis/flag-icons (MIT License)\n'
                b'Copyright (c) 2013 Panayiotis Lipiridis\n\n' + fetch(f'{SOURCE}/LICENSE'))
    missing = []
    with tempfile.TemporaryDirectory() as scratch:
        for cc in country_codes():
            name = CODE_ALIASES.get(cc, cc).lower()
            try:
                svg = fetch(f'{SOURCE}/flags/4x3/{name}.svg')
            except OSError:
                missing.append(cc)
                continue
            svg_path = os.path.join(scratch, f'{name}.svg')
            with open(svg_path, 'wb') as f:
                f.write(svg)
            out_path = os.path.join(OUT_DIR, f'{cc.lower()}.png')
            subprocess.run(['convert', '-background', 'none', svg_path,
                            '-resize', f'{WIDTH}x{HEIGHT}!', out_path], check=True)
    print(f'wrote flags to {os.path.relpath(OUT_DIR, ROOT)}; missing: {missing or "none"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
