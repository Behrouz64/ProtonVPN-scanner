import json
import os
import tempfile
import unittest
from unittest import mock
from urllib.parse import parse_qsl, unquote, urlsplit

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

    def test_merge_results_keeps_newest_for_same_host(self):
        old = [make_server('US#1', ip='10.1.1.1', ping=200)]
        new = [make_server('US#1', ip='10.1.1.1', ping=150), make_server('DE#1', ip='10.1.1.2', ping=180)]
        merged = core.merge_results(old, new)
        self.assertEqual(len(merged), 2)
        by_name = {s['name']: s for s in merged}
        self.assertEqual(by_name['US#1']['ping'], 150)

    def test_merge_results_does_not_duplicate_one_host_under_two_names(self):
        # حالت باگ: همان میزبان از حالت FREE با نام RO-FREE#13 و از ALL با نام RO#9 آمده
        old = [make_server('RO-FREE#13', ip='10.9.9.9', ping=150)]
        new = [make_server('RO#9', ip='10.9.9.9', ping=160)]
        merged = core.merge_results(old, new)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]['name'], 'RO#9')


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
        with self.assertRaises(core.ConfigError) as ctx:
            core.build_wireguard_config(server)
        self.assertEqual(ctx.exception.code, 'no_public_key')

    def test_invalid_public_key_raises(self):
        server = make_server('US#1', wg_key='not-a-key')
        with self.assertRaises(core.ConfigError) as ctx:
            core.build_wireguard_config(server)
        self.assertEqual(ctx.exception.code, 'bad_public_key')

    def test_invalid_private_key_raises(self):
        with self.assertRaises(core.ConfigError) as ctx:
            core.build_wireguard_config(self.server, 'nope')
        self.assertEqual(ctx.exception.code, 'bad_private_key')

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


class AmneziaWGCheckTests(unittest.TestCase):
    """فرم تنظیمات AmneziaWG: مقادیر پیش‌فرض، نرمال‌سازی و کدهای خطا (بدون متن ورودی)."""

    def values(self, **changes):
        return {**core.DEFAULT_OBFUSCATION, **changes}

    def test_defaults_are_valid_and_normalized(self):
        params, errors = core.check_obfuscation(core.DEFAULT_OBFUSCATION)
        self.assertEqual(errors, {})
        self.assertEqual(params, {'Jc': 4, 'Jmin': 50, 'Jmax': 1000, 'S1': 0, 'S2': 0,
                                  'H1': '1', 'H2': '2', 'H3': '3', 'H4': '4'})

    def test_text_numbers_are_accepted(self):
        params, errors = core.check_obfuscation(self.values(Jc=' 7 ', S1='3'))
        self.assertEqual(errors, {})
        self.assertEqual((params['Jc'], params['S1']), (7, 3))

    def test_persian_digits_are_accepted(self):
        params, errors = core.check_obfuscation(self.values(Jc='۷'))
        self.assertEqual((errors, params['Jc']), ({}, 7))

    def test_non_integer_is_reported_by_key(self):
        _, errors = core.check_obfuscation(self.values(Jc='four'))
        self.assertEqual(errors, {'Jc': 'number'})

    def test_negative_value_is_reported(self):
        _, errors = core.check_obfuscation(self.values(S1='-1'))
        self.assertEqual(errors, {'S1': 'number'})

    def test_h_range_is_kept(self):
        params, errors = core.check_obfuscation(self.values(H1='100-200'))
        self.assertEqual((errors, params['H1']), ({}, '100-200'))

    def test_h_above_uint32_is_range_error(self):
        _, errors = core.check_obfuscation(self.values(H1='99999999999'))
        self.assertEqual(errors, {'H1': 'range'})

    def test_h_range_with_low_above_high_is_range_error(self):
        _, errors = core.check_obfuscation(self.values(H2='9-3'))
        self.assertEqual(errors, {'H2': 'range'})

    def test_jmin_above_jmax_is_order_error(self):
        _, errors = core.check_obfuscation(self.values(Jmax=10))
        self.assertEqual(errors, {'Jmin': 'order'})

    def test_empty_field_is_reported(self):
        _, errors = core.check_obfuscation(self.values(H4=''))
        self.assertEqual(errors, {'H4': 'range'})

    def test_error_report_never_contains_the_input(self):
        # کاربر ممکن است کلید خصوصی را در یک فیلد بچسباند؛ گزارش خطا فقط کد دارد
        _, errors = core.check_obfuscation(self.values(Jc=VALID_KEY))
        self.assertEqual(errors, {'Jc': 'number'})
        self.assertNotIn(VALID_KEY, str(errors))


class QrCellTests(unittest.TestCase):
    """هندسه‌ی QR بدون نیاز به بسته‌ی qrcode: مربع‌ها باید درون بوم و با اندازه‌ی صحیح باشند."""

    def test_one_rect_per_dark_module_with_integer_cells(self):
        matrix = [[True, False, True], [False, True, False], [True, False, True]]
        cell, rects = core.qr_cells(matrix, 30)
        self.assertEqual(cell, 10)
        self.assertEqual(len(rects), 5)
        self.assertTrue(all(size == cell for _, _, size in rects))

    def test_rects_stay_inside_the_square_canvas(self):
        matrix = [[(row + col) % 2 == 0 for col in range(25)] for row in range(25)]
        side = 280
        cell, rects = core.qr_cells(matrix, side)
        for x, y, size in rects:
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x + size, side)
            self.assertLessEqual(y + size, side)

    def test_code_is_centered_when_side_is_not_a_multiple(self):
        matrix = [[True] * 33 for _ in range(33)]
        cell, rects = core.qr_cells(matrix, 280)
        drawn = cell * 33
        xs = [x for x, _, _ in rects]
        self.assertEqual(min(xs), (280 - drawn) // 2)
        self.assertEqual(max(xs) + cell, (280 - drawn) // 2 + drawn)

    def test_row_zero_is_drawn_at_the_top(self):
        matrix = [[True, True], [False, False]]
        _, rects = core.qr_cells(matrix, 20)
        self.assertEqual(min(y for _, y, _ in rects), 0)


class AmneziaWGConfigTests(unittest.TestCase):
    def test_server_ip_with_newline_is_rejected(self):
        # IP بدون اعتبارسنجی وارد فایل می‌شد و می‌توانست خط PostUp تزریق کند
        server = make_server('US#1', ip='1.2.3.4\nPostUp = echo injected')
        with self.assertRaises(core.ConfigError) as ctx:
            core.build_wireguard_config(server, VALID_KEY_2)
        self.assertEqual(ctx.exception.code, 'bad_ip')

    def setUp(self):
        self.server = make_server('US#1', ip='185.159.156.10')
        self.params = core.check_obfuscation(core.DEFAULT_OBFUSCATION)[0]

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



class DedupeEndpointTests(unittest.TestCase):
    def test_same_ip_and_key_merge_into_one_with_aliases(self):
        servers = [
            make_server('RO#1', ip='10.0.0.1'),
            make_server('RO#2', ip='10.0.0.1'),
            make_server('RO#3', ip='10.0.0.1'),
        ]
        merged = core.dedupe_endpoints(servers)
        self.assertEqual([s['name'] for s in merged], ['RO#1'])
        self.assertEqual(merged[0]['aliases'], ['RO#2', 'RO#3'])

    def test_same_ip_different_key_stays_separate(self):
        servers = [
            make_server('RO#1', ip='10.0.0.1', wg_key=VALID_KEY),
            make_server('RO#2', ip='10.0.0.1', wg_key=VALID_KEY_2),
        ]
        self.assertEqual(len(core.dedupe_endpoints(servers)), 2)

    def test_order_and_distinct_hosts_are_kept(self):
        servers = [make_server('DE#1', ip='10.0.0.2'), make_server('FR#1', ip='10.0.0.3'),
                   make_server('DE#2', ip='10.0.0.2')]
        merged = core.dedupe_endpoints(servers)
        self.assertEqual([s['name'] for s in merged], ['DE#1', 'FR#1'])
        self.assertEqual(merged[0]['aliases'], ['DE#2'])
        self.assertEqual(merged[1]['aliases'], [])

    def test_empty_input(self):
        self.assertEqual(core.dedupe_endpoints([]), [])

    def test_tier_filter_before_dedupe_keeps_tiers_apart(self):
        raw = [make_item('RO#1', ip='10.0.0.9', tier=0), make_item('RO#2', ip='10.0.0.9', tier=2)]
        servers = core.extract_servers(raw)
        free = core.dedupe_endpoints(core.filter_by_tier(servers, 'free'))
        paid = core.dedupe_endpoints(core.filter_by_tier(servers, 'paid'))
        self.assertEqual([s['name'] for s in free], ['RO#1'])
        self.assertEqual([s['name'] for s in paid], ['RO#2'])


def parse_wg_link(link):
    """تجزیه‌ی لینک wg:// به همان شکلی که کلاینت‌ها می‌خوانند (query + fragment)."""
    parts = urlsplit(link)
    params = dict(parse_qsl(parts.query, keep_blank_values=True))
    if 'obfsParam' in params:
        params['obfsParam'] = json.loads(params['obfsParam'])
    return {'host': parts.hostname, 'port': parts.port, 'label': unquote(parts.fragment), **params}


class WgLinkTests(unittest.TestCase):
    def setUp(self):
        self.server = {'name': 'AL#48', 'ip': '203.0.113.7', 'cc': 'AL', 'city': 'Tirana', 'wg_key': VALID_KEY_2}
        self.params = core.check_obfuscation(core.DEFAULT_OBFUSCATION)[0]

    def test_link_has_endpoint_and_key_parameters(self):
        link = core.build_wg_link(self.server, VALID_KEY, obfuscation=self.params)
        self.assertTrue(link.startswith('wg://203.0.113.7:51820?'))
        info = parse_wg_link(link)
        self.assertEqual(info['publicKey'], VALID_KEY_2)
        self.assertEqual(info['privateKey'], VALID_KEY)
        self.assertEqual(info['ip'], '10.2.0.2')
        self.assertEqual(info['dns'], core.WG_DNS)
        self.assertEqual((info['mtu'], info['udp'], info['keepalive']), ('1280', '1', '25'))

    def test_obfuscation_is_sent_as_json_with_lowercase_keys(self):
        info = parse_wg_link(core.build_wg_link(self.server, VALID_KEY, obfuscation=self.params))
        self.assertEqual(info['obfs'], 'amneziawg')
        self.assertEqual(info['obfsParam'], {'jc': '4', 'jmin': '50', 'jmax': '1000', 's1': '0', 's2': '0',
                                             'h1': '1', 'h2': '2', 'h3': '3', 'h4': '4'})

    def test_plain_wireguard_link_has_no_obfs(self):
        info = parse_wg_link(core.build_wg_link(self.server, VALID_KEY))
        self.assertNotIn('obfs', info)
        self.assertNotIn('obfsParam', info)

    def test_label_has_flag_country_city_and_ip(self):
        info = parse_wg_link(core.build_wg_link(self.server, VALID_KEY))
        self.assertEqual(info['label'], '\U0001F1E6\U0001F1F1 Albania — Tirana (203.0.113.7)')

    def test_uk_uses_gb_flag(self):
        self.assertEqual(core.country_flag('UK'), '\U0001F1EC\U0001F1E7')
        self.assertEqual(core.country_flag('UNK'), '')

    def test_label_without_city_uses_country_only(self):
        server = {**self.server, 'city': ''}
        self.assertEqual(core.server_label(server), '\U0001F1E6\U0001F1F1 Albania (203.0.113.7)')

    def test_keys_keep_slash_and_encode_plus_and_equals(self):
        key = '+/+/Pvv/vz77/78++/+/Pvv/vz77/78++/+/Pvv/vz4='
        link = core.build_wg_link(self.server, key)
        self.assertIn('privateKey=' + key.replace('+', '%2B').replace('=', '%3D'), link)
        self.assertEqual(parse_wg_link(link)['privateKey'], key)

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            core.build_wg_link(self.server, 'short')
        with self.assertRaises(ValueError):
            core.build_wg_link({**self.server, 'wg_key': ''}, VALID_KEY)
        with self.assertRaises(ValueError):
            core.build_wg_link({**self.server, 'ip': 'not-an-ip'}, VALID_KEY)


@unittest.skipUnless(core.qr_available(), 'qrcode is not installed')
class QrMatrixTests(unittest.TestCase):
    def test_matrix_is_square_with_dark_modules(self):
        matrix = core.qr_matrix(build_config_text())
        self.assertEqual(len(matrix), len(matrix[0]))
        self.assertTrue(any(any(row) for row in matrix))
        self.assertFalse(any(matrix[0]))  # حاشیه‌ی سفید

    def test_unavailable_package_raises(self):
        with mock.patch.object(core, 'qrcode', None):
            with self.assertRaises(RuntimeError):
                core.qr_matrix('x')


def build_config_text():
    server = make_server('US#1', ip='185.159.156.10')
    return core.build_wireguard_config(server, VALID_KEY_2)

if __name__ == '__main__':
    unittest.main()
