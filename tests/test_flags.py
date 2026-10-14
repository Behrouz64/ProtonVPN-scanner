import os
import unittest

import scanner_core as core

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLAGS = os.path.join(ROOT, 'assets', 'flags')
# کدی که پرچم جدا ندارد و با آیکون کره‌ی زمین نشان داده می‌شود
ALIASES = {'UK': 'gb'}


def flag_file(cc):
    return os.path.join(FLAGS, f"{ALIASES.get(cc, cc).lower()}.png")


class FlagCoverageTests(unittest.TestCase):
    def codes(self):
        codes = set(core.CC_TO_NAME) - {core.UNKNOWN_CC}
        codes |= {server['cc'] for server in core.load_surfshark_catalog()}
        return sorted(codes)

    def test_every_country_has_a_flag_image(self):
        missing = [cc for cc in self.codes() if not os.path.exists(flag_file(cc))]
        self.assertEqual(missing, [])

    def test_flag_images_are_small_png_files(self):
        for cc in self.codes():
            with self.subTest(cc=cc), open(flag_file(cc), 'rb') as f:
                self.assertEqual(f.read(8), b'\x89PNG\r\n\x1a\n')
            self.assertLess(os.path.getsize(flag_file(cc)), 40_000)

    def test_license_is_shipped_with_the_flags(self):
        self.assertTrue(os.path.exists(os.path.join(FLAGS, 'LICENSE.txt')))


if __name__ == '__main__':
    unittest.main()
