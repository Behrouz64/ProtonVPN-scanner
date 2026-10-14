"""تست دسترسی UDP سرورهای Surfshark با پیام Handshake واقعی WireGuard.

سرور WireGuard پیام‌های ناشناس را بی‌پاسخ رها می‌کند، پس پیام باید با کلید خصوصی حساب کاربر ساخته شود.
اگر سرور پیام را بپذیرد، Handshake Response (نوع ۲، ۹۲ بایت) برمی‌گرداند و زمان رفت‌وبرگشت همان پینگ است.
"""
import base64
import socket
import time
from contextlib import closing

import wg_crypto

WG_PORT = 51820
PROBE_LABEL = 'UDP:51820'


def handshake_rtt(host, server_public_key, private_key, timeout=1.5, port=WG_PORT):
    """(ms, برچسب) اگر سرور پاسخ Handshake بدهد؛ در غیر این صورت (None, None)."""
    if not private_key or not server_public_key:
        return None, None
    try:
        address = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_DGRAM)[0][4][0]
        packet = wg_crypto.build_initiation(_decode(private_key), _decode(server_public_key))
    except (OSError, ValueError, IndexError):
        return None, None

    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as sock:
        sock.settimeout(timeout)
        start = time.monotonic()
        try:
            sock.sendto(packet, (address, port))
            reply, _ = sock.recvfrom(256)
        except OSError:
            return None, None
        if not wg_crypto.is_handshake_response(reply):
            return None, None
        return int((time.monotonic() - start) * 1000), PROBE_LABEL


def _decode(base64_key):
    return base64.b64decode(base64_key, validate=True)
