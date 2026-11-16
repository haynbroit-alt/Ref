"""The pilot runbook works as written, and the metering recovers the ground truth of synthetic logs."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples"))
import pilot_demo  # noqa: E402


class TestPilotDemo(unittest.TestCase):
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            import io
            from contextlib import redirect_stdout
            with redirect_stdout(io.StringIO()):
                s = pilot_demo.main(d)
        self.assertTrue(s["constat_verified"])
        self.assertTrue(s["commit_proofs_verified"])
        self.assertEqual(s["public_log_size"], 12)  # 6 snapshots + 6 metering commitments
        o = s["openai"]
        # synthetic logs: 10% of genuine GPTBot fetches target the disallowed /premium/ directory
        self.assertAlmostEqual(o["disallowed_fetch_rate_verified"], 0.10, delta=0.02)
        self.assertEqual(o["verified_share"], 1.0)  # spoofed requests are excluded from the totals
        self.assertEqual(o["not_assessable_share"], 0.0)


if __name__ == "__main__":
    unittest.main()
