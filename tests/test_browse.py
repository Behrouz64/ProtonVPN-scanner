import unittest

import scanner_core as core

CATALOG = core.load_surfshark_catalog(core.SURFSHARK_CATALOG_FILE)


def proton(name, ip, key):
    return {'name': name, 'ip': ip, 'cc': 'DE', 'wg_key': key, 'provider': core.PROVIDER_PROTON}


class EndpointIdTests(unittest.TestCase):
    def test_scanned_surfshark_server_keeps_the_identity_of_its_catalog_entry(self):
        catalog = CATALOG[0]
        scanned = {**catalog, 'ip': '45.83.64.7', 'ping': 33, 'proto': 'UDP:51820'}
        self.assertEqual(core.endpoint_id(catalog), core.endpoint_id(scanned))

    def test_proton_identity_uses_its_ip(self):
        server = proton('DE#1', '203.0.113.1', 'K' * 43 + '=')
        self.assertEqual(core.endpoint_id(server)[1], '203.0.113.1')

    def test_different_surfshark_hosts_have_different_identities(self):
        self.assertEqual(len({core.endpoint_id(s) for s in CATALOG}), len(CATALOG))


class BrowseOrderTests(unittest.TestCase):
    def setUp(self):
        self.a, self.b, self.c, self.d = CATALOG[:4]

    def scanned(self, server, ping):
        return {**server, 'ip': '45.83.64.%d' % (ping % 200 + 1), 'ping': ping, 'proto': 'UDP:51820'}

    def test_replies_come_first_ordered_by_ping(self):
        alive = [self.scanned(self.c, 80), self.scanned(self.a, 20)]
        rows = core.browse_order([self.a, self.b, self.c, self.d], alive, set())
        self.assertEqual([state for state, _ in rows],
                         [core.STATE_ALIVE, core.STATE_ALIVE, core.STATE_UNTESTED, core.STATE_UNTESTED])
        self.assertEqual([s['ping'] for _, s in rows[:2]], [20, 80])

    def test_tested_but_silent_servers_come_before_untested(self):
        rows = core.browse_order([self.a, self.b, self.c], [], {core.endpoint_id(self.c)})
        self.assertEqual([state for state, _ in rows],
                         [core.STATE_NO_REPLY, core.STATE_UNTESTED, core.STATE_UNTESTED])
        self.assertIs(rows[0][1], self.c)

    def test_list_order_is_kept_inside_a_group(self):
        rows = core.browse_order([self.d, self.b, self.a], [], set())
        self.assertEqual([s['name'] for _, s in rows], [self.d['name'], self.b['name'], self.a['name']])

    def test_alive_entry_replaces_its_catalog_entry_once(self):
        alive = [self.scanned(self.a, 15)]
        rows = core.browse_order([self.a, self.b], alive, {core.endpoint_id(self.a)})
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], core.STATE_ALIVE)
        self.assertEqual(rows[0][1]['ip'], alive[0]['ip'])

    def test_empty_scope_gives_empty_list(self):
        self.assertEqual(core.browse_order([], [], set()), [])


if __name__ == '__main__':
    unittest.main()
