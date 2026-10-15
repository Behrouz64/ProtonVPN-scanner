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
            'good.prod.surfshark.com': {'ips': ['45.83.64.1', 'not-an-ip', '45.83.64.1'], 'at': NOW},
            'no-time.prod.surfshark.com': {'ips': ['45.83.64.2']},
            'bool-time.prod.surfshark.com': {'ips': ['45.83.64.3'], 'at': True},
            'not-a-dict.prod.surfshark.com': ['45.83.64.4'],
        }}
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(payload, f)
        cache = surfshark_ips.load_cache(self.path)
        self.assertEqual(list(cache), ['good.prod.surfshark.com'])
        self.assertEqual(cache['good.prod.surfshark.com']['ips'], ['45.83.64.1'])

    def test_save_then_load_round_trip(self):
        entries = {'a.prod.surfshark.com': {'ips': ['45.83.64.1', '45.83.64.2'], 'at': NOW}}
        surfshark_ips.save_cache(self.path, entries)
        self.assertEqual(surfshark_ips.load_cache(self.path), entries)
        self.assertFalse(os.path.exists(self.path + '.tmp'))

    def test_saved_file_holds_no_secrets(self):
        surfshark_ips.save_cache(self.path, {'a.prod.surfshark.com': {'ips': ['45.83.64.1'], 'at': NOW}})
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
                json.dump({'hosts': {'a.prod.surfshark.com': ['45.83.64.9', 'bad', 7, '45.83.64.9']}}, f)
            self.assertEqual(surfshark_ips.load_bundled(path), {'a.prod.surfshark.com': ['45.83.64.9']})


class FreshnessTests(unittest.TestCase):
    def test_entry_is_fresh_within_ttl_only(self):
        cache = {'h': {'ips': ['45.83.64.1'], 'at': NOW}}
        self.assertEqual(surfshark_ips.fresh_ips(cache, 'h', NOW + 60), ['45.83.64.1'])
        self.assertEqual(surfshark_ips.fresh_ips(cache, 'h', NOW + surfshark_ips.CACHE_TTL_S), ['45.83.64.1'])
        self.assertEqual(surfshark_ips.fresh_ips(cache, 'h', NOW + surfshark_ips.CACHE_TTL_S + 1), [])

    def test_future_timestamp_counts_as_stale(self):
        cache = {'h': {'ips': ['45.83.64.1'], 'at': NOW + 500}}
        self.assertEqual(surfshark_ips.fresh_ips(cache, 'h', NOW), [])

    def test_unknown_host_has_no_ips(self):
        self.assertEqual(surfshark_ips.fresh_ips({}, 'h', NOW), [])


class RefreshTests(unittest.TestCase):
    def test_refresh_splits_resolved_and_failed_hosts(self):
        answers = {'a': ['45.83.64.1', '45.83.64.2', '45.83.64.3'], 'b': []}

        def resolver(host, limit):
            return answers[host][:limit]

        fresh, failed = surfshark_ips.refresh(['a', 'b'], resolver, NOW, 2)
        self.assertEqual(fresh, {'a': {'ips': ['45.83.64.1', '45.83.64.2'], 'at': NOW}})
        self.assertEqual(failed, ['b'])

    def test_failed_host_keeps_its_older_entry(self):
        old = {'b': {'ips': ['45.83.64.5'], 'at': NOW - 10}}
        merged = surfshark_ips.merge_cache(old, {'a': {'ips': ['45.83.64.1'], 'at': NOW}})
        self.assertEqual(merged['b'], old['b'])
        self.assertEqual(merged['a']['ips'], ['45.83.64.1'])


class PublicAddressTests(unittest.TestCase):
    def test_only_public_ipv4_is_accepted(self):
        self.assertTrue(surfshark_ips.is_public_ipv4('45.83.64.1'))
        for value in ('10.10.34.34', '192.168.1.1', '127.0.0.1', '0.0.0.0', '100.64.0.1', 'example.com', '', 7):
            with self.subTest(value=value):
                self.assertFalse(surfshark_ips.is_public_ipv4(value))


class IpSourceOrderTests(unittest.TestCase):
    def setUp(self):
        self.calls = []

    def resolver(self, host, limit):
        self.calls.append(host)
        return ['91.108.56.1', '91.108.56.2', '91.108.56.3', '10.10.34.34']

    def test_stored_and_live_ips_are_both_candidates(self):
        cache = {'h': {'ips': ['45.83.64.1', '45.83.64.2'], 'at': NOW}}
        source = surfshark_ips.ip_source(cache, {'h': ['45.83.64.9']}, self.resolver, NOW, 4)
        self.assertEqual(source('h'), ['45.83.64.1', '45.83.64.2', '91.108.56.1', '91.108.56.2', '91.108.56.3'])
        self.assertEqual(self.calls, ['h'])

    def test_bundled_is_used_when_cache_is_stale(self):
        cache = {'h': {'ips': ['45.83.64.1'], 'at': NOW - surfshark_ips.CACHE_TTL_S - 5}}
        source = surfshark_ips.ip_source(cache, {'h': ['45.83.64.9']}, self.resolver, NOW, 1)
        self.assertEqual(source('h'), ['45.83.64.9', '91.108.56.1'])

    def test_poisoned_cache_does_not_hide_live_answers(self):
        cache = {'h': {'ips': ['45.83.64.7'], 'at': NOW}}
        source = surfshark_ips.ip_source(cache, {}, self.resolver, NOW, 2)
        self.assertEqual(source('h'), ['45.83.64.7', '91.108.56.1', '91.108.56.2'])

    def test_private_stored_entries_are_ignored(self):
        cache = {'h': {'ips': ['10.10.34.34'], 'at': NOW}}
        source = surfshark_ips.ip_source(cache, {}, self.resolver, NOW, 1)
        self.assertEqual(source('h'), ['91.108.56.1'])

    def test_limit_applies_to_each_source(self):
        cache = {'h': {'ips': ['45.83.64.1', '45.83.64.2', '45.83.64.3'], 'at': NOW}}
        source = surfshark_ips.ip_source(cache, {}, self.resolver, NOW, 2)
        self.assertEqual(source('h'), ['45.83.64.1', '45.83.64.2', '91.108.56.1', '91.108.56.2'])

    def test_private_live_answers_are_dropped(self):
        source = surfshark_ips.ip_source({}, {}, lambda host, limit: ['10.10.34.34', '127.0.0.1'], NOW, 4)
        self.assertEqual(source('h'), [])


if __name__ == '__main__':
    unittest.main()
