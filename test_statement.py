import copy
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from app import make_handler
from statement import income_statement, load_ledger, parse_cents


ROOT = Path(__file__).resolve().parent


class StatementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = load_ledger(ROOT / "ledger.json")

    def report(self, start="2026-01-01", end="2026-03-31"):
        return income_statement(self.ledger, start, end)

    def amounts(self, report):
        return {row["number"]: row["amount"]
                for section in report["sections"] for row in section["accounts"]}

    def test_q1_independent_account_and_total_targets(self):
        result = self.report()
        self.assertEqual(self.amounts(result), {
            "4000": "35650.75", "4100": "3000.00", "4900": "-800.25",
            "5000": "14272.75", "6000": "55500.00", "6100": "9000.00",
            "6200": "1099.97", "6300": "2500.10", "7000": "42.18",
        })
        self.assertEqual([s["subtotal"] for s in result["sections"]],
                         ["37850.50", "14272.75", "68100.07", "42.18"])
        self.assertEqual((result["gross_profit"], result["operating_income"], result["net_income"]),
                         ("23577.75", "-44522.32", "-44480.14"))

    def test_posted_only_and_inclusive_dates(self):
        february_sales = self.report("2026-02-03", "2026-02-03")
        self.assertEqual(self.amounts(february_sales)["4000"], "8200.00")
        self.assertEqual(self.amounts(february_sales)["5000"], "3280.00")
        self.assertEqual(self.amounts(self.report("2026-01-01", "2026-01-01"))["6100"], "9000.00")
        self.assertEqual(self.amounts(self.report("2026-03-31", "2026-03-31"))["7000"], "42.18")
        self.assertEqual(self.amounts(self.report())["6000"], "55500.00")  # draft bonus excluded

    def test_period_activity_and_balance_sheet_exclusion(self):
        january = self.report("2026-01-01", "2026-01-31")
        february = self.report("2026-02-01", "2026-02-28")
        self.assertEqual(self.amounts(january)["4100"], "1000.00")  # billing is deferred
        self.assertEqual(self.amounts(february)["4000"], "8200.00")  # collection is not sales
        self.assertEqual(self.amounts(february)["6100"], "0.00")  # no invented rent allocation
        self.assertEqual(self.amounts(january)["6300"], "2500.10")  # inactive account remains
        self.assertEqual(len(self.amounts(january)), 9)
        self.assertEqual(self.amounts(self.report("2025-12-15", "2025-12-15"))["4000"], "5000.00")
        self.assertEqual(self.amounts(self.report("2026-04-01", "2026-04-01"))["4000"], "9100.00")

    def test_reversing_signs_and_empty_period(self):
        february = self.report("2026-02-14", "2026-02-14")
        self.assertEqual(self.amounts(february)["4900"], "-650.25")
        self.assertEqual(february["net_income"], "-650.25")
        march_credit = self.report("2026-03-20", "2026-03-20")
        self.assertEqual(self.amounts(march_credit)["6200"], "-100.00")
        self.assertEqual(march_credit["net_income"], "100.00")
        empty = self.report("2026-05-01", "2026-05-31")
        self.assertEqual(empty["net_income"], "0.00")
        self.assertEqual(len(empty["sections"]), 4)
        self.assertTrue(all(amount == "0.00" for amount in self.amounts(empty).values()))

    def test_months_add_to_quarter_for_each_line_and_total(self):
        quarters = [self.report("2026-01-01", "2026-01-31"),
                    self.report("2026-02-01", "2026-02-28"),
                    self.report("2026-03-01", "2026-03-31")]
        q1 = self.report()
        for number, amount in self.amounts(q1).items():
            self.assertEqual(parse_cents_signed(amount),
                             sum(parse_cents_signed(self.amounts(month)[number]) for month in quarters))
        for field in ("gross_profit", "operating_income", "net_income"):
            self.assertEqual(parse_cents_signed(q1[field]),
                             sum(parse_cents_signed(month[field]) for month in quarters))

    def test_invalid_dates(self):
        for start, end in [("2026-02-30", "2026-03-01"), ("2026-03-02", "2026-03-01"),
                           ("2026-1-01", "2026-03-01"), (None, "2026-03-01")]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                self.report(start, end)

    def test_exact_cents_and_bad_source_data(self):
        self.assertEqual(parse_cents("12345678901234567890.09"), 1234567890123456789009)
        raw = json.loads((ROOT / "ledger.json").read_text())
        mutations = [
            lambda x: x["journal_entries"][0]["lines"][0].update(account="9999"),
            lambda x: x["journal_entries"][0]["lines"][0].update(debit="5000.01"),
            lambda x: x["journal_entries"][0]["lines"][0].update(debit="5000.001"),
        ]
        for mutate in mutations:
            invalid = copy.deepcopy(raw)
            mutate(invalid)
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "ledger.json"
                path.write_text(json.dumps(invalid))
                with self.assertRaises(ValueError):
                    load_ledger(path)

    def test_ledger_matches_assignment_source(self):
        source = (ROOT / "README.md").read_text().split("```json\n", 1)[1].split("\n```", 1)[0]
        self.assertEqual(json.loads((ROOT / "ledger.json").read_text()), json.loads(source))


def parse_cents_signed(value):
    return -parse_cents(value[1:]) if value.startswith("-") else parse_cents(value)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(load_ledger(ROOT / "ledger.json")))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_api_and_page(self):
        with urlopen(self.base + "/") as response:
            self.assertIn(b"Show statement", response.read())
        with urlopen(self.base + "/income-statement?start=2026-01-01&end=2026-03-31") as response:
            result = json.load(response)
        self.assertEqual(result["net_income"], "-44480.14")
        self.assertEqual(result["currency"], "USD")

    def test_bad_queries_return_400(self):
        for query in ("", "?start=2026-01-01", "?start=2026-02-30&end=2026-03-31",
                      "?start=2026-04-01&end=2026-03-31", "?start=2026-01-01&start=2026-02-01&end=2026-03-31"):
            with self.subTest(query=query), self.assertRaises(HTTPError) as error:
                urlopen(self.base + "/income-statement" + query)
            self.assertEqual(error.exception.code, 400)
            error.exception.close()


if __name__ == "__main__":
    unittest.main()
