import base64
import json
import os
import re
import socket
import struct
import threading
import unittest
from unittest import mock

import scanner_core as core
import surfshark_core
import wg_crypto

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, 'assets', 'surfshark', 'servers.json')
KEY_RE = re.compile(r'[A-Za-z0-9+/]{43}=')

# کلیدهای تستی ساختگی (نه کلید واقعی کاربر)
TEST_PRIVATE = base64.b64encode(bytes(range(1, 33))).decode()
TEST_PUBLIC = base64.b64encode(bytes(range(33, 65))).decode()


def _all_strings(node, field=''):
    """همه‌ی مقادیر رشته‌ای به همراه نام فیلد نزدیک‌ترشان."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _all_strings(value, key)
    elif isinstance(node, list):
        for item in node:
            yield from _all_strings(item, field)
    elif isinstance(node, str):
        yield (field, node)


class SurfsharkCatalogTests(unittest.TestCase):
    def setUp(self):
        with open(CATALOG, encoding='utf-8') as f:
            self.data = json.load(f)

    def test_catalog_has_servers_from_the_list_only(self):
        self.assertEqual(sorted(self.data), ['count', 'servers', 'source'])
        self.assertEqual(self.data['count'], len(self.data['servers']))
        self.assertEqual(len(self.data['servers']), 76)

    def test_no_account_secrets_in_catalog(self):
        text = json.dumps(self.data)
        for name in ('user_interface', 'private_key', '"address"', '"dns"'):
            self.assertNotIn(name, text)

    def test_only_public_keys_are_key_shaped(self):
        for field, value in _all_strings(self.data):
            if KEY_RE.fullmatch(value):
                self.assertEqual(field, 'public_key', f'unexpected key-shaped value in {field!r}')

    def test_every_entry_is_a_surfshark_host_with_known_country(self):
        for server in self.data['servers']:
            with self.subTest(host=server['hostname']):
                self.assertTrue(server['hostname'].endswith('.prod.surfshark.com'))
                self.assertIn(server['country_code'], core.CC_TO_NAME)
                self.assertIn(server['country_code'], sum(core.CONTINENTS.values(), []))

    def test_loader_builds_surfshark_servers(self):
        servers = core.load_surfshark_catalog(CATALOG)
        self.assertEqual(len(servers), 76)
        first = servers[0]
        self.assertEqual(first['provider'], core.PROVIDER_SURFSHARK)
        self.assertFalse(first['free'])
        self.assertEqual(first['port'], 51820)
        self.assertEqual(first['name'], f"{first['cc']}-{first['city']}")


class SurfsharkKeyTests(unittest.TestCase):
    def test_private_key_alone_creates_identity_with_default_tunnel(self):
        identity = core.surfshark_identity(f'  {TEST_PRIVATE}  ')
        self.assertEqual(identity.private_key, TEST_PRIVATE)
        self.assertEqual(identity.address, core.SURFSHARK_ADDRESS)
        self.assertEqual(identity.dns, core.SURFSHARK_DNS)

    def test_invalid_key_is_rejected(self):
        for value in ('', 'not-a-key', TEST_PUBLIC + 'x'):
            with self.subTest(value=value), self.assertRaises(core.ConfigError) as ctx:
                core.surfshark_identity(value)
            self.assertEqual(ctx.exception.code, 'bad_private_key')


class SurfsharkConfigTests(unittest.TestCase):
    def setUp(self):
        self.server = {**core.load_surfshark_catalog(CATALOG)[0], 'ip': '203.0.113.5'}
        self.identity = core.WgIdentity(private_key=TEST_PRIVATE, address='10.14.0.2/16', dns='162.252.172.57')

    def test_config_uses_host_port_and_account_address(self):
        conf = core.build_wireguard_config(self.server, self.identity.private_key,
                                           address=self.identity.address, dns=self.identity.dns)
        self.assertIn(f"Endpoint = {self.server['ip']}:51820", conf)
        self.assertIn(f"PublicKey = {self.server['wg_key']}", conf)
        self.assertIn('Address = 10.14.0.2/16', conf)
        self.assertIn('DNS = 162.252.172.57', conf)

    def test_link_uses_host_marker_and_account_address(self):
        link = core.build_wg_link(self.server, self.identity.private_key,
                                  address=self.identity.address, dns=self.identity.dns)
        self.assertTrue(link.startswith(f"wg://{self.server['ip']}:51820?"))
        self.assertIn('ip=10.14.0.2', link)
        self.assertIn('%F0%9F%A6%88', link)  # 🦈

    def test_file_names_are_prefixed_by_provider(self):
        self.assertEqual(core.config_file_stem(self.server), 'surfshark_' + core.safe_filename(self.server['name']))
        self.assertEqual(core.config_file_stem(self.server, '_awg'),
                         'surfshark_' + core.safe_filename(self.server['name']) + '_awg')

    def test_surfshark_entries_are_not_free(self):
        free = core.filter_by_tier([self.server], 'free')
        paid = core.filter_by_tier([self.server], 'paid')
        self.assertEqual(free, [])
        self.assertEqual(paid, [self.server])


class ProbeDispatchTests(unittest.TestCase):
    def test_surfshark_uses_handshake_probe(self):
        server = {**core.load_surfshark_catalog(CATALOG)[0], 'ip': '203.0.113.5'}
        with mock.patch.object(surfshark_core, 'handshake_rtt', return_value=(42, 'UDP:51820')) as probe:
            result = core.probe_server(server, TEST_PRIVATE)
        self.assertEqual(result, (42, 'UDP:51820'))
        probe.assert_called_once_with('203.0.113.5', server['wg_key'], TEST_PRIVATE, port=server['port'])

    def test_proton_keeps_the_ping(self):
        server = {'name': 'US#1', 'ip': '203.0.113.7', 'cc': 'US', 'provider': core.PROVIDER_PROTON}
        with mock.patch.object(core, 'smart_ping', return_value=(120, 'TCP:443')) as ping:
            self.assertEqual(core.probe_server(server, TEST_PRIVATE), (120, 'TCP:443'))
        ping.assert_called_once_with('203.0.113.7')


class ScanModeTests(unittest.TestCase):
    def setUp(self):
        self.server = core.load_surfshark_catalog(CATALOG)[0]

    def test_keyless_probe_pings_the_ip_without_dns(self):
        server = {**self.server, 'ip': '203.0.113.9'}
        with mock.patch.object(core.socket, 'getaddrinfo') as dns, \
                mock.patch.object(core, 'smart_ping', return_value=(77, 'TCP:443')) as ping, \
                mock.patch.object(surfshark_core, 'handshake_rtt') as handshake:
            result = core.probe_server(server, '', core.SCAN_WITHOUT_KEY)
        self.assertEqual(result, (77, 'TCP:443'))
        ping.assert_called_once_with('203.0.113.9')
        dns.assert_not_called()
        handshake.assert_not_called()

    def test_resolve_ipv4_keeps_unique_addresses_up_to_limit(self):
        answers = [(None, None, None, None, (ip, 0)) for ip in
                   ('198.51.100.1', '198.51.100.1', '198.51.100.2', '198.51.100.3')]
        with mock.patch.object(core.socket, 'getaddrinfo', return_value=answers):
            self.assertEqual(core.resolve_ipv4('host.example'), ['198.51.100.1', '198.51.100.2'])
            self.assertEqual(core.resolve_ipv4('host.example', limit=1), ['198.51.100.1'])

    def test_resolve_ipv4_dns_error_gives_empty_list(self):
        with mock.patch.object(core.socket, 'getaddrinfo', side_effect=OSError('no dns')):
            self.assertEqual(core.resolve_ipv4('nowhere.invalid.example'), [])

    def test_scan_server_keeps_the_faster_usable_ip(self):
        with mock.patch.object(core, 'resolve_ipv4', return_value=['198.51.100.1', '198.51.100.2']), \
                mock.patch.object(surfshark_core, 'handshake_rtt',
                                  side_effect=[(80, 'UDP:51820'), (35, 'UDP:51820')]) as handshake:
            found = core.scan_server(self.server, TEST_PRIVATE, core.SCAN_WITH_KEY, 10)
        self.assertEqual(found['ip'], '198.51.100.2')
        self.assertEqual(found['hostname'], self.server['hostname'])
        self.assertEqual((found['ping'], found['proto']), (35, 'UDP:51820'))
        self.assertEqual([call.args[0] for call in handshake.call_args_list], ['198.51.100.1', '198.51.100.2'])

    def test_scan_server_drops_replies_below_threshold(self):
        with mock.patch.object(core, 'resolve_ipv4', return_value=['198.51.100.1']), \
                mock.patch.object(core, 'smart_ping', return_value=(4, 'TCP:443')):
            self.assertIsNone(core.scan_server(self.server, '', core.SCAN_WITHOUT_KEY, 10))

    def test_scan_server_dns_failure_gives_none(self):
        with mock.patch.object(core.socket, 'getaddrinfo', side_effect=OSError('no dns')):
            self.assertIsNone(core.scan_server(self.server, '', core.SCAN_WITHOUT_KEY, 10))

    def test_proton_scan_uses_its_own_ip(self):
        server = {'name': 'US#1', 'ip': '203.0.113.7', 'cc': 'US', 'provider': core.PROVIDER_PROTON}
        with mock.patch.object(core.socket, 'getaddrinfo') as dns, \
                mock.patch.object(core, 'smart_ping', return_value=(120, 'TCP:443')) as ping:
            found = core.scan_server(server, '', core.SCAN_WITHOUT_KEY, 10)
        dns.assert_not_called()
        ping.assert_called_once_with('203.0.113.7')
        self.assertEqual(found['ip'], '203.0.113.7')
        self.assertEqual(found['ping'], 120)

    def test_config_ready_resolves_surfshark_hostnames(self):
        proton = {'name': 'US#1', 'ip': '203.0.113.7', 'cc': 'US', 'provider': core.PROVIDER_PROTON}
        with mock.patch.object(core, 'resolve_ipv4', return_value=['198.51.100.2']):
            ready, unresolved = core.config_ready([self.server, proton])
        self.assertEqual(unresolved, [])
        self.assertEqual(ready[0]['ip'], '198.51.100.2')
        self.assertEqual(ready[0]['hostname'], self.server['hostname'])
        self.assertEqual(ready[1], proton)

    def test_config_ready_reports_unresolved_hosts(self):
        with mock.patch.object(core, 'resolve_ipv4', return_value=[]):
            ready, unresolved = core.config_ready([self.server])
        self.assertEqual(ready, [])
        self.assertEqual(unresolved, [self.server])

    def test_config_refuses_a_hostname_endpoint(self):
        with self.assertRaises(core.ConfigError) as ctx:
            core.build_wireguard_config(self.server, TEST_PRIVATE)
        self.assertEqual(ctx.exception.code, 'bad_ip')

    def test_reply_threshold_rule(self):
        self.assertFalse(core.is_usable_reply(None, 0))
        self.assertTrue(core.is_usable_reply(0, 0))
        self.assertFalse(core.is_usable_reply(9, 10))
        self.assertTrue(core.is_usable_reply(10, 10))
        self.assertTrue(core.is_usable_reply(3, 0))

    def test_threshold_choices_include_default(self):
        self.assertIn(core.MIN_PLAUSIBLE_PING_MS, core.FAKE_THRESHOLD_CHOICES)
        self.assertIn(0, core.FAKE_THRESHOLD_CHOICES)


class WgCryptoTests(unittest.TestCase):
    def test_x25519_rfc7748_vector(self):
        scalar = bytes.fromhex('a546e36bf0527c9d3b16154b82465edd62144c0ac1fc5a18506a2244ba449ac4')
        point = bytes.fromhex('e6db6867583030db3594c1a424b15f7c726624ec26b3353b10a903a6d0ab1c4c')
        self.assertEqual(wg_crypto.x25519(scalar, point).hex(),
                         'c3da55379de9c6908e94ea4df28d084f32eccf03491c71f754b4075577a28552')

    def test_public_key_vector(self):
        priv = bytes(range(1, 33))
        self.assertEqual(wg_crypto.public_key(priv).hex(),
                         '07a37cbc142093c8b755dc1b10e86cb426374ad16aa853ed0bdfc0b2b86d1c7c')

    def test_chacha20_block_vector(self):
        key = bytes(range(32))
        nonce = bytes([0, 0, 0, 9, 0, 0, 0, 0x4A, 0, 0, 0, 0])
        self.assertEqual(wg_crypto._chacha_block(key, 1, nonce)[:8].hex(), '10f1e7e4d13b5915')

    def test_aead_vector(self):
        key = bytes(range(32))
        out = wg_crypto.aead_encrypt(key, bytes(range(12)), b'hello wireguard', b'aad')
        self.assertEqual(out.hex(), 'e19e646c4637d229c5e65886f96f6a960c9adbf7e9ecccad1e7dbb0000b98b')

    def test_initiation_layout_and_mac1(self):
        server_public = wg_crypto.public_key(bytes(range(65, 97)))
        packet = wg_crypto.build_initiation(bytes(range(1, 33)), server_public, sender_index=b'\x01\x02\x03\x04')
        self.assertEqual(len(packet), wg_crypto.WG_INITIATION_SIZE)
        self.assertEqual(struct.unpack('<I', packet[:4])[0], wg_crypto.WG_MSG_INITIATION)
        self.assertEqual(packet[4:8], b'\x01\x02\x03\x04')
        mac_key = wg_crypto.blake2s(b'mac1----', server_public)
        self.assertEqual(packet[116:132], wg_crypto.blake2s_mac(mac_key, packet[:116], 16))
        self.assertEqual(packet[132:], bytes(16))

    def test_handshake_response_detection(self):
        self.assertTrue(wg_crypto.is_handshake_response(struct.pack('<I', 2) + bytes(88)))
        self.assertFalse(wg_crypto.is_handshake_response(struct.pack('<I', 1) + bytes(143)))
        self.assertFalse(wg_crypto.is_handshake_response(struct.pack('<I', 2) + bytes(10)))


class HandshakeProbeTests(unittest.TestCase):
    def _responder(self, reply):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('127.0.0.1', 0))
        sock.settimeout(3)
        port = sock.getsockname()[1]

        def run():
            try:
                packet, peer = sock.recvfrom(256)
                if reply is not None:
                    sock.sendto(reply, peer)
                self.received = packet
            except OSError:
                pass
            finally:
                sock.close()

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return port, thread

    def test_answered_handshake_returns_round_trip(self):
        self.received = None
        port, thread = self._responder(struct.pack('<I', 2) + bytes(88))
        ms, label = surfshark_core.handshake_rtt('127.0.0.1', TEST_PUBLIC, TEST_PRIVATE, timeout=2, port=port)
        thread.join(3)
        self.assertEqual(label, 'UDP:51820')
        self.assertIsInstance(ms, int)
        self.assertEqual(len(self.received), wg_crypto.WG_INITIATION_SIZE)

    def test_silent_server_returns_nothing(self):
        port, thread = self._responder(None)
        result = surfshark_core.handshake_rtt('127.0.0.1', TEST_PUBLIC, TEST_PRIVATE, timeout=0.3, port=port)
        thread.join(3)
        self.assertEqual(result, (None, None))

    def test_missing_key_skips_the_network(self):
        self.assertEqual(surfshark_core.handshake_rtt('127.0.0.1', TEST_PUBLIC, '', timeout=0.2, port=1),
                         (None, None))


if __name__ == '__main__':
    unittest.main()
