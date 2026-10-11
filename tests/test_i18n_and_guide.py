import re
import unittest

import guide_content
import i18n

BIDI_LRI, BIDI_PDI = '⁦', '⁩'
KEY_LIKE = re.compile(r'[A-Za-z0-9+/]{43}=')


def format_fields(text):
    return set(re.findall(r'\{(\w+)\}', text))


class StringCatalogueTests(unittest.TestCase):
    def test_every_key_exists_in_both_languages(self):
        self.assertEqual(set(i18n.STRINGS['en']), set(i18n.STRINGS['fa']))

    def test_placeholders_match_between_languages(self):
        for key in i18n.STRINGS['en']:
            with self.subTest(key=key):
                self.assertEqual(format_fields(i18n.STRINGS['en'][key]), format_fields(i18n.STRINGS['fa'][key]))

    def test_no_empty_strings(self):
        for lang, table in i18n.STRINGS.items():
            for key, text in table.items():
                with self.subTest(lang=lang, key=key):
                    self.assertTrue(text.strip())

    def test_unknown_language_uses_default(self):
        self.assertEqual(i18n.normalize_language('de'), i18n.DEFAULT_LANGUAGE)
        self.assertEqual(i18n.normalize_language(None), i18n.DEFAULT_LANGUAGE)

    def test_translate_formats_values(self):
        self.assertEqual(i18n.t('en', 'scan_found', alive=3, shown=3),
                         'Found 3 alive. Showing the top 3.')

    def test_missing_key_in_language_falls_back_to_english(self):
        original = i18n.STRINGS['fa'].pop('close')
        try:
            self.assertEqual(i18n.t('fa', 'close'), 'Close')
        finally:
            i18n.STRINGS['fa']['close'] = original


class KeyUsageTests(unittest.TestCase):
    """هر متنی که در فایل‌های رابط تعریف شده باید واقعاً نشان داده شود."""

    def test_every_key_is_referenced_by_the_interface(self):
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        source = ''
        for name in ('main.py', 'ui_parts.py'):
            with open(os.path.join(root, name), encoding='utf-8') as f:
                source += f.read()
        unused = sorted(key for key in i18n.STRINGS['en'] if f"'{key}'" not in source)
        self.assertEqual(unused, [])


class BidiIsolationTests(unittest.TestCase):
    def test_latin_tokens_with_punctuation_are_isolated(self):
        text = i18n.isolate_ltr('کپی لینک‌های wg://')
        self.assertIn(f'{BIDI_LRI}wg://{BIDI_PDI}', text)

    def test_latin_phrase_stays_together(self):
        text = i18n.isolate_ltr('از App Store.')
        self.assertIn(f'{BIDI_LRI}App Store.{BIDI_PDI}', text)

    def test_file_extension_is_isolated_inside_brackets(self):
        self.assertEqual(i18n.isolate_ltr('(.conf)'), f'({BIDI_LRI}.conf{BIDI_PDI})')

    def test_plain_words_and_lone_symbols_are_left_alone(self):
        for text in ('WireGuard کلید', 'بعد - قبل', '17 ms'):
            with self.subTest(text=text):
                self.assertEqual(i18n.isolate_ltr(text), text)

    def test_persian_strings_are_isolated_english_are_not(self):
        self.assertIn(BIDI_LRI, i18n.t('fa', 'btn_export'))
        self.assertNotIn(BIDI_LRI, i18n.t('en', 'btn_export'))


class GuideContentTests(unittest.TestCase):
    def test_both_languages_have_the_same_number_of_sections(self):
        self.assertEqual(set(guide_content.GUIDE), {'fa', 'en'})
        self.assertEqual(len(guide_content.GUIDE['fa']), len(guide_content.GUIDE['en']))

    def test_sections_have_matching_block_kinds_and_list_sizes(self):
        for index, (fa, en) in enumerate(zip(guide_content.GUIDE['fa'], guide_content.GUIDE['en'])):
            with self.subTest(section=index):
                self.assertTrue(fa['title'].strip() and en['title'].strip())
                self.assertEqual([kind for kind, _ in fa['blocks']], [kind for kind, _ in en['blocks']])
                for (kind, fa_value), (_, en_value) in zip(fa['blocks'], en['blocks']):
                    if kind in ('ul', 'ol'):
                        self.assertEqual(len(fa_value), len(en_value))

    def test_only_known_block_kinds_are_used(self):
        allowed = {'p', 'ul', 'ol', 'note', 'warn', 'link'}
        for lang, sections in guide_content.GUIDE.items():
            for section in sections:
                for kind, _ in section['blocks']:
                    with self.subTest(lang=lang, kind=kind):
                        self.assertIn(kind, allowed)

    def test_links_are_https_and_identical_in_both_languages(self):
        for index, (fa, en) in enumerate(zip(guide_content.GUIDE['fa'], guide_content.GUIDE['en'])):
            fa_links = [value for kind, value in fa['blocks'] if kind == 'link']
            en_links = [value for kind, value in en['blocks'] if kind == 'link']
            with self.subTest(section=index):
                self.assertEqual([url for _, url in fa_links], [url for _, url in en_links])
                for label, url in fa_links:
                    self.assertTrue(label.strip())
                    self.assertTrue(url.startswith('https://'), url)

    def test_guide_text_contains_no_real_looking_key(self):
        for lang, sections in guide_content.GUIDE.items():
            flat = repr(sections)
            with self.subTest(lang=lang):
                self.assertIsNone(KEY_LIKE.search(flat))


if __name__ == '__main__':
    unittest.main()
