"""Does a neutral usage metric make publisher-AI bargaining cheaper? A falsifiable test.

Two standard models, computed numerically rather than assumed:

1. Final-offer arbitration (FOA, used by Australia's News Media Bargaining Code
   and Canada's Online News Act). The arbitrator's preferred award z is unknown
   to the parties, z ~ Normal(mu, sigma). Each side submits an offer; the
   arbitrator picks the one closer to z. Farber (1980) shows the equilibrium
   offer gap is 1/f(mu) = sigma*sqrt(2*pi). We recover it by best-response
   iteration (no closed form used in the solver) and check the prediction.
   Implication: halving the arbitrator's uncertainty halves the gap and divides
   the outcome variance (risk borne by both sides) by four.

2. Divergent expectations (the main cause of failed negotiations in the
   bargaining literature). Each party estimates the fair value with error
   N(0, s). A dispute occurs when the publisher's estimate exceeds the
   provider's by more than the total cost of litigating/arbitrating (2c).
   P(dispute) = 1 - Phi(2c / (s*sqrt(2))). Monte Carlo confirms it.

The empirical anchor for s: published crawl-to-referral ratios for the same AI
vendor differ by several-fold between measurement providers (see
MEASUREMENT_SPREAD below), i.e. today the parties do not share a metric.

Usage: python studies/arbitration_sim.py [--out studies/results]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics

# Crawl-to-referral ratios reported for the same vendor by different sources
# (different periods and methods: this illustrates disagreement, it is not a
# controlled comparison). Sources: Cloudflare blog Aug 2025; TollBit via Digiday
# (Q4 2024-Q1 2025). See docs/ARBITRE.md.
MEASUREMENT_SPREAD = {
    "Anthropic": {"cloudflare_aug2025": 50000, "tollbit_q1_2025": 8692},
    "OpenAI": {"cloudflare_aug2025": 887, "tollbit_q1_2025": 179},
    "Perplexity": {"cloudflare_aug2025": 118, "tollbit_q1_2025": 369},
}


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def pdf(x: float, mu: float, sigma: float) -> float:
    return math.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * math.sqrt(2 * math.pi))


def expected_award(a: float, p: float, mu: float, sigma: float) -> float:
    """Expected payment when the provider offers a and the publisher asks p (a < p)."""
    m = (a + p) / 2
    prob_p = 1 - phi((m - mu) / sigma)
    return a + (p - a) * prob_p


def best_response_publisher(a, mu, sigma, grid):
    return max(grid, key=lambda p: expected_award(a, p, mu, sigma) if p > a else -1e18)


def best_response_provider(p, mu, sigma, grid):
    return min(grid, key=lambda a: expected_award(a, p, mu, sigma) if a < p else 1e18)


def foa_equilibrium(mu: float, sigma: float, iters: int = 60) -> tuple[float, float]:
    lo, hi = mu - 6 * sigma, mu + 6 * sigma
    a, p = mu - sigma, mu + sigma
    step = sigma / 40
    for _ in range(iters):
        grid_p = [p + k * step for k in range(-40, 41)]
        p = best_response_publisher(a, mu, sigma, [x for x in grid_p if lo < x < hi])
        grid_a = [a + k * step for k in range(-40, 41)]
        a = best_response_provider(p, mu, sigma, [x for x in grid_a if lo < x < hi])
        step = max(step * 0.93, sigma / 4000)
    return a, p


def dispute_probability_mc(s: float, c: float, n: int = 200_000, seed: int = 7) -> float:
    rnd = random.Random(seed)
    hits = 0
    for _ in range(n):
        if rnd.gauss(0, s) - rnd.gauss(0, s) > 2 * c:
            hits += 1
    return hits / n


def run() -> dict:
    mu = 100.0  # fair annual licence value (arbitrary unit)
    foa = []
    for sigma in (40.0, 20.0, 10.0):
        a, p = foa_equilibrium(mu, sigma)
        gap = p - a
        predicted = sigma * math.sqrt(2 * math.pi)
        foa.append({"arbitrator_uncertainty_sigma": sigma, "provider_offer": round(a, 2), "publisher_offer": round(p, 2),
                    "gap_computed": round(gap, 2), "gap_farber_prediction": round(predicted, 2),
                    "relative_error_pct": round(100 * abs(gap - predicted) / predicted, 2),
                    "outcome_std_dev": round(gap / 2, 2)})
    disputes = []
    c = 5.0  # each side's cost of a contested procedure: 5% of the deal value
    for s in (60.0, 30.0, 15.0, 7.5):
        analytic = 1 - phi(2 * c / (s * math.sqrt(2)))
        mc = dispute_probability_mc(s, c)
        disputes.append({"valuation_error_s_pct_of_value": s, "dispute_probability_analytic": round(analytic, 4),
                         "dispute_probability_monte_carlo": round(mc, 4),
                         "expected_procedure_cost_per_deal_pct": round(100 * analytic * 2 * c / mu, 2)})
    spread = {}
    for vendor, d in MEASUREMENT_SPREAD.items():
        vals = list(d.values())
        spread[vendor] = {"values": d, "max_over_min": round(max(vals) / min(vals), 1),
                          "log10_std": round(statistics.pstdev([math.log10(v) for v in vals]), 2)}
    return {"assumptions": {"fair_value_mu": mu, "procedure_cost_c_each": c, "risk_neutral_parties": True},
            "final_offer_arbitration": foa, "divergent_expectations": disputes,
            "measurement_disagreement_today": spread}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results"))
    a = ap.parse_args()
    res = run()
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "arbitration_sim.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
