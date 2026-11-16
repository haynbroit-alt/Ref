import unittest

from novarys.robots import decide, escaped_wildcard_rules, interpret_status, parse
from novarys.dialects import root_divergence


class TestRFC9309(unittest.TestCase):
    def test_longest_match_and_allow_tie(self):
        r = parse("User-agent: *\nDisallow: /a\nAllow: /a/b\nDisallow: /x\nAllow: /x\n")
        self.assertFalse(r.can_fetch("bot", "/a/c"))
        self.assertTrue(r.can_fetch("bot", "/a/b/c"))
        self.assertTrue(r.can_fetch("bot", "/x"))  # tie -> allow

    def test_wildcards_and_anchor(self):
        r = parse("User-agent: *\nDisallow: /*.pdf$\nDisallow: /private*/\n")
        self.assertFalse(r.can_fetch("bot", "/docs/file.pdf"))
        self.assertTrue(r.can_fetch("bot", "/docs/file.pdf?x=1"))
        self.assertFalse(r.can_fetch("bot", "/private-zone/a"))
        self.assertTrue(r.can_fetch("bot", "/public/"))

    def test_pathological_wildcards_do_not_hang(self):
        r = parse("User-agent: *\nDisallow: /" + "*" * 200 + "a$\n")
        self.assertTrue(r.can_fetch("bot", "/" + "b" * 5000))

    def test_named_group_replaces_star(self):
        r = parse("User-agent: *\nDisallow: /cart/\n\nUser-agent: GPTBot\nAllow: /\n")
        self.assertTrue(r.can_fetch("GPTBot", "/cart/1"))
        self.assertFalse(r.can_fetch("Bingbot", "/cart/1"))
        esc = escaped_wildcard_rules(r, "gptbot")
        self.assertEqual([e.rule.pattern for e in esc], ["/cart/"])

    def test_groups_merge_and_case_insensitive(self):
        r = parse("User-agent: gptbot\nDisallow: /a\n\nUser-agent: GPTBot\nDisallow: /b\n")
        self.assertFalse(r.can_fetch("GPTBOT", "/a"))
        self.assertFalse(r.can_fetch("GPTBOT", "/b"))

    def test_blank_line_does_not_end_group(self):
        r = parse("User-agent: GPTBot\nAllow: /\n\nDisallow: /secret\n")
        self.assertFalse(r.can_fetch("GPTBot", "/secret"))

    def test_unknown_record_does_not_split_agents(self):
        # Google's reference parser: only allow/disallow end an agent run
        r = parse("User-agent: CCBot\nCrawl-delay: 1\n\nUser-agent: Other\nDisallow: /\n")
        self.assertTrue(r.fully_blocked("CCBot"))
        self.assertIn("ambiguous-group-boundary", [l.code for l in r.lints])
        # and the legacy (urllib) reading differs
        self.assertIn("CCBot", root_divergence("User-agent: CCBot\nCrawl-delay: 1\n\nUser-agent: Other\nDisallow: /\n", ["CCBot"]))

    def test_product_token_with_version(self):
        r = parse("User-agent: GPTBot/1.2\nDisallow: /\n")
        self.assertTrue(r.fully_blocked("gptbot"))

    def test_robots_txt_always_allowed(self):
        r = parse("User-agent: *\nDisallow: /\n")
        self.assertTrue(r.can_fetch("x", "/robots.txt"))

    def test_empty_disallow_allows(self):
        r = parse("User-agent: *\nDisallow:\n")
        self.assertTrue(r.can_fetch("x", "/anything"))

    def test_other_records_kept(self):
        r = parse("User-agent: *\nContent-Signal: search=yes, ai-train=no\nAllow: /\n")
        self.assertEqual(r.records("content-signal"), ["search=yes, ai-train=no"])

    def test_percent_encoding_equivalence(self):
        r = parse("User-agent: *\nDisallow: /caf%C3%A9\n")
        from novarys.robots import encode_path
        self.assertFalse(r.can_fetch("x", encode_path("/café")))
        self.assertFalse(r.can_fetch("x", "/caf%c3%a9".upper().replace("CAF", "caf")))

    def test_status_interpretation(self):
        self.assertEqual(interpret_status(404), "allow-all")
        self.assertEqual(interpret_status(503), "disallow-all")
        self.assertEqual(interpret_status(200), "parse")

    def test_decide_empty(self):
        self.assertEqual(decide([], "/x"), (True, None))


if __name__ == "__main__":
    unittest.main()
