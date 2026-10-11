import os
import re
import unittest

import scanner_core as core

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ReleaseTests(unittest.TestCase):
    def test_app_version_is_1_0_2(self):
        self.assertEqual(core.APP_VERSION, '1.0.2')

    def test_pyproject_version_matches_app_version(self):
        with open(os.path.join(ROOT, 'pyproject.toml'), encoding='utf-8') as f:
            match = re.search(r'^version = "([^"]+)"', f.read(), re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), core.APP_VERSION)

    def test_kivy_build_file_is_gone(self):
        self.assertFalse(os.path.exists(os.path.join(ROOT, 'buildozer.spec')))


if __name__ == '__main__':
    unittest.main()
