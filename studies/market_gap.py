"""Intent-vs-implementation gap of AI-training opt-outs across 30 markets.

Data: Crawlora "AI-Crawler Blocking Index" (Tranco top 1M, scanned 2026-06-20,
CC BY 4.0, github.com/Crawlora-org/ai-crawler-blocking-index-data). Each record
lists the AI user-agents a domain names and fully blocks ('Disallow: /').

Market proxy: country-code TLD (.fr, .de, .jp, ...); '.com/.us' stands in for
the US and is a global mix, so treat it with caution.

A site "expresses a training opt-out" when it fully blocks at least one core
training agent and does not block every bot with 'User-agent: *'. For those
sites we measure which other core training agents remain allowed.

Usage: python studies/market_gap.py path/to/results.jsonl.gz [--out studies/results]
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import os

CORE = ["gptbot", "ccbot", "claudebot", "google-extended", "meta-externalagent", "applebot-extended", "bytespider"]
SEARCH_AGENTS = ["oai-searchbot", "chatgpt-user", "perplexitybot"]
# crawlers whose only documented use is training: allowing them brings no visibility benefit,
# so leaving one open after blocking another is unlikely to be a deliberate trade-off
PURE_TRAINING = ["gptbot", "ccbot", "claudebot", "meta-externalagent", "bytespider"]
MARKETS = {
    "us": "United States (.com/.us)", "cn": "China", "jp": "Japan", "de": "Germany", "in": "India", "uk": "United Kingdom",
    "fr": "France", "it": "Italy", "ca": "Canada", "br": "Brazil", "kr": "South Korea", "au": "Australia", "es": "Spain",
    "mx": "Mexico", "id": "Indonesia", "nl": "Netherlands", "sa": "Saudi Arabia", "tr": "Turkey", "ch": "Switzerland",
    "pl": "Poland", "tw": "Taiwan", "be": "Belgium", "se": "Sweden", "sg": "Singapore", "ae": "UAE", "il": "Israel",
    "ar": "Argentina", "za": "South Africa", "th": "Thailand", "vn": "Vietnam",
}
EU_OPTOUT = {"de", "fr", "it", "es", "nl", "pl", "be", "se"}


def market(domain: str) -> str | None:
    tld = domain.rsplit(".", 1)[-1].lower()
    if tld in ("com", "us"):
        return "us"
    return tld if tld in MARKETS else None


def run(path: str) -> dict:
    by = collections.defaultdict(collections.Counter)
    missing = collections.defaultdict(collections.Counter)
    for line in gzip.open(path, "rt", encoding="utf-8"):
        r = json.loads(line)
        keys = ["ALL"]
        m = market(r["domain"])
        if m:
            keys.append(m)
            if m in EU_OPTOUT:
                keys.append("EU-8")
        b = set(r.get("blocks_ai") or [])
        star = bool(r.get("star_disallow_root"))
        core_b = [x for x in CORE if x in b]
        intent = bool(core_b) and not star
        flags = {
            "domains": True,
            "has_robots": r.get("has_robots"),
            "blocks_any_ai": bool(b),
            "training_optout": intent,
            "incomplete": intent and len(core_b) < len(CORE),
            "single_agent_only": intent and len(core_b) == 1,
            "strict_incomplete": intent and any(x not in b for x in PURE_TRAINING),
            "obsolete_anthropic_only": bool({"anthropic-ai", "claude-web"} & b) and "claudebot" not in b and not star,
            "blocks_ai_search_agents": bool(set(SEARCH_AGENTS) & b) and not star,
        }
        for k in keys:
            for f, v in flags.items():
                if v:
                    by[k][f] += 1
            if intent:
                for x in CORE:
                    if x not in b:
                        missing[k][x] += 1
    out = {}
    for k, c in by.items():
        io = c["training_optout"]
        out[k] = {
            "name": MARKETS.get(k, k), "domains": c["domains"], "with_robots": c["has_robots"],
            "blocks_any_ai_pct_of_robots": round(100 * c["blocks_any_ai"] / c["has_robots"], 1) if c["has_robots"] else None,
            "training_optout_sites": io,
            "incomplete_pct": round(100 * c["incomplete"] / io, 1) if io else None,
            "single_agent_only_pct": round(100 * c["single_agent_only"] / io, 1) if io else None,
            "strict_incomplete_pct": round(100 * c["strict_incomplete"] / io, 1) if io else None,
            "missing_pct": {x: round(100 * missing[k][x] / io, 1) for x in CORE} if io else {},
            "obsolete_anthropic_only_sites": c["obsolete_anthropic_only"],
            "blocks_ai_search_agents_pct_of_robots": round(100 * c["blocks_ai_search_agents"] / c["has_robots"], 1) if c["has_robots"] else None,
        }
    return out


def markdown(res: dict) -> str:
    rows = ["| Market | Domains | Opt-out sites | Incomplete % | Strict incomplete % | One agent only % | Missing CCBot % | missing Google-Ext % | missing ClaudeBot % | Obsolete-only (Anthropic) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    order = ["ALL", "EU-8"] + sorted((k for k in res if k not in ("ALL", "EU-8")), key=lambda k: -res[k]["training_optout_sites"])
    for k in order:
        if k not in res:
            continue
        r = res[k]
        mp = r["missing_pct"]
        rows.append(f"| {r['name'] if k not in ('ALL', 'EU-8') else ('All Tranco top 1M' if k == 'ALL' else 'EU opt-out markets (8)')} | {r['domains']:,} | {r['training_optout_sites']:,} | "
                    f"{r['incomplete_pct']} | {r['strict_incomplete_pct']} | {r['single_agent_only_pct']} | {mp.get('ccbot')} | {mp.get('google-extended')} | {mp.get('claudebot')} | {r['obsolete_anthropic_only_sites']:,} |")
    return "\n".join(rows) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results"))
    a = ap.parse_args()
    res = run(a.data)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "market_gap.json"), "w", encoding="utf-8") as fh:
        json.dump({"source": "Crawlora AI-Crawler Blocking Index, Tranco top 1M, 2026-06-20, CC BY 4.0", "core_training_agents": CORE, "markets": res}, fh, indent=1)
    md = markdown(res)
    with open(os.path.join(a.out, "market_gap.md"), "w", encoding="utf-8") as fh:
        fh.write("Source: Crawlora AI-Crawler Blocking Index (Tranco top 1M, 2026-06-20), CC BY 4.0. Analysis: NOVARYS.\n\n" + md)
    print(md)


if __name__ == "__main__":
    main()
