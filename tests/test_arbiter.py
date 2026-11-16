"""End-to-end tests of the neutral third-party layer (transparency log, constat, metering, canaries)."""
import io
import json
import os
import random
import tempfile
import unittest
from contextlib import redirect_stdout

from novarys import canary, constat, evidence, logs, metering, robots, transparency
from novarys.cli import main

URL = "https://news.example/robots.txt"
V1 = b"User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n"
V2 = b"User-agent: *\nAllow: /\n"
LOG = [
    # verified GPTBot fetch while V1 (block) was in force -> disallowed fetch
    '20.171.207.5 - - [10/Mar/2026:09:00:00 +0000] "GET /article/7 HTTP/1.1" 200 900 "-" "Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)"',
    # same agent string from an IP outside OpenAI's ranges -> spoofed, excluded
    '66.66.66.66 - - [10/Mar/2026:09:01:00 +0000] "GET /article/8 HTTP/1.1" 200 900 "-" "Mozilla/5.0 (compatible; GPTBot/1.2)"',
    # after V2 (no block) -> allowed fetch
    '20.171.207.6 - - [10/Jun/2026:09:00:00 +0000] "GET /article/9 HTTP/1.1" 200 900 "-" "Mozilla/5.0 (compatible; GPTBot/1.2)"',
    '1.2.3.4 - - [10/Jun/2026:10:00:00 +0000] "GET /article/9 HTTP/1.1" 200 900 "https://chatgpt.com/" "Mozilla/5.0 Firefox/130"',
]


def setup_case(d):
    led = evidence.Ledger(os.path.join(d, "ledger"))
    tl = transparency.Log(os.path.join(d, "tlog"))
    for ts, body in (("2026-01-01T00:00:00+00:00", V1), ("2026-05-01T00:00:00+00:00", V2)):
        e = led.add(URL, body, kind="robots.txt", ts=ts)
        tl.append({"type": "signal-snapshot", "url": URL, "kind": "robots.txt", "recorded_at": e.ts, "content_sha256": e.sha256})
    ranges_path = os.path.join(d, "gptbot.json")
    with open(ranges_path, "w") as fh:
        json.dump({"prefixes": [{"ipv4Prefix": "20.171.207.0/24"}]}, fh)
    cache = {}

    def robots_for(t):
        e = led.state_at(URL, t.isoformat())
        if e is None:
            return None
        return cache.setdefault(e.sha256, robots.parse(led.content(e).decode()))

    lr = logs.analyse(LOG, robots_for, {"GPTBot": logs.load_ranges(ranges_path)}).to_dict()
    return led, tl, lr


class TestTransparencyLog(unittest.TestCase):
    def test_inclusion_and_consistency_all_sizes(self):
        leaves = [transparency.leaf_hash(bytes([i])) for i in range(40)]
        full = transparency.Tree(leaves)
        root = full.mth()
        for n in range(1, 41):
            t = transparency.Tree(leaves[:n])
            for i in range(n):
                self.assertTrue(transparency.verify_inclusion(leaves[i], i, n, t.inclusion_proof(i), t.mth()))
            self.assertTrue(transparency.verify_consistency(n, 40, t.mth(), root, full.consistency_proof(n)))
            if n < 40:  # a rewritten history must not verify
                forged = transparency.Tree([transparency.leaf_hash(b"forged")] + leaves[1:n]).mth()
                self.assertFalse(transparency.verify_consistency(n, 40, forged, root, full.consistency_proof(n)))

    def test_file_log_proofs(self):
        with tempfile.TemporaryDirectory() as d:
            tl = transparency.Log(d)
            for i in range(7):
                tl.append({"i": i})
            old = tl.head()
            tl.append({"i": 7})
            p = tl.prove(3)
            self.assertTrue(transparency.check_inclusion(p))
            p["record"]["i"] = 99
            self.assertFalse(transparency.check_inclusion(p))
            c = tl.prove_consistency(old.size)
            self.assertEqual(c["old_root_sha256"], old.root)
            self.assertTrue(transparency.check_consistency(c))
            # reopening the directory gives the same head
            self.assertEqual(transparency.Log(d).head().root, tl.head().root)


class TestConstat(unittest.TestCase):
    def test_neutral_deterministic_and_dated(self):
        with tempfile.TemporaryDirectory() as d:
            led, tl, lr = setup_case(d)
            args = (os.path.join(d, "ledger"), URL, "2026-03-15T00:00:00+00:00", ["EU", "FR", "US"], lr, os.path.join(d, "tlog"))
            pub = constat.build(*args, requested_by="publisher")
            ai = constat.build(*args, requested_by="ai-provider")
            self.assertEqual(pub["report_sha256"], ai["report_sha256"])  # requester-independent
            self.assertTrue(constat.verify(pub))
            self.assertEqual(constat.neutral_wording(pub), [])
            o = pub["body"]["observation"]
            gpt = [a for a in o["agents"] if a["token"] == "GPTBot"][0]
            self.assertTrue(gpt["blocked_at_root_rfc9309"])  # V1 was in force on 15 March
            self.assertTrue(o["public_commitment"]["verified"])
            act = pub["body"]["crawler_activity"]["agents"]["GPTBot"]
            self.assertEqual((act["verified"], act["spoofed"], act["disallowed_fetches_verified"]), (2, 1, 1))
            # a later date shows the later file
            later = constat.build(os.path.join(d, "ledger"), URL, "2026-06-01T00:00:00+00:00")
            gpt2 = [a for a in later["body"]["observation"]["agents"] if a["token"] == "GPTBot"][0]
            self.assertFalse(gpt2["blocked_at_root_rfc9309"])
            # tampering with the body is detected
            pub["body"]["observation"]["content_sha256"] = "0" * 64
            self.assertFalse(constat.verify(pub))
            self.assertIn("Limites", constat.to_markdown(ai))

    def test_no_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            setup_case(d)
            rep = constat.build(os.path.join(d, "ledger"), URL, "2025-01-01T00:00:00+00:00")
            self.assertFalse(rep["body"]["observation"]["found"])


class TestMetering(unittest.TestCase):
    def synthetic(self, i):
        rnd = random.Random(i)
        req = rnd.randint(1000, 5000)
        return {"agents": {"GPTBot": {"requests": req, "verified": req - 10, "spoofed": 5, "disallowed_fetches_verified": rnd.randint(0, 20)},
                           "ClaudeBot": {"requests": 300, "verified": 290, "spoofed": 0, "disallowed_fetches_verified": 0}},
                "referrals": {"OpenAI": rnd.randint(5, 50)}}

    def test_k_anonymous_aggregate_without_prices(self):
        reports = [metering.publisher_report(self.synthetic(i), f"pub-{i}", "2026-10") for i in range(6)]
        reports += [metering.publisher_report({"agents": {"Bytespider": {"requests": 10, "verified": 0, "spoofed": 0}}, "referrals": {}}, "pub-x", "2026-10")]
        agg = metering.aggregate(reports)
        self.assertIn("OpenAI", agg["vendors"])
        self.assertEqual(agg["vendors"]["OpenAI"]["publishers_contributing"], 6)
        self.assertIn("ByteDance", agg["suppressed"])  # only one publisher saw it
        self.assertIn("median", agg["vendors"]["OpenAI"]["crawl_to_referral"])
        self.assertIsInstance(agg["vendors"]["Anthropic"]["crawl_to_referral"], str)  # no referrals -> suppressed
        text = json.dumps(agg).lower()
        for w in ("price", "eur", "usd", "rate_card", "pub-0"):
            self.assertNotIn(w, text)

    def test_dominance_rule(self):
        big = {"agents": {"GPTBot": {"requests": 100000, "verified": 100000, "spoofed": 0}}, "referrals": {}}
        small = {"agents": {"GPTBot": {"requests": 100, "verified": 100, "spoofed": 0}}, "referrals": {}}
        reps = [metering.publisher_report(big, "big", "2026-10")] + [metering.publisher_report(small, f"s{i}", "2026-10") for i in range(5)]
        agg = metering.aggregate(reps)
        self.assertEqual(agg["vendors"]["OpenAI"]["requests_not_spoofed_total"], "suppressed (dominance rule)")
        balanced = [metering.publisher_report(small, f"s{i}", "2026-10") for i in range(6)]
        self.assertEqual(metering.aggregate(balanced)["vendors"]["OpenAI"]["requests_not_spoofed_total"], 600)

    def test_commitment(self):
        with tempfile.TemporaryDirectory() as d:
            rep = metering.publisher_report(self.synthetic(1), "pub-1", "2026-10")
            p = metering.commit_report(rep, transparency.Log(d))
            self.assertTrue(transparency.check_inclusion(p))
            self.assertNotIn("pub-1", json.dumps(p))  # only a hash of the publisher id is public

    def test_single_period(self):
        a = metering.publisher_report(self.synthetic(1), "a", "2026-09")
        b = metering.publisher_report(self.synthetic(2), "b", "2026-10")
        with self.assertRaises(ValueError):
            metering.aggregate([a, b])


class TestCanary(unittest.TestCase):
    def test_exact_test_and_reveal(self):
        d = canary.create(12, seed=b"\x01" * 32)
        secret = d["secret"]
        self.assertTrue(canary.verify_reveal(secret, d["commitment"]))
        self.assertEqual(len(set(canary.published(secret)) & set(canary.withheld(secret))), 0)
        trained = {c: 1.0 for c in canary.published(secret)} | {c: 0.0 for c in canary.withheld(secret)}
        r = canary.test(secret, trained)
        self.assertEqual(r["mode"], "exact")
        self.assertAlmostEqual(r["p_value"], 1 / 2 ** 12)
        rnd = random.Random(3)
        null = {c: rnd.gauss(0, 1) for pair in secret["pairs"] for c in pair}
        self.assertGreater(canary.test(secret, null)["p_value"], 1 / 2 ** 12)
        tampered = dict(secret, pairs=[("x", "y")] + secret["pairs"][1:])
        self.assertFalse(canary.verify_reveal(tampered, d["commitment"]))

    def test_null_calibration(self):
        # under the null the exact p-value is uniform: P(p <= 0.05) ~ 0.05
        rej = 0
        for s in range(300):
            d = canary.create(10, seed=s.to_bytes(32, "big"))
            rnd = random.Random(s)
            scores = {c: rnd.gauss(0, 1) for pair in d["secret"]["pairs"] for c in pair}
            rej += canary.test(d["secret"], scores)["p_value"] <= 0.05
        self.assertLess(rej / 300, 0.09)


class TestCLI(unittest.TestCase):
    def run_cli(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(list(args))
        return code, buf.getvalue()

    def test_full_flow(self):
        with tempfile.TemporaryDirectory() as d:
            rp = os.path.join(d, "robots.txt")
            with open(rp, "wb") as fh:
                fh.write(V1)
            led, tl = os.path.join(d, "ledger"), os.path.join(d, "tlog")
            self.assertEqual(self.run_cli("snapshot", led, "--url", URL, "--file", rp, "--tlog", tl)[0], 0)
            out = os.path.join(d, "c.json")
            code, txt = self.run_cli("constat", led, "--url", URL, "--as-of", "2100-01-01T00:00:00+00:00",
                                     "--tlog", tl, "--jurisdiction", "EU,JP", "-o", out, "--md", os.path.join(d, "c.md"))
            self.assertEqual(code, 0, txt)
            self.assertIn("VALID", self.run_cli("constat-verify", out)[1])
            self.run_cli("tlog", "prove", tl, "--index", "0", "-o", os.path.join(d, "p.json"))
            self.assertIn("VALID", self.run_cli("check", os.path.join(d, "p.json"))[1])
            code, txt = self.run_cli("canary", "create", os.path.join(d, "s.json"), "-n", "4", "--tlog", tl, "-o", os.path.join(d, "pub.json"))
            self.assertEqual(code, 0)
            self.assertIn("VALID", self.run_cli("canary", "verify", os.path.join(d, "s.json"), os.path.join(d, "pub.json"))[1])
            self.run_cli("tlog", "consistency", tl, "--index", "1", "-o", os.path.join(d, "cons.json"))
            self.assertIn("VALID", self.run_cli("check", os.path.join(d, "cons.json"))[1])


if __name__ == "__main__":
    unittest.main()
