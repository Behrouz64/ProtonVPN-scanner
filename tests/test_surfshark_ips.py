import json
import os
import tempfile
import unittest

import surfshark_ips

NOW = 1_000_000


class CacheFileTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, 'sub', 'surfshark_ips.json')

    def tearDown(self):
        self.dir.cleanup()

    def test_missing_file_is_an_empty_cache(self):
        self.assertEqual(surfshark_ips.load_cache(self.path), {})

    def test_corrupt_file_is_an_empty_cache(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write('{not json')
        self.assertEqual(surfshark_ips.load_cache(self.path), {})

    def test_bad_entries_are_dropped_and_ips_validated(self):
        os.makedirs(os.path.dirname(self.path))
        payload = {'hosts': {
            'good.prod.surfshark.com': {'ips': ['198.51.100.1', 'not-an-ip', '198.51.100.1'], 'at': NOW},
            'no-time.prod.surfshark.com': {'ips': ['198.51.100.2']},
            'bool-time.prod.surfshark.com': {'ips': ['198.51.100.3'], 'at': True},
            'not-a-dict.prod.surfshark.com': ['198.51.100.4'],
        }}
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(payload, f)
        cache = surfshark_ips.load_cache(self.path)
        self.assertEqual(list(cache), ['good.prod.surfshark.com'])
        self.assertEqual(cache['good.prod.surfshark.com']['ips'], ['198.51.100.1'])

    def test_save_then_load_round_trip(self):
        entries = {'a.prod.surfshark.com': {'ips': ['198.51.100.1', '198.51.100.2'], 'at': NOW}}
        surfshark_ips.save_cache(self.path, entries)
        self.assertEqual(surfshark_ips.load_cache(self.path), entries)
        self.assertFalse(os.path.exists(self.path + '.tmp'))

    def test_saved_file_holds_no_secrets(self):
        surfshark_ips.save_cache(self.path, {'a.prod.surfshark.com': {'ips': ['198.51.100.1'], 'at': NOW}})
        with open(self.path, encoding='utf-8') as f:
            text = f.read()
        for word in ('private', 'PrivateKey', 'address', 'dns', 'user_interface'):
            self.assertNotIn(word, text)


class BundledListTests(unittest.TestCase):
    def test_missing_bundled_file_is_empty(self):
        self.assertEqual(surfshark_ips.load_bundled('/nonexistent/ips.json'), {})

    def test_bundled_ips_are_validated(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'ips.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'hosts': {'a.prod.surfshark.com': ['198.51.100.9', 'bad', 7, '198.51.100.9']}}, f)
            self.assertEqual(surfshark_ips.load_bundled(path), {'a.prod.surfshark.com': ['198.51.100.9']})


class FreshnessTests(unittest.TestCase):
    def test_entry_is_fresh_within_ttl_only(self):
        cache = {'h': {'ips': ['198.51.100.1'], 'at': NOW}}
        self.assertEqual(surfshark_ips.fresh_ips(cache, 'h', NOW + 60), ['198.51.100.1'])
        self.assertEqual(surfshark_ips.fresh_ips(cache, 'h', NOW + surfshark_ips.CACHE_TTL_S), ['198.51.100.1'])
        self.assertEqual(surfshark_ips.fresh_ips(cache, 'h', NOW + surfshark_ips.CACHE_TTL_S + 1), [])

    def test_future_timestamp_counts_as_stale(self):
        cache = {'h': {'ips': ['198.51.100.1'], 'at': NOW + 500}}
        self.assertEqual(surfshark_ips.fresh_ips(cache, 'h', NOW), [])

    def test_unknown_host_has_no_ips(self):
        self.assertEqual(surfshark_ips.fresh_ips({}, 'h', NOW), [])


class RefreshTests(unittest.TestCase):
    def test_refresh_splits_resolved_and_failed_hosts(self):
        answers = {'a': ['198.51.100.1', '198.51.100.2', '198.51.100.3'], 'b': []}

        def resolver(host, limit):
            return answers[host][:limit]

        fresh, failed = surfshark_ips.refresh(['a', 'b'], resolver, NOW, 2)
        self.assertEqual(fresh, {'a': {'ips': ['198.51.100.1', '198.51.100.2'], 'at': NOW}})
        self.assertEqual(failed, ['b'])

    def test_failed_host_keeps_its_older_entry(self):
        old = {'b': {'ips': ['198.51.100.5'], 'at': NOW - 10}}
        merged = surfshark_ips.merge_cache(old, {'a': {'ips': ['198.51.100.1'], 'at': NOW}})
        self.assertEqual(merged['b'], old['b'])
        self.assertEqual(merged['a']['ips'], ['198.51.100.1'])


class IpSourceOrderTests(unittest.TestCase):
    def setUp(self):
        self.calls = []

    def resolver(self, host, limit):
        self.calls.append(host)
        return ['203.0.113.1', '203.0.113.2', '203.0.113.3']

    def test_fresh_cache_wins_over_bundled_and_dns(self):
        cache = {'h': {'ips': ['198.51.100.1', '198.51.100.2'], 'at': NOW}}
        source = surfshark_ips.ip_source(cache, {'h': ['198.51.100.9']}, self.resolver, NOW, 4)
        self.assertEqual(source('h'), ['198.51.100.1', '198.51.100.2'])
        self.assertEqual(self.calls, [])

    def test_stale_cache_falls_back_to_bundled_then_dns(self):
        cache = {'h': {'ips': ['198.51.100.1'], 'at': NOW - surfshark_ips.CACHE_TTL_S - 5}}
        source = surfshark_ips.ip_source(cache, {'h': ['198.51.100.9']}, self.resolver, NOW, 4)
        self.assertEqual(source('h'), ['198.51.100.9'])
        self.assertEqual(self.calls, [])
        source_without_bundle = surfshark_ips.ip_source(cache, {}, self.resolver, NOW, 4)
        self.assertEqual(source_without_bundle('h'), ['203.0.113.1', '203.0.113.2', '203.0.113.3'])
        self.assertEqual(self.calls, ['h'])

    def test_limit_applies_to_every_source(self):
        cache = {'h': {'ips': ['198.51.100.1', '198.51.100.2', '198.51.100.3'], 'at': NOW}}
        self.assertEqual(surfshark_ips.ip_source(cache, {}, self.resolver, NOW, 2)('h'),
                         ['198.51.100.1', '198.51.100.2'])
        self.assertEqual(surfshark_ips.ip_source({}, {}, self.resolver, NOW, 1)('h'), ['203.0.113.1'])


if __name__ == '__main__':
    unittest.main()
