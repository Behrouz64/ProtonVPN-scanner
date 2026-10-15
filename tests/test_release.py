import os
import re
import unittest

import scanner_core as core

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ReleaseTests(unittest.TestCase):
    def test_app_version_is_1_0_2(self):
        self.assertEqual(core.APP_VERSION, '1.0.3')

    def test_pyproject_version_matches_app_version(self):
        with open(os.path.join(ROOT, 'pyproject.toml'), encoding='utf-8') as f:
            match = re.search(r'^version = "([^"]+)"', f.read(), re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), core.APP_VERSION)

    def test_kivy_build_file_is_gone(self):
        self.assertFalse(os.path.exists(os.path.join(ROOT, 'buildozer.spec')))

    def test_docs_and_tests_stay_out_of_the_app_package(self):
        import tomllib
        with open(os.path.join(ROOT, 'pyproject.toml'), 'rb') as f:
            excludes = tomllib.load(f)['tool']['flet']['app']['exclude']
        self.assertIn('docs', excludes)
        self.assertIn('tests', excludes)

    def test_no_markdown_notes_inside_assets(self):
        assets = os.path.join(ROOT, 'assets')
        self.assertEqual([n for n in os.listdir(assets) if n.endswith('.md')], [])


if __name__ == '__main__':
    unittest.main()
