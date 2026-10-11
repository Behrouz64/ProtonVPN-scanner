import json
import os
import tempfile
import unittest
from unittest import mock

import requests

import scanner_core as core

VALID_KEY = 'uH1fTd6LVbwkNKs1qlozF15r9fchF/KqtZye1WSLk6E='
VALID_KEY_2 = '9VYFayLDRmYouw8FvUcE9UdDBuzxwbbk2HPMWEh3DmU='


def make_item(name, ip='1.2.3.4', tier=0, status=1, key=VALID_KEY):
    return {
        'Name': name,
        'Tier': tier,
        'Status': status,
        'Servers': [{'EntryIP': ip, 'X25519PublicKey': key}],
    }


def make_server(name='US#1', ip='1.2.3.4', ping=None, wg_key=VALID_KEY, free=True):
    server = {'name': name, 'ip': ip, 'cc': core.country_code(name), 'free': free, 'wg_key': wg_key}
    if ping is not None:
        server.update(ping=ping, proto='TCP:443')
    return server


class CountryCodeTests(unittest.TestCase):
    def test_extracts_two_letter_prefix(self):
        self.assertEqual(core.country_code('US#1'), 'US')
        self.assertEqual(core.country_code('de-free-3'), 'DE')

    def test_unknown_when_no_prefix(self):
        self.assertEqual(core.country_code('1A'), core.UNKNOWN_CC)
        self.assertEqual(core.country_code(''), core.UNKNOWN_CC)


class ExtractServersTests(unittest.TestCase):
    def test_skips_inactive_and_malformed_items(self):
        raw = [
            make_item('US#1'),
            make_item('DE#1', status=0),
            {'Name': 'NL#1', 'Status': 1, 'Servers': []},
            {'Name': 'CH#1', 'Status': 1},
            {'Name': 'FR#1', 'Status': 1, 'Servers': [{'NoIP': True}]},
        ]
        servers = core.extract_servers(raw)
        self.assertEqual([s['name'] for s in servers], ['US#1'])

    def test_reads_tier_and_wireguard_key(self):
        raw = [make_item('US#1', tier=0), make_item('US#2', tier=2, key=VALID_KEY_2)]
        free, paid = core.extract_servers(raw)
        self.assertTrue(free['free'])
        self.assertFalse(paid['free'])
        self.assertEqual(paid['wg_key'], VALID_KEY_2)

    def test_missing_key_becomes_empty_string(self):
        raw = [{'Name': 'US#1', 'Status': 1, 'Servers': [{'EntryIP': '1.1.1.1'}]}]
        self.assertEqual(core.extract_servers(raw)[0]['wg_key'], '')

    def test_handles_none_input(self):
        self.assertEqual(core.extract_servers(None), [])


class FilterTests(unittest.TestCase):
    def setUp(self):
        self.servers = core.extract_servers([
            make_item('US#1', tier=0),
            make_item('US#2', tier=2),
            make_item('DE#1', tier=0),
            make_item('1XYZ', tier=2),
        ])

    def test_tier_filter(self):
        self.assertEqual(len(core.filter_by_tier(self.servers, 'free')), 2)
        self.assertEqual(len(core.filter_by_tier(self.servers, 'paid')), 2)
        self.assertEqual(len(core.filter_by_tier(self.servers, 'all')), 4)

    def test_region_index_counts_and_continents(self):
        index = core.build_region_index(self.servers)
        self.assertEqual(index.cc_counts, {'US': 2, 'DE': 1, core.UNKNOWN_CC: 1})
        self.assertEqual(index.active_map['North America'], ['US'])
        self.assertEqual(index.active_map['Europe'], ['DE'])
        self.assertNotIn('Asia', index.active_map)
        self.assertEqual(index.cont_counts['North America'], 2)

    def test_continent_choices_sorted_by_count(self):
        servers = core.extract_servers([make_item('DE#1'), make_item('DE#2'), make_item('US#1')])
        index = core.build_region_index(servers)
        self.assertEqual(core.continent_choices(index), ['Europe', 'North America'])

    def test_country_choices_exclude_unknown_for_all_continents(self):
        index = core.build_region_index(self.servers)
        choices = core.country_choices(index, core.ALL_CONTINENTS)
        self.assertEqual(choices[0], core.ALL_COUNTRIES)
        self.assertEqual(choices[1], 'United States (US)')
        self.assertNotIn(core.UNKNOWN_CC, choices)
        self.assertEqual(len(choices), 3)

    def test_country_choices_for_one_continent(self):
        index = core.build_region_index(self.servers)
        self.assertEqual(core.country_choices(index, 'Europe'),
                         [core.ALL_COUNTRIES, 'Germany (DE)'])

    def test_label_round_trip(self):
        self.assertEqual(core.cc_from_label(core.label_for_cc('JP')), 'JP')
        self.assertEqual(core.cc_from_label(core.ALL_COUNTRIES), core.ALL_COUNTRIES)
        self.assertEqual(core.cc_from_label(core.UNKNOWN_CC), core.UNKNOWN_CC)
        self.assertEqual(core.label_for_cc(core.UNKNOWN_CC), core.UNKNOWN_CC)

    def test_filter_servers_by_continent_and_country(self):
        index = core.build_region_index(self.servers)
        all_servers = core.filter_servers(self.servers, core.ALL_CONTINENTS, core.ALL_COUNTRIES, index.active_map)
        self.assertEqual(len(all_servers), 4)

        europe = core.filter_servers(self.servers, 'Europe', core.ALL_COUNTRIES, index.active_map)
        self.assertEqual([s['name'] for s in europe], ['DE#1'])

        us = core.filter_servers(self.servers, core.ALL_CONTINENTS, 'US', index.active_map)
        self.assertEqual([s['name'] for s in us], ['US#1', 'US#2'])


class PingTests(unittest.TestCase):
    def test_smart_ping_picks_fastest_probe(self):
        with mock.patch.object(core, '_tcp_rtt', return_value=180), \
                mock.patch.object(core, '_udp_rtt', return_value=120):
            self.assertEqual(core.smart_ping('1.2.3.4'), (120, 'UDP:80'))

    def test_smart_ping_tcp_only(self):
        with mock.patch.object(core, '_tcp_rtt', return_value=150), \
                mock.patch.object(core, '_udp_rtt', return_value=None):
            self.assertEqual(core.smart_ping('1.2.3.4'), (150, 'TCP:443'))

    def test_smart_ping_none_when_both_fail(self):
        with mock.patch.object(core, '_tcp_rtt', return_value=None), \
                mock.patch.object(core, '_udp_rtt', return_value=None):
            self.assertEqual(core.smart_ping('1.2.3.4'), (None, None))

    def test_smart_ping_survives_socket_errors(self):
        with mock.patch.object(core, '_tcp_rtt', side_effect=OSError), \
                mock.patch.object(core, '_udp_rtt', return_value=90):
            self.assertEqual(core.smart_ping('1.2.3.4'), (90, 'UDP:80'))


class ResultsTests(unittest.TestCase):
    def test_top_results_sorted_and_limited(self):
        servers = [make_server(f'S{i}', ping=ms) for i, ms in enumerate([300, 120, 250, 110])]
        top = core.top_results(servers, limit=2)
        self.assertEqual([s['ping'] for s in top], [110, 120])

    def test_merge_results_dedups_by_name_keeping_newest(self):
        old = [make_server('US#1', ping=200)]
        new = [make_server('US#1', ping=150), make_server('DE#1', ping=180)]
        merged = core.merge_results(old, new)
        self.assertEqual(len(merged), 2)
        by_name = {s['name']: s for s in merged}
        self.assertEqual(by_name['US#1']['ping'], 150)


class WireGuardKeyTests(unittest.TestCase):
    def test_valid_key(self):
        self.assertTrue(core.is_valid_wg_key(VALID_KEY))

    def test_invalid_keys(self):
        for bad in ('', None, 'short=', VALID_KEY[:-1], VALID_KEY + 'A', VALID_KEY.replace('=', '!')):
            self.assertFalse(core.is_valid_wg_key(bad), bad)


class WireGuardConfigTests(unittest.TestCase):
    def setUp(self):
        self.server = make_server('US#1', ip='185.159.156.10')

    def test_config_contains_expected_sections(self):
        conf = core.build_wireguard_config(self.server, VALID_KEY_2)
        lines = conf.splitlines()
        self.assertEqual(lines[0], '[Interface]')
        self.assertIn('[Peer]', lines)
        self.assertIn(f'PrivateKey = {VALID_KEY_2}', lines)
        self.assertIn(f'PublicKey = {VALID_KEY}', lines)
        self.assertIn(f'Address = {core.WG_ADDRESS}', lines)
        self.assertIn(f'DNS = {core.WG_DNS}', lines)
        self.assertIn('AllowedIPs = 0.0.0.0/0, ::/0', lines)
        self.assertIn('Endpoint = 185.159.156.10:51820', lines)

    def test_placeholder_used_without_private_key(self):
        conf = core.build_wireguard_config(self.server)
        self.assertIn(f'PrivateKey = {core.PRIVATE_KEY_PLACEHOLDER}', conf.splitlines())

    def test_missing_public_key_raises(self):
        server = make_server('US#1', wg_key='')
        with self.assertRaisesRegex(ValueError, 'کلید عمومی'):
            core.build_wireguard_config(server)

    def test_invalid_public_key_raises(self):
        server = make_server('US#1', wg_key='not-a-key')
        with self.assertRaises(ValueError):
            core.build_wireguard_config(server)

    def test_invalid_private_key_raises(self):
        with self.assertRaisesRegex(ValueError, 'کلید خصوصی'):
            core.build_wireguard_config(self.server, 'nope')

    def test_safe_filename(self):
        self.assertEqual(core.safe_filename('US#1 (Free)'), 'US_1_Free')
        self.assertEqual(core.safe_filename('###'), 'server')


class WireGuardExportTests(unittest.TestCase):
    def test_export_writes_files_and_reports_skipped(self):
        servers = [
            make_server('US#1', ip='10.0.0.1'),
            make_server('DE#1', ip='10.0.0.2', wg_key=''),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, 'wireguard')
            written, skipped = core.export_wireguard_configs(servers, target, VALID_KEY_2)

            self.assertEqual(skipped, ['DE#1'])
            self.assertEqual([os.path.basename(p) for p in written], ['US_1.conf'])
            with open(written[0], encoding='utf-8') as f:
                content = f.read()
            self.assertIn('Endpoint = 10.0.0.1:51820', content)
            self.assertIn(f'PrivateKey = {VALID_KEY_2}', content)
            self.assertNotIn('\r', content)

    def test_export_with_no_servers_creates_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            written, skipped = core.export_wireguard_configs([], os.path.join(tmp, 'x'))
            self.assertEqual((written, skipped), ([], []))


class DownloadTests(unittest.TestCase):
    def test_falls_back_to_next_mirror(self):
        good = mock.Mock(status_code=200)
        good.json.return_value = {'LogicalServers': [make_item('US#1')]}
        responses = [requests.ConnectionError('boom'), good]

        def fake_get(url, timeout):
            result = responses.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        with mock.patch.object(core.requests, 'get', side_effect=fake_get):
            data = core.download_database(['https://a', 'https://b'])
        self.assertEqual(data, [make_item('US#1')])

    def test_bad_status_and_bad_json_are_skipped(self):
        bad_status = mock.Mock(status_code=500)
        bad_json = mock.Mock(status_code=200)
        bad_json.json.side_effect = ValueError('not json')
        with mock.patch.object(core.requests, 'get', side_effect=[bad_status, bad_json]):
            self.assertIsNone(core.download_database(['https://a', 'https://b']))

    def test_plain_list_payload_is_returned_as_is(self):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = [make_item('US#1')]
        with mock.patch.object(core.requests, 'get', return_value=resp):
            self.assertEqual(core.download_database(['https://a']), [make_item('US#1')])


class LoadDatabaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cache = os.path.join(self._tmp.name, 'cache.json')
        self.data = [make_item('US#1')]

    def tearDown(self):
        self._tmp.cleanup()

    def write_cache(self, age_s):
        with open(self.cache, 'w', encoding='utf-8') as f:
            json.dump(self.data, f)
        mtime = os.path.getmtime(self.cache)
        os.utime(self.cache, (mtime - age_s, mtime - age_s))

    def test_fresh_cache_skips_network(self):
        self.write_cache(age_s=10)
        with mock.patch.object(core, 'download_database') as dl:
            data, source = core.load_database(self.cache, max_age=3600)
        dl.assert_not_called()
        self.assertEqual((data, source), (self.data, 'cache'))

    def test_network_used_and_cache_written_when_no_cache(self):
        with mock.patch.object(core, 'download_database', return_value=self.data):
            data, source = core.load_database(self.cache)
        self.assertEqual((data, source), (self.data, 'network'))
        self.assertEqual(core._read_cache(self.cache), self.data)

    def test_zero_max_age_forces_network_even_with_fresh_cache(self):
        self.write_cache(age_s=10)
        fresh = [make_item('DE#9')]
        with mock.patch.object(core, 'download_database', return_value=fresh) as dl:
            data, source = core.load_database(self.cache, max_age=0)
        dl.assert_called_once()
        self.assertEqual((data, source), (fresh, 'network'))
        self.assertEqual(core._read_cache(self.cache), fresh)

    def test_stale_cache_used_when_network_fails(self):
        self.write_cache(age_s=7200)
        with mock.patch.object(core, 'download_database', return_value=None):
            data, source = core.load_database(self.cache, max_age=3600)
        self.assertEqual((data, source), (self.data, 'stale-cache'))

    def test_error_when_nothing_available(self):
        with mock.patch.object(core, 'download_database', return_value=None):
            self.assertEqual(core.load_database(self.cache), (None, 'error'))

    def test_corrupted_fresh_cache_falls_back_to_network(self):
        with open(self.cache, 'w', encoding='utf-8') as f:
            f.write('{not json')
        with mock.patch.object(core, 'download_database', return_value=self.data):
            data, source = core.load_database(self.cache)
        self.assertEqual((data, source), (self.data, 'network'))


AWG_BLOCK = """
Jc = 4
Jmin = 50
Jmax = 1000
S1 = 0
S2 = 0
H1 = 1
H2 = 2
H3 = 3
H4 = 4
"""


class AmneziaWGParseTests(unittest.TestCase):
    def test_empty_text_means_plain_wireguard(self):
        self.assertIsNone(core.parse_obfuscation(''))
        self.assertIsNone(core.parse_obfuscation('   \n  '))

    def test_parses_full_block(self):
        params = core.parse_obfuscation(AWG_BLOCK)
        self.assertEqual(params, {'Jc': 4, 'Jmin': 50, 'Jmax': 1000, 'S1': 0, 'S2': 0,
                                  'H1': '1', 'H2': '2', 'H3': '3', 'H4': '4'})

    def test_default_block_round_trips(self):
        text = core.format_obfuscation(core.DEFAULT_OBFUSCATION)
        params = core.parse_obfuscation(text)
        expected = {k: str(v) if k.startswith('H') else v for k, v in core.DEFAULT_OBFUSCATION.items()}
        self.assertEqual(params, expected)

    def test_ignores_comments_and_blank_lines(self):
        text = '# Bouncing = 0\n\n' + AWG_BLOCK.replace('Jc = 4', 'Jc = 4  # junk count')
        self.assertEqual(core.parse_obfuscation(text)['Jc'], 4)

    def test_unknown_key_is_rejected_without_echoing_value(self):
        with self.assertRaisesRegex(ValueError, 'خط') as ctx:
            core.parse_obfuscation(AWG_BLOCK + 'PrivateKey = SECRETVALUE\n')
        self.assertNotIn('SECRETVALUE', str(ctx.exception))
        self.assertNotIn('PrivateKey', str(ctx.exception))

    def test_bare_private_key_line_is_not_echoed(self):
        # کلید خصوصی بدون نام کلید: قبلاً بخشی از آن در پیام خطا برمی‌گشت
        with self.assertRaises(ValueError) as ctx:
            core.parse_obfuscation(VALID_KEY + '\n' + AWG_BLOCK)
        self.assertNotIn(VALID_KEY, str(ctx.exception))
        self.assertNotIn(VALID_KEY[:-1], str(ctx.exception))

    def test_duplicate_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'تکراری'):
            core.parse_obfuscation(AWG_BLOCK + 'Jc = 99\n')

    def test_newer_amneziawg_keys_are_reported_as_unsupported(self):
        with self.assertRaisesRegex(ValueError, 'پشتیبانی‌نشده'):
            core.parse_obfuscation(AWG_BLOCK + 'S3 = 5\n')

    def test_h_range_is_accepted_and_kept(self):
        params = core.parse_obfuscation(AWG_BLOCK.replace('H1 = 1', 'H1 = 100-200'))
        self.assertEqual(params['H1'], '100-200')

    def test_h_value_above_uint32_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'H1'):
            core.parse_obfuscation(AWG_BLOCK.replace('H1 = 1', 'H1 = 99999999999'))

    def test_h_range_with_low_above_high_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'H2'):
            core.parse_obfuscation(AWG_BLOCK.replace('H2 = 2', 'H2 = 9-3'))

    def test_missing_s1_s2_default_to_zero(self):
        text = AWG_BLOCK.replace('S1 = 0', '').replace('S2 = 0', '')
        params = core.parse_obfuscation(text)
        self.assertEqual((params['S1'], params['S2']), (0, 0))

    def test_missing_keys_are_named(self):
        text = AWG_BLOCK.replace('H4 = 4', '')
        with self.assertRaisesRegex(ValueError, 'H4'):
            core.parse_obfuscation(text)

    def test_non_integer_value_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Jc'):
            core.parse_obfuscation(AWG_BLOCK.replace('Jc = 4', 'Jc = four'))

    def test_negative_value_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'S1'):
            core.parse_obfuscation(AWG_BLOCK.replace('S1 = 0', 'S1 = -1'))

    def test_jmin_greater_than_jmax_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Jmin'):
            core.parse_obfuscation(AWG_BLOCK.replace('Jmax = 1000', 'Jmax = 10'))

    def test_line_without_equals_is_rejected(self):
        with self.assertRaises(ValueError):
            core.parse_obfuscation(AWG_BLOCK + 'garbage\n')


class AmneziaWGConfigTests(unittest.TestCase):
    def test_server_ip_with_newline_is_rejected(self):
        # IP بدون اعتبارسنجی وارد فایل می‌شد و می‌توانست خط PostUp تزریق کند
        server = make_server('US#1', ip='1.2.3.4\nPostUp = echo injected')
        with self.assertRaisesRegex(ValueError, 'IP'):
            core.build_wireguard_config(server, VALID_KEY_2)

    def setUp(self):
        self.server = make_server('US#1', ip='185.159.156.10')
        self.params = core.parse_obfuscation(AWG_BLOCK)

    def test_obfuscation_lines_are_in_interface_section(self):
        conf = core.build_wireguard_config(self.server, VALID_KEY_2, obfuscation=self.params)
        lines = conf.splitlines()
        peer_index = lines.index('[Peer]')
        interface = lines[:peer_index]
        for key in core.AWG_KEYS:
            self.assertIn(f'{key} = {self.params[key]}', interface)

    def test_plain_wireguard_has_no_obfuscation_lines(self):
        conf_lines = core.build_wireguard_config(self.server, VALID_KEY_2).splitlines()
        for key in core.AWG_KEYS:
            self.assertFalse(any(line.startswith(f'{key} =') for line in conf_lines), key)

    def test_persistent_keepalive_present_in_both_modes(self):
        plain = core.build_wireguard_config(self.server, VALID_KEY_2)
        awg = core.build_wireguard_config(self.server, VALID_KEY_2, obfuscation=self.params)
        for conf in (plain, awg):
            self.assertIn('PersistentKeepalive = 25', conf.splitlines())

    def test_awg_export_uses_suffix_and_keeps_wireguard_default_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            awg_path = core.write_wireguard_config(self.server, tmp, VALID_KEY_2, self.params)
            plain_path = core.write_wireguard_config(self.server, tmp, VALID_KEY_2)
            self.assertEqual(os.path.basename(awg_path), 'US_1_awg.conf')
            self.assertEqual(os.path.basename(plain_path), 'US_1.conf')
            with open(awg_path, encoding='utf-8') as f:
                self.assertIn('Jc = 4', f.read())


if __name__ == '__main__':
    unittest.main()
