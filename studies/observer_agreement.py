"""Do two independent observers see the same reservation for the same site?

Compares two public robots.txt scans of the same domains:
- Crawlora AI-Crawler Blocking Index (Tranco top 1M, 2026-06-20, CC BY 4.0)
- robots.txt AI allow-list study (Tranco top 10k, 2026-11-06, results CC BY 4.0)

Measures (1) agreement on whether a robots.txt could be read at all, and
(2) for the raw files published by the second study, agreement on whether a
given AI agent is fully blocked (re-parsed with NOVARYS) vs the first scan.
Differences mix real changes over 5 months, fetch failures (e.g. 403 to data
-centre IPs) and parser differences: exactly the noise a neutral, timestamped
reference observation must remove.

Usage: python studies/observer_agreement.py CRAWLORA_results.jsonl.gz GHAITH_DATA_DIR [--out studies/results]
"""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from novarys import robots  # noqa: E402

COMMON = ["gptbot", "oai-searchbot", "chatgpt-user", "claudebot", "anthropic-ai", "perplexitybot",
          "bytespider", "ccbot", "amazonbot", "meta-externalagent", "cohere-ai"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("crawlora")
    ap.add_argument("ghaith_dir")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results"))
    a = ap.parse_args()
    with open(os.path.join(a.ghaith_dir, "results.csv"), encoding="utf-8") as fh:
        g = {r["domain"]: r for r in csv.DictReader(fh) if r["sample"] == "tranco-top-10000"}
    c = {}
    for line in gzip.open(a.crawlora, "rt", encoding="utf-8"):
        r = json.loads(line)
        if r["domain"] in g:
            c[r["domain"]] = r
    both = sorted(set(g) & set(c))
    conf = collections.Counter()
    for d in both:
        conf[(bool(c[d]["has_robots"]), g[d]["outcome"] == "read")] += 1
    readable_agree = conf[(True, True)] + conf[(False, False)]
    # per-agent comparison on raw files
    per = collections.Counter()
    files = 0
    file_disagree = 0
    for line in gzip.open(os.path.join(a.ghaith_dir, "flagged-robots-files.jsonl.gz"), "rt", encoding="utf-8"):
        rec = json.loads(line)
        d = rec["domain"]
        if d not in c or not c[d]["has_robots"]:
            continue
        files += 1
        rb = robots.parse(rec["robots_txt"])
        cb = set(c[d]["blocks_ai"])
        dis = False
        for bot in COMMON:
            now = rb.fully_blocked(bot)
            then = bot in cb
            per[(bot, then, now)] += 1
            if now != then:
                dis = True
        file_disagree += dis
    agents = {}
    for bot in COMMON:
        tt, tf, ft, ff = (per[(bot, True, True)], per[(bot, True, False)], per[(bot, False, True)], per[(bot, False, False)])
        agents[bot] = {"blocked_both": tt, "blocked_june_only": tf, "blocked_november_only": ft, "open_both": ff,
                       "agreement_pct": round(100 * (tt + ff) / max(1, tt + tf + ft + ff), 1)}
    res = {
        "domains_in_both_scans": len(both),
        "robots_readable": {"both": conf[(True, True)], "june_only": conf[(True, False)], "november_only": conf[(False, True)],
                            "neither": conf[(False, False)], "agreement_pct": round(100 * readable_agree / len(both), 1)},
        "flagged_files_compared": files,
        "files_with_at_least_one_agent_disagreement": file_disagree,
        "per_agent": agents,
        "caveat": "Scans are 5 months apart: disagreement mixes real policy changes, fetch failures and parser differences.",
    }
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "observer_agreement.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
