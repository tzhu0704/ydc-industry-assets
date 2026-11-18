import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from media_utils import (extract_audio_ids, extract_media_urls, host, is_direct_image, is_stock, numbers_in,
                         on_topic, ungrounded_numbers)


class MediaUtilsTests(unittest.TestCase):
    def test_stock_detection(self):
        self.assertTrue(is_stock("https://www.shutterstock.com/image-photo/x"))
        self.assertTrue(is_stock("https://media.istockphoto.com/id/1/photo/a.jpg?s=61"))
        self.assertTrue(is_stock("iStock"))
        self.assertFalse(is_stock("https://www.nasa.gov/image-article/x"))
        self.assertFalse(is_stock("https://example.com/shutter"))

    def test_direct_image(self):
        self.assertTrue(is_direct_image("https://a.com/p/x.JPG?w=100"))
        self.assertTrue(is_direct_image("https://a.com/p/x.webp"))
        self.assertFalse(is_direct_image("https://lookaside.instagram.com/seo/google_widget/crawler/?media_id=1"))
        self.assertFalse(is_direct_image("https://a.com/photos/tokyo"))
        self.assertFalse(is_direct_image(""))

    def test_on_topic(self):
        self.assertTrue(on_topic("Islamabad at night", ["islamabad"]))
        self.assertFalse(on_topic("generic blurred city", ["islamabad"]))

    def test_audio_ids_distinct_in_order(self):
        md = "a instagram.com/reels/audio/111 b instagram.com/reels/audio/222 c instagram.com/reels/audio/111"
        self.assertEqual(extract_audio_ids(md), ["111", "222"])
        self.assertEqual(extract_audio_ids(""), [])

    def test_media_urls(self):
        md = "![x](https://a.com/i/one.jpg) and https://b.org/v.mp4?x=1 and https://c.net/page.html and https://a.com/i/one.jpg"
        self.assertEqual(extract_media_urls(md), ["https://a.com/i/one.jpg", "https://b.org/v.mp4?x=1"])
        self.assertEqual(extract_media_urls("see https://commons.wikimedia.org/wiki/File:X.jpg"), [])
        self.assertEqual(extract_media_urls("https://u.org/c/2/2f/A.jpg/20px-A.jpg https://u.org/c/2/2f/A.jpg/1280px-A.jpg https://u.org/i.svg.png"),
                         ["https://u.org/c/2/2f/A.jpg/1280px-A.jpg"])
        self.assertEqual(extract_media_urls("https://n.gov/wp-content/plugins/x/favicons/favicon-16x16.png https://n.gov/a/photo.png"), ["https://n.gov/a/photo.png"])
        self.assertEqual(extract_media_urls('{"u":"https:\\/\\/a.com\\/x.jpg"}'), ["https://a.com/x.jpg"])

    def test_numbers_normalised(self):
        self.assertEqual(numbers_in("BTC 67,250.50 and 3.0 and 12."), {"67250.5", "3", "12"})

    def test_ungrounded_numbers(self):
        src = "Bitcoin traded at $67,250.5; air quality index 87"
        self.assertEqual(ungrounded_numbers("比特币 67250.5 美元，空气质量 87", src), [])
        self.assertEqual(ungrounded_numbers("比特币 70000 美元，空气质量 87", src), ["70000"])

    def test_host(self):
        self.assertEqual(host("https://www.NASA.gov/x"), "nasa.gov")


if __name__ == "__main__":
    unittest.main()


class ShotScriptTests(unittest.TestCase):
    def setUp(self):
        from media_utils import validate_shot_script
        self.v = validate_shot_script
        self.good = {"shoot_window": "15:34-16:34", "shots": [
            {"n": 1, "seconds": 10, "camera_move": "push-in", "facts": ["S1"]},
            {"n": 2, "seconds": 20, "camera_move": "drone-orbit", "facts": ["S2"]}]}

    def test_passes(self):
        self.assertEqual(self.v(self.good, {"S1", "S2"}, {"S2"}, 30, "15:34-16:34"), [])

    def test_catches_problems(self):
        bad = {"shoot_window": "10:00-11:00", "shots": [
            {"n": 1, "seconds": 10, "camera_move": "whip-pan", "facts": ["S9"]},
            {"n": 2, "seconds": 5, "camera_move": "drone-orbit", "facts": ["S1"]}]}
        p = self.v(bad, {"S1"}, {"S2"}, 30, "15:34-16:34")
        self.assertEqual(len(p), 5)  # vocab, unknown source, drone w/o rules, sum, window

    def test_sunset_and_window(self):
        from media_utils import golden_hour_window, parse_sunset
        self.assertEqual(parse_sunset("Sunrise is at 6:15 AM and sunset is at 4:34 PM."), (16, 34))
        self.assertEqual(parse_sunset("sunset is at 12:05 AM"), (0, 5))
        self.assertIsNone(parse_sunset("no times here"))
        self.assertEqual(golden_hour_window((16, 34)), "15:34-16:34")

    def test_extract_json(self):
        from media_utils import extract_json
        self.assertEqual(extract_json('prose ```json\n{"a": {"b": "x}y"}}\n``` tail'), {"a": {"b": "x}y"}})
        self.assertIsNone(extract_json("no json"))


class DataCardCheckTests(unittest.TestCase):
    def test_spelled_out_number_is_caught(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scenarios"))
        import importlib.util
        spec = importlib.util.spec_from_file_location("s3", Path(__file__).resolve().parent.parent / "scenarios" / "03_data_card_script.py")
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        src = "Bitcoin $64,607.8 as of 2026-11-18"
        ok = {"voice_over": "比特币 64607.8 美元", "on_screen": ["64,607.8 美元"]}
        words = {"voice_over": "比特币六万四千六百零七点八美元", "on_screen": ["64,607.8 美元"]}
        wrong = {"voice_over": "比特币 66000 美元", "on_screen": ["66000 美元"]}
        self.assertEqual(m.check(ok, src), [])
        self.assertEqual(len(m.check(words, src)), 1)
        self.assertEqual(m.check(wrong, src), ["66000"] )

