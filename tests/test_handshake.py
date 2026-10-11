import base64
import hashlib
import os
import socket
import struct
import threading
import unittest

import scanner_core as core

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

CLIENT_PRIVATE = 'uH1fTd6LVbwkNKs1qlozF15r9fchF/KqtZye1WSLk6E='
SERVER_PRIVATE = '9VYFayLDRmYouw8FvUcE9UdDBuzxwbbk2HPMWEh3DmU='


def public_of(private_b64):
    private = X25519PrivateKey.from_private_bytes(base64.b64decode(private_b64))
    return private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def keyed_mac1(data, peer_public):
    key = hashlib.blake2s(b'mac1----' + peer_public).digest()
    return hashlib.blake2s(data, key=key, digest_size=16).digest()


class FakeResponder:
    """یک سرور UDP که فقط وقتی پیام initiation معتبر ببیند جواب می‌دهد."""

    def __init__(self, client_public, echo_receiver=True):
        self.client_public = client_public
        self.echo_receiver = echo_receiver
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', 0))
        self.port = self.sock.getsockname()[1]
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        self.sock.settimeout(3)
        try:
            packet, addr = self.sock.recvfrom(2048)
        except OSError:
            return
        if len(packet) != 148:
            return
        receiver = packet[4:8] if self.echo_receiver else os.urandom(4)
        body = struct.pack('<I', 2) + os.urandom(4) + receiver + os.urandom(32) + os.urandom(16)
        self.sock.sendto(body + keyed_mac1(body, self.client_public) + b'\x00' * 16, addr)

    def close(self):
        self.thread.join(timeout=4)
        self.sock.close()


def closed_udp_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@unittest.skipUnless(HAS_CRYPTO, 'cryptography is not installed')
class HandshakeTests(unittest.TestCase):
    def setUp(self):
        self.client_public = public_of(CLIENT_PRIVATE)
        self.server_public = public_of(SERVER_PRIVATE)
        self.server = {
            'name': 'LOCAL',
            'ip': '127.0.0.1',
            'wg_key': base64.b64encode(self.server_public).decode(),
        }

    def test_supported_when_cryptography_installed(self):
        self.assertTrue(core.handshake_supported())

    def test_initiation_packet_layout(self):
        packet, sender, own_public = core.build_handshake_initiation(CLIENT_PRIVATE, self.server['wg_key'])
        self.assertEqual(len(packet), 148)
        self.assertEqual(struct.unpack('<I', packet[:4])[0], 1)
        self.assertEqual(packet[4:8], sender)
        self.assertEqual(own_public, self.client_public)
        self.assertEqual(packet[116:132], keyed_mac1(packet[:116], self.server_public))
        self.assertEqual(packet[132:148], b'\x00' * 16)

    def test_accepts_response_from_peer_that_knows_key(self):
        responder = FakeResponder(self.client_public)
        self.addCleanup(responder.close)
        server = {**self.server, 'ip': '127.0.0.1'}
        self.assertTrue(core.verify_handshake(server, CLIENT_PRIVATE, timeout=2.0, port=responder.port))

    def test_response_with_wrong_receiver_is_ignored(self):
        responder = FakeResponder(self.client_public, echo_receiver=False)
        self.addCleanup(responder.close)
        self.assertFalse(core.verify_handshake(self.server, CLIENT_PRIVATE, timeout=1.0, port=responder.port))

    def test_no_listener_returns_false(self):
        self.assertFalse(core.verify_handshake(self.server, CLIENT_PRIVATE, timeout=0.5, port=closed_udp_port()))

    def test_bad_server_ip_returns_false(self):
        server = {**self.server, 'ip': 'not-an-ip'}
        self.assertFalse(core.verify_handshake(server, CLIENT_PRIVATE, timeout=0.2))

    def test_invalid_private_key_raises(self):
        with self.assertRaises(ValueError):
            core.verify_handshake(self.server, 'short', timeout=0.2)

    def test_missing_server_key_raises(self):
        with self.assertRaises(ValueError):
            core.verify_handshake({**self.server, 'wg_key': ''}, CLIENT_PRIVATE, timeout=0.2)


class HandshakeUnavailableTests(unittest.TestCase):
    def test_handshake_supported_flag_matches_import(self):
        self.assertEqual(core.handshake_supported(), HAS_CRYPTO)



@unittest.skipUnless(
    os.environ.get('WG_TEST_PEER_PORT') and os.environ.get('WG_TEST_CLIENT_KEY') and os.environ.get('WG_TEST_SERVER_PUB'),
    'set WG_TEST_PEER_PORT, WG_TEST_CLIENT_KEY and WG_TEST_SERVER_PUB to test against a real WireGuard peer',
)
@unittest.skipUnless(HAS_CRYPTO, 'cryptography is not installed')
class RealPeerTests(unittest.TestCase):
    """اجرای اختیاری روی یک WireGuard واقعی (مثلاً wireguard-go با یک کلید تستی)."""

    def test_known_key_is_accepted_and_unknown_key_is_rejected(self):
        port = int(os.environ['WG_TEST_PEER_PORT'])
        server = {
            'name': 'REAL',
            'ip': '127.0.0.1',
            'wg_key': os.environ['WG_TEST_SERVER_PUB'],
        }
        self.assertTrue(core.verify_handshake(server, os.environ['WG_TEST_CLIENT_KEY'], port=port))
        self.assertFalse(core.verify_handshake(server, SERVER_PRIVATE, port=port, timeout=1.0))

if __name__ == '__main__':
    unittest.main()
