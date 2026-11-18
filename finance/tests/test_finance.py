import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finance_utils import (band_status, days_old, hkex_url_date, parse_date, parse_peg_band, quote_supported,
                           simplified_chars, ungrounded_numbers)


class FinanceUtilsTests(unittest.TestCase):
    def test_parse_date(self):
        self.assertEqual(parse_date("2026-11-18T22:12:18"), date(2026, 11, 18))
        self.assertEqual(parse_date("2026-09-01"), date(2026, 9, 1))
        self.assertIsNone(parse_date(""))
        self.assertIsNone(parse_date("n/a"))

    def test_days_old(self):
        self.assertEqual(days_old("2026-11-08", date(2026, 11, 18)), 10)
        self.assertIsNone(days_old(None, date(2026, 11, 18)))

    def test_hkex_url_date(self):
        self.assertEqual(hkex_url_date("https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0318/2026031800123.pdf"), date(2026, 3, 18))
        self.assertIsNone(hkex_url_date("https://example.com/x.pdf"))
        self.assertIsNone(hkex_url_date("https://h.hk/a/2026/1332/x.pdf"))  # month 13 is not a date

    def test_peg_band(self):
        self.assertEqual(parse_peg_band("the exchange rate between 7.75 and 7.85 HK$ per US$"), (7.75, 7.85))
        self.assertIsNone(parse_peg_band("only 7.75 appears here"))
        self.assertIsNone(parse_peg_band(""))

    def test_band_status(self):
        b = (7.75, 7.85)
        self.assertTrue(band_status(7.80, b).startswith("inside the band (50%"))
        self.assertIn("strong side", band_status(7.70, b))
        self.assertIn("weak side", band_status(7.90, b))

    def test_numbers(self):
        self.assertEqual(ungrounded_numbers("匯率 7.8 與 1,234.50", "rate 7.80 and 1234.5"), [])
        self.assertEqual(ungrounded_numbers("匯率 7.9", "rate 7.80"), ["7.9"])

    def test_quote_supported(self):
        src = ["The Commission reprimanded  the firm and fined it HK$3 million for failures."]
        self.assertTrue(quote_supported("reprimanded the firm and fined it HK$3 million", src))
        self.assertFalse(quote_supported("fined it HK$30 million", src))
        self.assertFalse(quote_supported("fined", src))  # too short to count as evidence

    def test_simplified_chars(self):
        self.assertEqual(simplified_chars("銀行與客戶"), [])
        self.assertEqual(simplified_chars("银行与客户"), ["与", "户", "银"])


if __name__ == "__main__":
    unittest.main()


class MoreUtilsTests(unittest.TestCase):
    def test_dates(self):
        from finance_utils import dates_in, ungrounded_dates
        self.assertEqual(dates_in("on 2026-11-02 and 2026-10-30."), {"2026-11-02", "2026-10-30"})
        self.assertEqual(ungrounded_dates("發布於 2026-11-02、2026-11-05", {"2026-11-02"}), ["2026-11-05"])

    def test_citations(self):
        from finance_utils import bad_citations
        self.assertEqual(bad_citations("見 [1] [3] [7]", 5), ["7"])
        self.assertEqual(bad_citations("無引用", 5), [])
        self.assertEqual(bad_citations("[0]", 5), ["0"])

    def test_content_language(self):
        from finance_utils import content_language
        self.assertEqual(content_language("The Hong Kong Monetary Authority " * 20), "EN")
        self.assertEqual(content_language("財富管理互聯互通合資格投資者須在內地開設銀行賬戶並於香港銀行開立投資專戶" * 3), "ZH-HANT")
        self.assertEqual(content_language("财富管理互联互通合资格投资者须在内地开设银行账户并于香港银行开立投资专户" * 3), "ZH-HANS")
        self.assertEqual(content_language(""), "EN")

    def test_outside_window(self):
        from finance_utils import outside_window
        self.assertEqual(outside_window([10, 400, None, 3000], 365), (2, 1))
        self.assertEqual(outside_window([], 30), (0, 0))

    def test_median(self):
        from finance_utils import median
        self.assertEqual(median([3, 1, 2]), 2)
        self.assertEqual(median([4, 1, 3, 2]), 2.5)
        self.assertIsNone(median([None]))
