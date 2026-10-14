import json
import unittest

import app_settings
import scanner_core as core

VALID_KEY = 'A' * 43 + '='


class DefaultsAndLoadTests(unittest.TestCase):
    def test_defaults_are_persian_obfuscation_on_suggested_values(self):
        settings = app_settings.default_settings()
        self.assertEqual(settings['language'], 'fa')
        self.assertTrue(settings['obfuscation_enabled'])
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
        text = json.dumps({'language': 'en', 'obfuscation_enabled': False,
                           'obfuscation': {**core.DEFAULT_OBFUSCATION, 'Jc': '7', 'H1': '100-200'}})
        settings = app_settings.load_settings(text)
        self.assertEqual(settings['language'], 'en')
        self.assertFalse(settings['obfuscation_enabled'])
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

    def test_non_boolean_switch_is_ignored(self):
        settings = app_settings.load_settings(json.dumps({'obfuscation_enabled': 'no'}))
        self.assertTrue(settings['obfuscation_enabled'])


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


class RoundTripAndBuildTests(unittest.TestCase):
    def test_dump_then_load_gives_same_settings(self):
        settings = {'language': 'en', 'obfuscation_enabled': False,
                    'obfuscation': {**core.DEFAULT_OBFUSCATION, 'S1': 3}}
        loaded = app_settings.load_settings(app_settings.dump_settings(settings))
        self.assertEqual(loaded['language'], 'en')
        self.assertFalse(loaded['obfuscation_enabled'])
        self.assertEqual(loaded['obfuscation']['S1'], 3)

    def test_saved_file_never_contains_a_private_key_field(self):
        saved = json.loads(app_settings.dump_settings(app_settings.default_settings()))
        self.assertEqual(set(saved), {'version', 'language', 'obfuscation_enabled', 'obfuscation', 'scan_mode', 'fake_threshold_ms'})
        self.assertNotIn(VALID_KEY, app_settings.dump_settings(app_settings.default_settings()))

    def test_reset_restores_suggested_values_only(self):
        settings = {'language': 'en', 'obfuscation_enabled': False,
                    'obfuscation': {**core.DEFAULT_OBFUSCATION, 'Jc': 99}}
        reset = app_settings.reset_obfuscation(settings)
        self.assertEqual(reset['obfuscation'], core.DEFAULT_OBFUSCATION)
        self.assertEqual(reset['language'], 'en')
        self.assertFalse(reset['obfuscation_enabled'])

    def test_reset_does_not_change_the_original_dict(self):
        settings = app_settings.default_settings()
        settings['obfuscation'] = {**core.DEFAULT_OBFUSCATION, 'Jc': 99}
        app_settings.reset_obfuscation(settings)
        self.assertEqual(settings['obfuscation']['Jc'], 99)

    def test_build_parameters_are_none_when_obfuscation_is_off(self):
        settings = {**app_settings.default_settings(), 'obfuscation_enabled': False}
        self.assertIsNone(app_settings.obfuscation_for_build(settings))

    def test_build_parameters_are_normalized_when_on(self):
        params = app_settings.obfuscation_for_build(app_settings.default_settings())
        self.assertEqual(params['Jc'], 4)
        self.assertEqual(params['H4'], '4')

    def test_build_refuses_invalid_settings(self):
        settings = app_settings.default_settings()
        settings['obfuscation'] = {**core.DEFAULT_OBFUSCATION, 'Jmax': 1}
        with self.assertRaises(ValueError):
            app_settings.obfuscation_for_build(settings)


if __name__ == '__main__':
    unittest.main()
