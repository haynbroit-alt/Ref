"""The figures quoted in README and reports must match the committed study results.

If a study is re-run and a number changes, this test fails until the documents
are updated: the reports cannot silently drift from the data.
"""
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "studies", "results", name), encoding="utf-8") as fh:
        return json.load(fh)


def doc(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def fr(x, digits=1):
    return f"{x:.{digits}f}".replace(".", ",")


def fr_int(n):
    return f"{n:,}".replace(",", " ")


class TestClaims(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme, cls.rapport, cls.arbitre = doc("README.md"), doc("docs/RAPPORT.md"), doc("docs/ARBITRE.md")

    def assertIn_(self, needle, text, where):
        self.assertIn(needle, text, f"'{needle}' not found in {where}")

    def test_market_gap(self):
        m = load("market_gap.json")["markets"]
        all_, eu, us = m["ALL"], m["EU-8"], m["us"]
        for v in (all_["incomplete_pct"], eu["incomplete_pct"], eu["strict_incomplete_pct"], us["incomplete_pct"]):
            self.assertIn_(f"{v} %", self.readme, "README")
            self.assertIn_(f"{fr(v)} %", self.rapport, "RAPPORT")
        self.assertIn_(f"{all_['obsolete_anthropic_only_sites']:,}", self.readme, "README")
        self.assertIn_(fr_int(all_["obsolete_anthropic_only_sites"]), self.rapport, "RAPPORT")
        self.assertIn_(fr_int(all_["training_optout_sites"]), self.rapport, "RAPPORT")
        self.assertIn_(f"{all_['training_optout_sites']:,}", self.readme, "README")

    def test_benchmark(self):
        b = load("benchmark.json")
        c = b["google_conformance"]
        self.assertEqual((c["novarys"]["passed"], c["novarys"]["total"]), (142, 142))
        self.assertIn_(f"{c['python-urllib']['passed']} ({c['python-urllib']['rate']} %)", self.readme, "README")
        self.assertIn_(f"{c['protego (Scrapy)']['passed']} ({c['protego (Scrapy)']['rate']} %)", self.readme, "README")
        self.assertIn_(f"{fr(c['python-urllib']['rate'])} %", self.rapport, "RAPPORT")
        self.assertIn_(f"{fr(c['protego (Scrapy)']['rate'])} %", self.rapport, "RAPPORT")
        r = b["real_files"]
        self.assertIn_(f"{r['files_where_parsers_disagree_on_root_access_for_an_AI_agent']} files", self.readme, "README")
        self.assertIn_(f"{r['files_where_parsers_disagree_on_root_access_for_an_AI_agent']} fichiers", self.rapport, "RAPPORT")
        self.assertIn_(f"{r['reservation_score_median']}/100", self.rapport, "RAPPORT")
        self.assertIn_(f"seuls {r['reservation_score_ge_80']} atteignent", self.rapport, "RAPPORT")
        self.assertIn_(f"{r['files_with_high_or_critical_finding']} ont au moins un constat grave", self.rapport, "RAPPORT")
        self.assertIn_(f"{r['training_optout_files_scored']} fichiers", self.rapport, "RAPPORT")

    def test_observer_agreement(self):
        o = load("observer_agreement.json")
        disagree = round(100 - o["robots_readable"]["agreement_pct"], 1)
        self.assertIn_(f"{fr(disagree)} %", self.arbitre, "ARBITRE")
        changed = round(100 * o["files_with_at_least_one_agent_disagreement"] / o["flagged_files_compared"])
        self.assertIn_(f"{changed} %", self.arbitre, "ARBITRE")
        self.assertIn_(fr_int(o["domains_in_both_scans"]), self.arbitre, "ARBITRE")

    def test_arbitration_sim(self):
        a = load("arbitration_sim.json")
        d = a["divergent_expectations"]
        hi, lo = round(100 * d[0]["dispute_probability_analytic"]), round(100 * d[-1]["dispute_probability_analytic"])
        self.assertIn_(f"{hi} % → {lo} %", self.arbitre, "ARBITRE")
        self.assertTrue(all(row["relative_error_pct"] <= 0.01 for row in a["final_offer_arbitration"]))
        ratios = [v["max_over_min"] for v in a["measurement_disagreement_today"].values()]
        self.assertGreaterEqual(min(ratios), 3)
        self.assertLessEqual(max(ratios), 6)

    def test_registry_and_merkle(self):
        r = load("registry_scale.json")
        self.assertTrue(r["all_1000_proofs_verified"] and r["tamper_detected"] and r["consistency_900k_to_full_verified"])
        self.assertIn_(fr_int(r["records"]), self.arbitre, "ARBITRE")
        self.assertIn_(f"{r['proof_bytes']} octets", self.arbitre, "ARBITRE")
        m = load("merkle_exhaustive.json")
        self.assertEqual(m["failures"], 0)
        self.assertIn_(fr_int(m["checks"]), self.arbitre, "ARBITRE")

    def test_canary(self):
        s = {row["scenario"]: row for row in load("canary_preregistration.json")["scenarios"]}
        shifted = s["null, 0.2 SD shift in comparison text"]
        self.assertIn_(f"{fr(100 * shifted['rejection_rate_preregistered_paired'])} %", self.arbitre, "ARBITRE")
        self.assertIn_(f"{round(100 * shifted['rejection_rate_naive_unpaired'])} %", self.arbitre, "ARBITRE")


if __name__ == "__main__":
    unittest.main()
