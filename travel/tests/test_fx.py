import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fx import parse_rate, to_cny

JPY = "Exchange rate from Japanese Yen (JPY) to Chinese Yuan (CNY). The current rate is 0.0417751 CNY per JPY. The rate is down 0.01%"
EUR = "Exchange rate from Euro (EUR) to Chinese Yuan (CNY). The current rate is 7.34912 CNY per EUR."


class FxTests(unittest.TestCase):
    def test_parses_matching_pair(self):
        self.assertAlmostEqual(parse_rate(JPY, "JPY", "CNY"), 0.0417751)
        self.assertAlmostEqual(parse_rate(EUR, "EUR", "CNY"), 7.34912)

    def test_rejects_wrong_direction(self):
        self.assertIsNone(parse_rate(JPY, "CNY", "JPY"))

    def test_rejects_unrelated_text(self):
        self.assertIsNone(parse_rate("Tokyo weather is rainy", "JPY", "CNY"))
        self.assertIsNone(parse_rate("", "JPY", "CNY"))

    def test_thousands_separator(self):
        self.assertAlmostEqual(parse_rate("The current rate is 1,234.5 CNY per XXX", "XXX", "CNY"), 1234.5)

    def test_conversion(self):
        self.assertEqual(to_cny(54000, 0.0417751), 2255.86)


if __name__ == "__main__":
    unittest.main()
