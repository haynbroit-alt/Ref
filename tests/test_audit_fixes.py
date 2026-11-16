"""Regression tests for defects found during the self-audit (16 Nov 2026)."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from novarys import signals
from novarys.cli import main


class TestAuditFixes(unittest.TestCase):
    def test_logs_with_ledger_requires_matching_url(self):
        # before the fix, a missing --url silently defaulted to "/robots.txt", matched no snapshot
        # and reported zero disallowed fetches
        with tempfile.TemporaryDirectory() as d:
            rp, lp = os.path.join(d, "robots.txt"), os.path.join(d, "access.log")
            with open(rp, "w") as fh:
                fh.write("User-agent: GPTBot\nDisallow: /\n")
            with open(lp, "w") as fh:
                fh.write('1.1.1.1 - - [01/Oct/2026:10:00:00 +0000] "GET /a HTTP/1.1" 200 1 "-" "GPTBot/1.2"\n')
            led = os.path.join(d, "ledger")
            buf = io.StringIO()
            with redirect_stdout(buf):
                main(["snapshot", led, "--url", "https://x.example/robots.txt", "--file", rp])
                self.assertEqual(main(["logs", lp, "--ledger", led]), 2)
                self.assertEqual(main(["logs", lp, "--ledger", led, "--url", "https://other.example/robots.txt"]), 2)
                self.assertEqual(main(["logs", lp, "--ledger", led, "--url", "https://x.example/robots.txt"]), 0)
            self.assertIn("--url is required", buf.getvalue())

    def test_malformed_tdmrep_does_not_crash(self):
        entries = signals.parse_tdmrep('[{"location": "/", "tdm-reservation": "yes"}, {"location": "/", "tdm-reservation": 1}]')
        self.assertTrue(signals.tdmrep_reserves_root(entries))
        self.assertFalse(signals.tdmrep_reserves_root(signals.parse_tdmrep('[{"location": "/", "tdm-reservation": null}]')))


if __name__ == "__main__":
    unittest.main()
