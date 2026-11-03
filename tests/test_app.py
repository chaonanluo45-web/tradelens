import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from app import Handler
from engine import CATEGORIES, MARKETS, analyze_market, format_local, parse_inquiry


class EngineTests(unittest.TestCase):
    def test_default_brief_is_stable(self):
        result = analyze_market("led_outdoor", "DE", 22, "trial")
        self.assertEqual(result["score"], 78)
        self.assertEqual(result["verdict"], "建议试单")
        self.assertEqual(len(result["radar"]), 5)
        self.assertEqual(len(result["trace"]), 5)
        self.assertIn("€22.0", result["summary"])

    def test_every_category_market_combination(self):
        for category in CATEGORIES:
            for market in MARKETS:
                result = analyze_market(category, market, None, "trial")
                self.assertGreaterEqual(result["score"], 35)
                self.assertLessEqual(result["score"], 92)
                self.assertTrue(result["summary"])
                self.assertEqual(len(result["metrics"]), 4)

    def test_price_position_changes(self):
        inside = analyze_market("led_outdoor", "DE", 22, "trial")
        low = analyze_market("led_outdoor", "DE", 10, "trial")
        high = analyze_market("led_outdoor", "DE", 100, "trial")
        self.assertEqual(low["price_band"]["position"], "低于主流带")
        self.assertEqual(high["price_band"]["position"], "高于主流带")
        self.assertLess(low["score"], inside["score"])
        self.assertLess(high["score"], inside["score"])

    def test_currency_formatting(self):
        self.assertEqual(format_local(1234, MARKETS["VN"]), "1,000 ₫")
        self.assertEqual(format_local(19.5, MARKETS["DE"]), "€19.5")
        self.assertEqual(format_local(20, MARKETS["AE"]), "AED 20")

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            analyze_market("nope", "DE")
        with self.assertRaises(ValueError):
            analyze_market("led_outdoor", "NOPE")


class InquiryTests(unittest.TestCase):
    SAMPLE = """Subject: Inquiry for 50W LED garden light
    Dear Supplier, we are based in Hamburg, Germany. We need 2,000 pcs
    50W IP65 LED garden lights. Delivery within 3 weeks. Target price EUR
    14.5/pc FOB. Please send CE and RoHS certificates."""

    def test_extracts_core_fields(self):
        result = parse_inquiry(self.SAMPLE)
        values = {item["label"]: item["value"] for item in result["extracted"]}
        self.assertEqual(values["数量"], "2,000 件")
        self.assertEqual(values["目的地"], "德国")
        self.assertEqual(values["贸易条款"], "FOB")
        self.assertIn("CE", values["认证要求"])
        self.assertEqual(result["lead_level"], "B")

    def test_flags_low_price_and_tight_deadline(self):
        result = parse_inquiry(self.SAMPLE)
        titles = [flag["title"] for flag in result["flags"]]
        self.assertIn("目标价低于主流带", titles)
        self.assertIn("交期偏紧", titles)
        self.assertEqual(result["benchmark"]["position"], "低于主流带")

    def test_reply_is_english(self):
        result = parse_inquiry(self.SAMPLE)
        self.assertIn("Subject: Re: Inquiry for LED outdoor garden light", result["reply"])
        self.assertIn("Reference unit price", result["reply"])
        self.assertNotIn("LED 户外庭院灯 project", result["reply"])

    def test_short_text_rejected(self):
        with self.assertRaises(ValueError):
            parse_inquiry("too short")


class QuietHandler(Handler):
    def log_message(self, fmt, *args):
        pass


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def request(self, method, path, payload=None):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if body else {}
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()
        return response.status, data

    def test_health(self):
        status, data = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])

    def test_analyze_endpoint(self):
        status, data = self.request("POST", "/api/analyze", {
            "category": "led_outdoor", "market": "DE", "target_price": 22, "goal": "trial"
        })
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["result"]["score"], 78)

    def test_invalid_payload(self):
        status, data = self.request("POST", "/api/analyze", {"category": "bad", "market": "DE"})
        self.assertEqual(status, 400)
        self.assertFalse(data["ok"])

    def test_static_page(self):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", "/")
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        conn.close()
        self.assertEqual(response.status, 200)
        self.assertIn("TradeLens", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
