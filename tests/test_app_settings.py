import json
import unittest

import app_settings
import scanner_core as core

VALID_KEY = 'A' * 43 + '='


class DefaultsAndLoadTests(unittest.TestCase):
    def test_defaults_are_persian_both_formats_and_suggested_values(self):
        settings = app_settings.default_settings()
        self.assertEqual(settings['language'], 'fa')
        self.assertEqual(settings['export_formats'], core.EXPORT_BOTH)
        self.assertEqual(settings['obfuscation'], core.DEFAULT_OBFUSCATION)

    def test_missing_or_broken_text_gives_defaults(self):
        defaults = app_settings.default_settings()
        for text in (None, '', '{not json', '[1, 2]', '"text"'):
            with self.subTest(text=text):
                self.assertEqual(app_settings.load_settings(text), defaults)

    def test_unknown_language_falls_back_to_default(self):
        settings = app_settings.load_settings(json.dumps({'language': 'de'}))
        self.assertEqual(settings['language'], 'fa')

    def test_valid_saved_values_are_kept_and_normalized(self):
        text = json.dumps({'language': 'en', 'export_formats': core.EXPORT_WG,
                           'obfuscation': {**core.DEFAULT_OBFUSCATION, 'Jc': '7', 'H1': '100-200'}})
        settings = app_settings.load_settings(text)
        self.assertEqual(settings['language'], 'en')
        self.assertEqual(settings['export_formats'], core.EXPORT_WG)
        self.assertEqual((settings['obfuscation']['Jc'], settings['obfuscation']['H1']), (7, '100-200'))

    def test_invalid_obfuscation_block_falls_back_to_suggested_values(self):
        text = json.dumps({'language': 'en', 'obfuscation': {**core.DEFAULT_OBFUSCATION, 'Jc': 'four'}})
        settings = app_settings.load_settings(text)
        self.assertEqual(settings['obfuscation'], core.DEFAULT_OBFUSCATION)
        self.assertEqual(settings['language'], 'en')

    def test_incomplete_obfuscation_block_falls_back(self):
        block = dict(core.DEFAULT_OBFUSCATION)
        del block['H4']
        settings = app_settings.load_settings(json.dumps({'obfuscation': block}))
        self.assertEqual(settings['obfuscation'], core.DEFAULT_OBFUSCATION)

    def test_unknown_export_format_falls_back_to_both(self):
        for value in ('all', 'WG', None, True):
            with self.subTest(value=value):
                loaded = app_settings.load_settings(json.dumps({'export_formats': value}))
                self.assertEqual(loaded['export_formats'], core.EXPORT_BOTH)

    def test_old_switch_is_migrated(self):
        on = app_settings.load_settings(json.dumps({'obfuscation_enabled': True}))
        off = app_settings.load_settings(json.dumps({'obfuscation_enabled': False}))
        self.assertEqual(on['export_formats'], core.EXPORT_BOTH)
        self.assertEqual(off['export_formats'], core.EXPORT_WG)

    def test_new_format_wins_over_old_switch(self):
        text = json.dumps({'obfuscation_enabled': False, 'export_formats': core.EXPORT_AWG})
        self.assertEqual(app_settings.load_settings(text)['export_formats'], core.EXPORT_AWG)

    def test_non_boolean_old_switch_is_ignored(self):
        settings = app_settings.load_settings(json.dumps({'obfuscation_enabled': 'no'}))
        self.assertEqual(settings['export_formats'], core.EXPORT_BOTH)


class ExportFormatTests(unittest.TestCase):
    def settings_with(self, formats):
        return {**app_settings.default_settings(), 'export_formats': formats}

    def test_both_writes_a_standard_and_an_amneziawg_file(self):
        obfs = app_settings.export_obfuscations(self.settings_with(core.EXPORT_BOTH))
        self.assertEqual(len(obfs), 2)
        self.assertIsNone(obfs[0])
        self.assertEqual(obfs[1]['Jc'], core.DEFAULT_OBFUSCATION['Jc'])

    def test_wg_writes_only_standard_files(self):
        self.assertEqual(app_settings.export_obfuscations(self.settings_with(core.EXPORT_WG)), [None])

    def test_awg_writes_only_amneziawg_files(self):
        obfs = app_settings.export_obfuscations(self.settings_with(core.EXPORT_AWG))
        self.assertEqual(len(obfs), 1)
        self.assertIsNotNone(obfs[0])

    def test_server_cards_are_standard_unless_awg_is_chosen(self):
        self.assertIsNone(app_settings.card_obfuscation(self.settings_with(core.EXPORT_BOTH)))
        self.assertIsNone(app_settings.card_obfuscation(self.settings_with(core.EXPORT_WG)))
        self.assertIsNotNone(app_settings.card_obfuscation(self.settings_with(core.EXPORT_AWG)))

    def test_invalid_amneziawg_parameters_refuse_the_export(self):
        settings = {**self.settings_with(core.EXPORT_BOTH), 'obfuscation': {**core.DEFAULT_OBFUSCATION, 'Jmax': 1}}
        with self.assertRaises(ValueError):
            app_settings.export_obfuscations(settings)

    def test_standard_export_ignores_invalid_amneziawg_parameters(self):
        settings = {**self.settings_with(core.EXPORT_WG), 'obfuscation': {**core.DEFAULT_OBFUSCATION, 'Jmax': 1}}
        self.assertEqual(app_settings.export_obfuscations(settings), [None])


class UntestedCountTests(unittest.TestCase):
    def test_default_is_fifteen(self):
        self.assertEqual(app_settings.default_settings()['untested_export_count'], 15)
        self.assertEqual(core.UNTESTED_EXPORT_DEFAULT, 15)

    def test_only_listed_counts_are_loaded(self):
        for value in core.UNTESTED_EXPORT_CHOICES:
            loaded = app_settings.load_settings(json.dumps({'untested_export_count': value}))
            self.assertEqual(loaded['untested_export_count'], value)
        for payload in ({'untested_export_count': 7}, {'untested_export_count': True},
                        {'untested_export_count': '15'}, {'untested_export_count': 0}):
            with self.subTest(payload=payload):
                loaded = app_settings.load_settings(json.dumps(payload))
                self.assertEqual(loaded['untested_export_count'], core.UNTESTED_EXPORT_DEFAULT)


class ScanSettingsTests(unittest.TestCase):
    def test_defaults_use_key_scan_and_ten_ms_threshold(self):
        settings = app_settings.default_settings()
        self.assertEqual(settings['scan_mode'], core.SCAN_WITH_KEY)
        self.assertEqual(settings['fake_threshold_ms'], core.MIN_PLAUSIBLE_PING_MS)

    def test_valid_values_are_loaded(self):
        loaded = app_settings.load_settings(
            json.dumps({'scan_mode': 'keyless', 'fake_threshold_ms': 20}))
        self.assertEqual(loaded['scan_mode'], 'keyless')
        self.assertEqual(loaded['fake_threshold_ms'], 20)

    def test_invalid_values_fall_back_to_defaults(self):
        for payload in ({'scan_mode': 'both'}, {'fake_threshold_ms': 7}, {'fake_threshold_ms': True},
                        {'fake_threshold_ms': '10'}, {'scan_mode': None}):
            with self.subTest(payload=payload):
                loaded = app_settings.load_settings(json.dumps(payload))
                self.assertEqual(loaded['scan_mode'], core.SCAN_WITH_KEY)
                self.assertEqual(loaded['fake_threshold_ms'], core.MIN_PLAUSIBLE_PING_MS)

    def test_round_trip_keeps_scan_settings(self):
        settings = {**app_settings.default_settings(), 'scan_mode': 'keyless', 'fake_threshold_ms': 0}
        loaded = app_settings.load_settings(app_settings.dump_settings(settings))
        self.assertEqual(loaded['scan_mode'], 'keyless')
        self.assertEqual(loaded['fake_threshold_ms'], 0)


class IpLimitSettingsTests(unittest.TestCase):
    def test_default_is_four_ips(self):
        self.assertEqual(app_settings.default_settings()['surfshark_ip_limit'], core.SURFSHARK_IP_DEFAULT)
        self.assertEqual(core.SURFSHARK_IP_DEFAULT, 4)

    def test_only_listed_choices_are_loaded(self):
        for value in core.SURFSHARK_IP_CHOICES:
            loaded = app_settings.load_settings(json.dumps({'surfshark_ip_limit': value}))
            self.assertEqual(loaded['surfshark_ip_limit'], value)
        for payload in ({'surfshark_ip_limit': 3}, {'surfshark_ip_limit': True}, {'surfshark_ip_limit': '4'}):
            with self.subTest(payload=payload):
                loaded = app_settings.load_settings(json.dumps(payload))
                self.assertEqual(loaded['surfshark_ip_limit'], core.SURFSHARK_IP_DEFAULT)

    def test_round_trip_keeps_the_limit(self):
        settings = {**app_settings.default_settings(), 'surfshark_ip_limit': 8}
        self.assertEqual(app_settings.load_settings(app_settings.dump_settings(settings))['surfshark_ip_limit'], 8)


class RoundTripAndBuildTests(unittest.TestCase):
    def test_dump_then_load_gives_same_settings(self):
        settings = {**app_settings.default_settings(), 'language': 'en', 'export_formats': core.EXPORT_AWG,
                    'obfuscation': {**core.DEFAULT_OBFUSCATION, 'S1': 3}, 'untested_export_count': 25}
        loaded = app_settings.load_settings(app_settings.dump_settings(settings))
        self.assertEqual(loaded['language'], 'en')
        self.assertEqual(loaded['export_formats'], core.EXPORT_AWG)
        self.assertEqual(loaded['obfuscation']['S1'], 3)
        self.assertEqual(loaded['untested_export_count'], 25)

    def test_saved_file_never_contains_a_private_key_field(self):
        saved = json.loads(app_settings.dump_settings(app_settings.default_settings()))
        self.assertEqual(set(saved), {'version', 'language', 'export_formats', 'obfuscation', 'scan_mode',
                                      'fake_threshold_ms', 'surfshark_ip_limit', 'untested_export_count'})
        self.assertNotIn(VALID_KEY, app_settings.dump_settings(app_settings.default_settings()))

    def test_reset_restores_suggested_values_only(self):
        settings = {**app_settings.default_settings(), 'language': 'en', 'export_formats': core.EXPORT_WG,
                    'obfuscation': {**core.DEFAULT_OBFUSCATION, 'Jc': 99}}
        reset = app_settings.reset_obfuscation(settings)
        self.assertEqual(reset['obfuscation'], core.DEFAULT_OBFUSCATION)
        self.assertEqual(reset['language'], 'en')
        self.assertEqual(reset['export_formats'], core.EXPORT_WG)

    def test_reset_does_not_change_the_original_dict(self):
        settings = app_settings.default_settings()
        settings['obfuscation'] = {**core.DEFAULT_OBFUSCATION, 'Jc': 99}
        app_settings.reset_obfuscation(settings)
        self.assertEqual(settings['obfuscation']['Jc'], 99)

    def test_build_parameters_are_normalized_when_amneziawg_is_chosen(self):
        params = app_settings.card_obfuscation(
            {**app_settings.default_settings(), 'export_formats': core.EXPORT_AWG})
        self.assertEqual(params['Jc'], 4)
        self.assertEqual(params['H4'], '4')


if __name__ == '__main__':
    unittest.main()
