import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone

from novarys import audit, compiler, evidence, logs, registry, robots, signals
from novarys.cli import main

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY = os.path.join(ROOT, "examples", "policy-media-fr.json")


def load_policy(**over):
    with open(POLICY, encoding="utf-8") as fh:
        d = json.load(fh)
    d.update(over)
    return compiler.Policy.from_dict(d)


class TestRegistry(unittest.TestCase):
    def test_core_training_agents_exist(self):
        for t in registry.CORE_TRAINING:
            self.assertIsNotNone(registry.agent(t), t)

    def test_every_agent_has_status_and_known_purpose(self):
        for a in registry.agents():
            self.assertIn(a.status, ("verified", "reported", "unverified"))
            self.assertIn(a.purpose, ("search", "ai_answers", "user_fetch", "training", "ads", "mixed"))

    def test_jurisdictions_cover_30_markets(self):
        js = registry.jurisdictions()
        markets = [k for k in js if k != "EU"]
        self.assertEqual(len(markets), 30)
        self.assertEqual(registry.jurisdiction("DE")["regime"], "eu-optout")  # inherited
        self.assertIn("named_bot_risk", registry.jurisdiction("FR"))


class TestCompiler(unittest.TestCase):
    def test_compiled_robots_implements_policy_in_both_dialects(self):
        pol = load_policy()
        files = compiler.compile_all(pol)
        v = compiler.verify(pol, files["robots.txt"])
        self.assertTrue(v.ok, (v.mismatches, v.dialect_divergences, v.lints))

    def test_variants_all_verify(self):
        for purposes in ({"training": "allow"}, {"ai_answers": "deny"}, {"user_fetch": "deny", "training": "deny"},
                         {"search": "deny", "ai_answers": "deny", "training": "deny", "user_fetch": "deny"}):
            pol = load_policy(purposes=purposes)
            v = compiler.verify(pol, compiler.compile_robots(pol))
            self.assertTrue(v.ok, (purposes, v.mismatches[:3], v.dialect_divergences[:3], v.lints))

    def test_override(self):
        pol = load_policy(agent_overrides={"Google-Extended": "allow"})
        rb = robots.parse(compiler.compile_robots(pol))
        self.assertTrue(rb.can_fetch("Google-Extended", "/article"))
        self.assertFalse(rb.can_fetch("GPTBot", "/article"))

    def test_premium_path_and_snippet(self):
        pol = load_policy()
        rb = robots.parse(compiler.compile_robots(pol))
        self.assertFalse(rb.can_fetch("OAI-SearchBot", "/premium/x"))
        self.assertTrue(rb.can_fetch("OAI-SearchBot", "/news/x"))
        self.assertTrue(rb.can_fetch("Googlebot", "/premium/x"))
        self.assertEqual(compiler.compile_headers(pol)["/premium/"]["X-Robots-Tag"], "max-snippet:50")

    def test_tdmrep_and_statements(self):
        pol = load_policy()
        tdm = json.loads(compiler.compile_tdmrep(pol))
        self.assertEqual(tdm[0]["tdm-reservation"], 1)
        st = compiler.compile_statements(pol)
        self.assertIn("L. 122-5-3", st["fr"])
        self.assertIn("Japan", st["jurisdiction_notes"])

    def test_manifest_hashes(self):
        files = compiler.compile_all(load_policy())
        man = json.loads(files["manifest.json"])
        for name, h in man["files"].items():
            self.assertEqual(hashlib.sha256(files[name].encode()).hexdigest(), h)

    def test_invalid_policy(self):
        with self.assertRaises(ValueError):
            load_policy(purposes={"training": "maybe"})


class TestAudit(unittest.TestCase):
    def test_compiled_output_scores_100_with_tos(self):
        pol = load_policy()
        f = compiler.compile_all(pol)
        rep = audit.audit(audit.Inputs(robots_txt=f["robots.txt"], tdmrep_json=f[".well-known/tdmrep.json"],
                                       tos_text=compiler.compile_statements(pol)["en"], jurisdictions=["EU", "FR"]))
        self.assertEqual(rep.reservation["score"], 100)
        self.assertEqual([x.code for x in rep.findings if x.severity in ("critical", "high", "medium")], [])
        self.assertEqual(rep.jurisdictions[0]["effect"], "strong")

    def test_typical_partial_file(self):
        txt = "User-agent: GPTBot\nDisallow: /\n\nUser-agent: anthropic-ai\nDisallow: /\n"
        rep = audit.audit(audit.Inputs(robots_txt=txt, jurisdictions=["EU", "JP"]))
        codes = {f.code for f in rep.findings}
        self.assertTrue({"TRAINING_PARTIAL", "OBSOLETE_TOKEN", "NAMED_BOTS_ONLY", "NO_TDMREP"} <= codes, codes)
        self.assertEqual(rep.jurisdictions[0]["effect"], "weak")
        self.assertEqual(rep.jurisdictions[1]["effect"], "limited")

    def test_server_error_is_critical(self):
        rep = audit.audit(audit.Inputs(robots_txt="", robots_status=503))
        self.assertEqual(rep.findings[0].code, "ROBOTS_SERVER_ERROR")

    def test_no_signal_means_no_reservation(self):
        rep = audit.audit(audit.Inputs(robots_txt="User-agent: *\nDisallow: /tmp/\n", jurisdictions=["EU"]))
        self.assertEqual(rep.reservation["intent"], "unknown")
        self.assertEqual(rep.jurisdictions[0]["effect"], "none")

    def test_parser_divergence_detected(self):
        txt = "User-agent: CCBot\nCrawl-delay: 2\n\nUser-agent: BadBot\nDisallow: /\n"
        codes = {f.code for f in audit.audit(audit.Inputs(robots_txt=txt)).findings}
        self.assertIn("PARSER_DIVERGENCE", codes)
        self.assertIn("AMBIGUOUS_GROUPS", codes)

    def test_snippet_controls_limit_ai_overviews(self):
        rep = audit.audit(audit.Inputs(robots_txt="", headers={"X-Robots-Tag": "nosnippet"}))
        aio = [v for v in rep.visibility if v["surface"].startswith("Google AI Overviews")][0]
        self.assertEqual(aio["state"], "blocked")


class TestSignals(unittest.TestCase):
    def test_prefs(self):
        self.assertEqual(signals.parse_prefs("search=yes, ai-train=no"), {"search": True, "ai-train": False})
        self.assertIs(signals.training_denied(signals.parse_prefs("train-ai=n")), True)

    def test_html(self):
        ps = signals.parse_page(html='<meta name="robots" content="max-snippet:20, noai"><meta name="tdm-reservation" content="1"><p data-nosnippet>x</p>')
        self.assertEqual(ps.max_snippet, 20)
        self.assertTrue(ps.tdm_reservation and ps.noai_meta and ps.data_nosnippet)

    def test_tdmrep(self):
        self.assertTrue(signals.tdmrep_reserves_root(signals.parse_tdmrep('[{"location":"/","tdm-reservation":1}]')))
        self.assertFalse(signals.tdmrep_reserves_root(signals.parse_tdmrep("not json")))


class TestEvidence(unittest.TestCase):
    def test_chain_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as d:
            led = evidence.Ledger(d)
            led.add("https://x/robots.txt", b"User-agent: GPTBot\nDisallow: /\n", ts="2026-01-01T00:00:00+00:00")
            led.add("https://x/robots.txt", b"User-agent: *\nAllow: /\n", ts="2026-06-01T00:00:00+00:00")
            self.assertEqual(led.verify(), [])
            e = led.state_at("https://x/robots.txt", "2026-03-01T00:00:00Z")
            self.assertIn(b"GPTBot", led.content(e))
            # tamper with the first entry
            with open(led.log, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            first = json.loads(lines[0]); first["ts"] = "2025-01-01T00:00:00+00:00"
            lines[0] = json.dumps(first)
            with open(led.log, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
            self.assertTrue(any("modified" in p for p in led.verify()))

    def test_tsq_is_valid_der(self):
        req = evidence.timestamp_request(hashlib.sha256(b"x").hexdigest(), nonce=1)
        self.assertEqual(req[0], 0x30)
        self.assertEqual(req[1], len(req) - 2)
        self.assertIn(hashlib.sha256(b"x").digest(), req)


class TestLogs(unittest.TestCase):
    LOG = [
        '20.171.207.1 - - [01/Oct/2026:10:00:00 +0000] "GET /article/1 HTTP/1.1" 200 512 "-" "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)"',
        '6.6.6.6 - - [01/Oct/2026:10:00:01 +0000] "GET /article/2 HTTP/1.1" 200 512 "-" "Mozilla/5.0 (compatible; GPTBot/1.2)"',
        '1.2.3.4 - - [01/Oct/2026:10:00:02 +0000] "GET /article/1 HTTP/1.1" 200 512 "https://chatgpt.com/" "Mozilla/5.0 Firefox/130"',
        '9.9.9.9 - - [01/Oct/2026:10:00:03 +0000] "GET /x HTTP/1.1" 200 1 "-" "Mozilla/5.0 (compatible; Claude-SearchBot/1.0; +Searchbot@anthropic.com)"',
        'garbage line',
    ]

    def test_identify_longest(self):
        self.assertEqual(logs.identify("compatible; Claude-SearchBot/1.0").token, "Claude-SearchBot")
        self.assertEqual(logs.identify("compatible; ClaudeBot/1.0; +claudebot@anthropic.com").token, "ClaudeBot")
        self.assertIsNone(logs.identify("Mozilla/5.0 Firefox/130"))

    def test_analyse(self):
        rb = robots.parse("User-agent: GPTBot\nDisallow: /\n")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump({"prefixes": [{"ipv4Prefix": "20.171.207.0/24"}]}, fh)
        rep = logs.analyse(self.LOG, lambda t: rb, {"GPTBot": logs.load_ranges(fh.name)})
        os.unlink(fh.name)
        g = rep.agents["GPTBot"]
        self.assertEqual((g.requests, g.verified, g.spoofed, g.disallowed_fetches_verified), (2, 1, 1, 1))
        self.assertEqual(rep.referrals, {"OpenAI": 1})
        self.assertEqual(rep.crawl_to_referral["OpenAI"], 1.0)
        self.assertEqual(rep.parsed, 4)


class TestCLI(unittest.TestCase):
    def run_cli(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(list(args))
        return code, buf.getvalue()

    def test_compile_then_audit_then_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = self.run_cli("compile", POLICY, "-o", d)
            self.assertEqual(code, 0)
            self.assertIn("self-verification: PASS", out)
            code, out = self.run_cli("audit", "--robots", os.path.join(d, "robots.txt"), "--json")
            self.assertEqual(json.loads(out)["reservation"]["intent"], "deny")
            led = os.path.join(d, "ledger")
            self.run_cli("evidence", "add", led, "--url", "https://x/robots.txt", "--file", os.path.join(d, "robots.txt"))
            code, out = self.run_cli("evidence", "verify", led)
            self.assertIn("intact", out)
            code, out = self.run_cli("evidence", "tsq", led, "-o", os.path.join(d, "head.tsq"))
            self.assertTrue(os.path.getsize(os.path.join(d, "head.tsq")) > 40)

    def test_module_entrypoint(self):
        r = subprocess.run([sys.executable, "-m", "novarys", "markets"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Japan", r.stdout)


if __name__ == "__main__":
    unittest.main()
