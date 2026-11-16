"""Benchmark NOVARYS against the robots.txt parsers real crawlers use, and on real files.

1. Conformance: Google's reference test-suite (142 assertions extracted from
   github.com/google/robotstxt robots_test.cc) run against
   - NOVARYS (novarys.robots),
   - Python urllib.robotparser (stdlib, used by many Python crawlers),
   - Protego (Scrapy's default parser), if installed.
2. Real files: robots.txt of Tranco top-10k sites flagged by the November 2026
   allow-list study (github.com/Ghaith-Abdullah/robots-ai-allowlist-study-2026).
   We measure how often the three parsers disagree on whether a major AI agent
   may fetch the site root or a disallowed sample path, and what NOVARYS finds.

Usage:
  python studies/benchmark.py --flagged path/to/flagged-robots-files.jsonl.gz [--out studies/results]
(the third-party robots.txt files are not redistributed here).
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import os
import sys
import urllib.robotparser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from novarys import audit, robots  # noqa: E402

try:
    from protego import Protego  # type: ignore
except ImportError:  # pragma: no cover
    Protego = None

FIXTURE = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "google_robots_conformance.json")
AI = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot",
      "CCBot", "Google-Extended", "Bytespider", "Amazonbot", "meta-externalagent", "Applebot-Extended"]


def novarys_parser(text):
    rb = robots.parse(text)
    return lambda ua, path: rb.can_fetch(ua, path)


def urllib_parser(text):
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(text.splitlines())
    return lambda ua, path: rp.can_fetch(ua, "http://example.invalid" + path)


def protego_parser(text):
    rp = Protego.parse(text)
    return lambda ua, path: rp.can_fetch("http://example.invalid" + path, ua)


PARSERS = {"novarys": novarys_parser, "python-urllib": urllib_parser}
if Protego is not None:
    PARSERS["protego (Scrapy)"] = protego_parser


def path_of(url):
    from urllib.parse import urlsplit
    if not url:
        return "/"
    if "://" not in url:
        url = "//" + url
    p = urlsplit(url)
    return (p.path or "/") + ("?" + p.query if p.query else "")


def conformance():
    with open(FIXTURE, encoding="utf-8") as fh:
        suite = json.load(fh)
    res = {}
    for name, factory in PARSERS.items():
        ok = tot = 0
        for t in suite:
            for c in t["cases"]:
                tot += 1
                try:
                    got = factory(c["robots"])(c["agent"], path_of(c["url"])) if c["agent"] else True
                except Exception:
                    got = None
                ok += got == c["expected"]
        res[name] = {"passed": ok, "total": tot, "rate": round(100 * ok / tot, 1)}
    return res


def real_files(path):
    n = 0
    root_div = collections.Counter()
    path_div_files = collections.Counter()
    any_root_div_files = 0
    findings = collections.Counter()
    sev_files = collections.Counter()
    scores = []
    for line in gzip.open(path, "rt", encoding="utf-8"):
        rec = json.loads(line)
        text = rec["robots_txt"]
        n += 1
        ps = {k: f(text) for k, f in PARSERS.items()}
        rb = robots.parse(text)
        probe = ["/"] + sorted({robots.sample_path(r.pattern) for g in rb.groups for r in g.rules})[:60]
        file_root_div = False
        file_path_div = set()
        for ua in AI:
            root = {k: p(ua, "/") for k, p in ps.items()}
            if len(set(root.values())) > 1:
                file_root_div = True
                root_div[ua] += 1
            for pth in probe:
                vals = {k: p(ua, pth) for k, p in ps.items()}
                if len(set(vals.values())) > 1:
                    for k in ps:
                        if k != "novarys" and vals[k] != vals["novarys"]:
                            file_path_div.add(k)
        any_root_div_files += file_root_div
        for k in file_path_div:
            path_div_files[k] += 1
        rep = audit.audit(audit.Inputs(robots_txt=text, jurisdictions=["EU"]))
        codes = {f.code for f in rep.findings}
        for c in codes:
            findings[c] += 1
        if any(f.severity in ("critical", "high") for f in rep.findings):
            sev_files["high_or_critical"] += 1
        if rep.reservation["score"] is not None:
            scores.append(rep.reservation["score"])
    scores.sort()
    med = scores[len(scores) // 2] if scores else None
    return {
        "files": n,
        "files_where_parsers_disagree_on_root_access_for_an_AI_agent": any_root_div_files,
        "root_disagreements_by_agent": dict(sorted(root_div.items(), key=lambda kv: (-kv[1], kv[0]))),
        "files_where_parser_disagrees_with_novarys_on_some_path": dict(path_div_files),
        "novarys_findings_files_per_code": dict(sorted(findings.items(), key=lambda kv: (-kv[1], kv[0]))),
        "files_with_high_or_critical_finding": sev_files["high_or_critical"],
        "training_optout_files_scored": len(scores),
        "reservation_score_median": med,
        "reservation_score_ge_80": sum(1 for s in scores if s >= 80),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flagged", help="flagged-robots-files.jsonl.gz from the allow-list study")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results"))
    a = ap.parse_args()
    out = {"parsers": list(PARSERS), "google_conformance": conformance()}
    if a.flagged:
        out["real_files"] = real_files(a.flagged)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "benchmark.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
