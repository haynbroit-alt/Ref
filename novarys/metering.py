"""Neutral AI-usage metering: per-publisher reports and a privacy-preserving aggregate.

Why: deciders that value content (Canada Online News Act s.38 "value added"
and "benefits", Indonesia Perpres 32/2024 Art. 7(3) "economic value", STIM's
mandatory third-party attribution, French CPI L.218-4 information duties)
need usage figures both sides accept. Today published ratios for the same
vendor differ by 3-6x between sources (studies/arbitration_sim.py).

Rules:
- Metric definitions are fixed and versioned (METRICS), computed from the
  publisher's own server logs by novarys.logs, counting only requests whose
  crawler identity was verified or not refuted (spoofed requests excluded).
- No price, rate or deal information is collected or reported, to avoid any
  exchange of competitively sensitive information between publishers
  (Art. 101 TFEU, Code de commerce L.420-1).
- The aggregate suppresses any cell with fewer than K_MIN publishers, and
  suppresses totals when a single publisher contributes more than
  DOMINANCE_MAX of them (dominance rule of statistical disclosure control),
  so it never reveals one publisher's figure.
- Each publisher report is committed to the transparency log, so a publisher
  can check its report entered the aggregate without revealing it.
"""
from __future__ import annotations

import hashlib
import json
import statistics

from . import registry, transparency

METHOD = "novarys-metering/0.1"
K_MIN = 5
DOMINANCE_MAX = 0.70  # suppress totals when one publisher contributes more than 70% of a vendor's requests
METRICS = {
    "requests_not_spoofed": "requests from the vendor's declared agents, minus those from IPs outside its published ranges",
    "requests_verified": "requests whose source IP is inside the vendor's published ranges",
    "disallowed_fetches_verified": "verified requests for paths disallowed by the robots.txt in force at request time",
    "referrals": "human visits whose Referer is one of the vendor's AI assistants",
    "crawl_to_referral": "requests_not_spoofed of training/answer/mixed agents divided by referrals (null if no referral)",
    "not_assessable": "requests made when no robots.txt snapshot was in force (compliance cannot be assessed)",
}


def publisher_report(logs_report: dict, publisher_id: str, period: str) -> dict:
    by_vendor: dict[str, dict] = {}
    for tok, s in logs_report.get("agents", {}).items():
        a = registry.agent(tok)
        op = a.operator if a else s.get("operator", "unknown")
        v = by_vendor.setdefault(op, {"requests_not_spoofed": 0, "requests_verified": 0, "disallowed_fetches_verified": 0,
                                      "referrals": 0, "by_purpose": {}})
        ns = s["requests"] - s["spoofed"]
        v["requests_not_spoofed"] += ns
        v["requests_verified"] += s["verified"]
        v["disallowed_fetches_verified"] += s.get("disallowed_fetches_verified", 0)
        v["not_assessable"] = v.get("not_assessable", 0) + s.get("not_assessable", 0)
        purpose = a.purpose if a else s.get("purpose", "mixed")
        v["by_purpose"][purpose] = v["by_purpose"].get(purpose, 0) + ns
    for op, n in logs_report.get("referrals", {}).items():
        by_vendor.setdefault(op, {"requests_not_spoofed": 0, "requests_verified": 0, "disallowed_fetches_verified": 0,
                                  "referrals": 0, "by_purpose": {}})["referrals"] += n
    for op, v in by_vendor.items():
        crawl = sum(n for p, n in v["by_purpose"].items() if p in ("training", "ai_answers", "mixed"))
        v["crawl_to_referral"] = round(crawl / v["referrals"], 2) if v["referrals"] else None
    return {"method": METHOD, "publisher_id": publisher_id, "period": period, "vendors": by_vendor}


def commit_report(report: dict, log: transparency.Log) -> dict:
    digest = hashlib.sha256(transparency.canonical(report)).hexdigest()
    idx = log.append({"type": "metering-report", "method": METHOD, "period": report["period"],
                      "publisher_id_sha256": hashlib.sha256(report["publisher_id"].encode()).hexdigest(),
                      "report_sha256": digest})
    return log.prove(idx)


def _quantiles(xs: list[float]) -> dict:
    xs = sorted(xs)
    if len(xs) < 2:
        return {"median": xs[0] if xs else None}
    q = statistics.quantiles(xs, n=4, method="inclusive")
    return {"p25": round(q[0], 2), "median": round(q[1], 2), "p75": round(q[2], 2)}


def aggregate(reports: list[dict], k_min: int = K_MIN, dominance_max: float = DOMINANCE_MAX) -> dict:
    periods = {r["period"] for r in reports}
    if len(periods) != 1:
        raise ValueError("aggregate reports of a single period")
    vendors: dict[str, list[dict]] = {}
    for r in reports:
        for op, v in r["vendors"].items():
            vendors.setdefault(op, []).append(v)
    out = {"method": METHOD, "period": periods.pop(), "publishers": len(reports), "k_min": k_min,
           "dominance_max": dominance_max, "vendors": {}, "suppressed": []}
    for op, vs in sorted(vendors.items()):
        if len(vs) < k_min:
            out["suppressed"].append(op)
            continue
        req = sum(v["requests_not_spoofed"] for v in vs)
        ver = sum(v["requests_verified"] for v in vs)
        dis = sum(v["disallowed_fetches_verified"] for v in vs)
        na = sum(v.get("not_assessable", 0) for v in vs)
        ratios = [v["crawl_to_referral"] for v in vs if v["crawl_to_referral"] is not None]
        dominant = req > 0 and max(v["requests_not_spoofed"] for v in vs) > dominance_max * req
        out["vendors"][op] = {
            "publishers_contributing": len(vs),
            "requests_not_spoofed_total": "suppressed (dominance rule)" if dominant else req,
            "verified_share": round(ver / req, 3) if req else None,
            "disallowed_fetch_rate_verified": round(dis / ver, 4) if ver else None,
            "not_assessable_share": round(na / req, 3) if req else None,
            "crawl_to_referral": _quantiles(ratios) if len(ratios) >= k_min else "suppressed (fewer than k publishers with referrals)",
        }
    return out
