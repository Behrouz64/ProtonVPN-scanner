"""ساخت پیام handshake WireGuard فقط با کتابخانه‌ی استاندارد پایتون.

این ماژول برای تست دسترسی UDP سرورها ساخته شده است، نه برای رمزنگاری ترافیک. دلیلش این است که
بسته‌ی `cryptography` روی بعضی بسته‌بندی‌های موبایل (Android/iOS) قابل اعتماد نیست. کارایی برای چند
صد پیام کافی است؛ اجرای غیرثابت زمان (constant-time) نیازی ندارد چون کلید تازه‌ی تست است.

اجزا:
- X25519 (RFC 7748)
- ChaCha20-Poly1305 (RFC 8439)
- BLAKE2s، HMAC-BLAKE2s و KDF مطابق مشخصات WireGuard
"""
import hashlib
import hmac
import os
import struct
import time

_P = 2 ** 255 - 19
_A24 = 121665
_BASE_U = (9).to_bytes(32, 'little')
_MASK32 = 0xFFFFFFFF

WG_INITIATION_SIZE = 148
WG_RESPONSE_SIZE = 92
WG_MSG_INITIATION = 1
WG_MSG_RESPONSE = 2

_CONSTRUCTION = b'Noise_IKpsk2_25519_ChaChaPoly_BLAKE2s'
_IDENTIFIER = b'WireGuard v1 zx2c4 Jason@zx2c4.com'
_LABEL_MAC1 = b'mac1----'
_NONCE_ZERO = bytes(12)


# ---------- X25519 ----------
def _clamp(scalar):
    buf = bytearray(scalar)
    buf[0] &= 248
    buf[31] &= 127
    buf[31] |= 64
    return bytes(buf)


def x25519(scalar, u_bytes):
    """ضرب نردبان مونتگومری (RFC 7748)؛ خروجی ۳۲ بایت است."""
    k = int.from_bytes(_clamp(scalar), 'little')
    x1 = int.from_bytes(u_bytes, 'little') & ((1 << 255) - 1)
    x2, z2, x3, z3 = 1, 0, x1, 1
    swap = 0
    for t in reversed(range(255)):
        bit = (k >> t) & 1
        swap ^= bit
        if swap:
            x2, x3 = x3, x2
            z2, z3 = z3, z2
        swap = bit
        a = (x2 + z2) % _P
        aa = a * a % _P
        b = (x2 - z2) % _P
        bb = b * b % _P
        e = (aa - bb) % _P
        c = (x3 + z3) % _P
        d = (x3 - z3) % _P
        da = d * a % _P
        cb = c * b % _P
        x3 = (da + cb) % _P
        x3 = x3 * x3 % _P
        z3 = (da - cb) % _P
        z3 = x1 * (z3 * z3 % _P) % _P
        x2 = aa * bb % _P
        z2 = e * (aa + _A24 * e) % _P
    if swap:
        x2, x3 = x3, x2
        z2, z3 = z3, z2
    return (x2 * pow(z2, _P - 2, _P) % _P).to_bytes(32, 'little')


def public_key(private_key):
    return x25519(private_key, _BASE_U)


# ---------- ChaCha20-Poly1305 ----------
def _rotl(value, count):
    return ((value << count) & _MASK32) | (value >> (32 - count))


def _chacha_block(key, counter, nonce):
    state = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]
    state += list(struct.unpack('<8I', key))
    state += [counter & _MASK32]
    state += list(struct.unpack('<3I', nonce))
    work = state[:]

    def quarter(a, b, c, d):
        work[a] = (work[a] + work[b]) & _MASK32
        work[d] = _rotl(work[d] ^ work[a], 16)
        work[c] = (work[c] + work[d]) & _MASK32
        work[b] = _rotl(work[b] ^ work[c], 12)
        work[a] = (work[a] + work[b]) & _MASK32
        work[d] = _rotl(work[d] ^ work[a], 8)
        work[c] = (work[c] + work[d]) & _MASK32
        work[b] = _rotl(work[b] ^ work[c], 7)

    for _ in range(10):
        quarter(0, 4, 8, 12)
        quarter(1, 5, 9, 13)
        quarter(2, 6, 10, 14)
        quarter(3, 7, 11, 15)
        quarter(0, 5, 10, 15)
        quarter(1, 6, 11, 12)
        quarter(2, 7, 8, 13)
        quarter(3, 4, 9, 14)
    return struct.pack('<16I', *[(work[i] + state[i]) & _MASK32 for i in range(16)])


def _chacha_xor(key, counter, nonce, data):
    out = bytearray(len(data))
    for block_index in range(0, len(data), 64):
        stream = _chacha_block(key, counter + block_index // 64, nonce)
        for offset, byte in enumerate(data[block_index:block_index + 64]):
            out[block_index + offset] = byte ^ stream[offset]
    return bytes(out)


def _poly1305(key, message):
    r = int.from_bytes(key[:16], 'little') & 0x0FFFFFFC0FFFFFFC0FFFFFFC0FFFFFFF
    s = int.from_bytes(key[16:32], 'little')
    prime = (1 << 130) - 5
    acc = 0
    for start in range(0, len(message), 16):
        chunk = message[start:start + 16]
        acc = (acc + int.from_bytes(chunk + b'\x01', 'little')) * r % prime
    return ((acc + s) & ((1 << 128) - 1)).to_bytes(16, 'little')


def _pad16(data):
    return bytes((16 - len(data) % 16) % 16)


def aead_encrypt(key, nonce, plaintext, aad=b''):
    """ChaCha20-Poly1305: خروجی = متن رمز + تگ ۱۶ بایتی."""
    poly_key = _chacha_block(key, 0, nonce)[:32]
    ciphertext = _chacha_xor(key, 1, nonce, plaintext)
    mac_data = (aad + _pad16(aad) + ciphertext + _pad16(ciphertext)
                + struct.pack('<Q', len(aad)) + struct.pack('<Q', len(ciphertext)))
    return ciphertext + _poly1305(poly_key, mac_data)


# ---------- هش و KDF ----------
def blake2s(*parts):
    digest = hashlib.blake2s()
    for part in parts:
        digest.update(part)
    return digest.digest()


def _hmac(key, data):
    return hmac.new(key, data, hashlib.blake2s).digest()


def _kdf1(chain_key, data):
    temp = _hmac(chain_key, data)
    return _hmac(temp, b'\x01')


def _kdf2(chain_key, data):
    temp = _hmac(chain_key, data)
    first = _hmac(temp, b'\x01')
    second = _hmac(temp, first + b'\x02')
    return first, second


def _tai64n_now():
    now = time.time()
    seconds = (1 << 62) + int(now) + 10  # برچسب TAI64 با آفست ۱۰ ثانیه‌ی ثابت
    nanos = int((now - int(now)) * 1e9)
    return struct.pack('>QI', seconds, nanos)


# ---------- پیام handshake ----------
def build_initiation(client_private, server_public, sender_index=None):
    """پیام ۱۴۸ بایتی Handshake Initiation مطابق WireGuard.

    client_private کلید خصوصی حساب کاربر است و باید در لیست peerهای سرور باشد؛ وگرنه سرور
    پیام را بی‌پاسخ رها می‌کند.
    """
    if len(client_private) != 32 or len(server_public) != 32:
        raise ValueError('WireGuard keys must be 32 bytes')
    if sender_index is None:
        sender_index = os.urandom(4)
    ephemeral_private = os.urandom(32)
    ephemeral_public = public_key(ephemeral_private)
    static_public = public_key(client_private)

    chain = blake2s(_CONSTRUCTION)
    digest = blake2s(chain, _IDENTIFIER)
    digest = blake2s(digest, server_public)

    chain = _kdf1(chain, ephemeral_public)
    digest = blake2s(digest, ephemeral_public)

    chain, key = _kdf2(chain, x25519(ephemeral_private, server_public))
    encrypted_static = aead_encrypt(key, _NONCE_ZERO, static_public, digest)
    digest = blake2s(digest, encrypted_static)

    chain, key = _kdf2(chain, x25519(client_private, server_public))
    encrypted_timestamp = aead_encrypt(key, _NONCE_ZERO, _tai64n_now(), digest)

    body = (struct.pack('<I', WG_MSG_INITIATION) + sender_index + ephemeral_public
            + encrypted_static + encrypted_timestamp)
    mac1 = blake2s_mac(blake2s(_LABEL_MAC1, server_public), body, 16)
    return body + mac1 + bytes(16)  # mac2 فقط وقتی کوکی داریم لازم است؛ اینجا صفر است


def blake2s_mac(key, data, size=16):
    return hashlib.blake2s(data, key=key, digest_size=size).digest()


def is_handshake_response(packet):
    """پاسخ Handshake Response دارای نوع ۲ و اندازه‌ی ۹۲ بایت است."""
    return (len(packet) == WG_RESPONSE_SIZE
            and struct.unpack('<I', packet[:4])[0] == WG_MSG_RESPONSE)
