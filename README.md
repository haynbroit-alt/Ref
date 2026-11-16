# NOVARYS OMNISEARCH

**AI visibility & content-rights compliance engine.** One declarative policy,
compiled into every machine-readable signal AI systems read, audited for its
*legal effect* in 30 markets, checked against how real crawlers parse it, and
backed by tamper-evident evidence.

> Rapport de recherche et décision GO/NO-GO (FR) : [`docs/RAPPORT.md`](docs/RAPPORT.md)

## Why

Measured on real data (see `studies/`):

- Among the 80,598 sites of the Tranco top 1M that block at least one AI-training
  crawler, **36.5 %** still leave another core training crawler allowed. In the
  8 EU markets where the opt-out *is* the legal mechanism (DSM Directive
  Art. 4(3)), the figure is **57.4 %** (53.5 % counting only pure training crawlers),
  versus 35.2 % for `.com`.
- 2,138 sites block only Anthropic's legacy tokens (`anthropic-ai`, `claude-web`)
  and not `ClaudeBot`.
- A Dutch court held that a robots.txt naming specific AI bots is not a general
  reservation against other bots (Rb Amsterdam, 30 Oct 2024, ECLI:NL:RBAMS:2024:6563).
- On 385 robots.txt files of top-10k sites, the three parsers used by real
  crawlers (Google/RFC 9309 semantics, Python `urllib`, Scrapy's Protego)
  disagree on whether a major AI agent may fetch the site root in 31 files.
  Among the 168 files expressing a training opt-out, the median NOVARYS
  reservation-robustness score is 60/100 and only 27 score 80 or more.
  This sample was selected by the source study for its findings, so it is not
  representative of all sites.

## What it does

| Module | Command | Output |
|---|---|---|
| Policy compiler | `novarys compile policy.json -o out/` | canonical `robots.txt` (incl. the vendor-neutral `__usage_ai-training` group, AIPREF `Content-Usage`, `Content-Signal`), `/.well-known/tdmrep.json`, HTTP headers + nginx snippet, meta tags, RSL `license.xml`, reservation statements (EN/FR/DE + market notes), hashed manifest. **Self-verified** against the policy for every known agent under two parser dialects. |
| Auditor | `novarys audit --robots robots.txt [--headers h.json --html page.html --tdmrep tdmrep.json --tos terms.txt] --jurisdiction EU,FR,JP,US,UK` | effective access per agent, contradictions (partial opt-outs, obsolete tokens, wildcard escapes, parser divergence, ambiguous groups, Google-Extended misconceptions), reservation-robustness score with its formula, legal effect per market, visibility eligibility per AI answer surface |
| Log verifier | `novarys logs access.log --ledger evidence/ --url https://site/robots.txt --ranges GPTBot=gptbot.json` | per agent: requests, verified vs spoofed (vendor IP ranges), fetches of disallowed paths under the robots.txt in force at that time, AI referrals, crawl-to-referral ratio. Human IPs are never output. |
| Evidence ledger | `novarys evidence add|verify|list|tsq DIR` | append-only hash-chained snapshots; RFC 3161 timestamp request (DER) for the head hash, to send to any TSA |
| Knowledge base | `novarys registry`, `novarys markets` | 39 AI/search agents with purpose, effect, verification source and verification status; 30 markets + EU baseline |

Pure Python ≥ 3.10, no dependencies, works offline.

```bash
pip install -e .
novarys compile examples/policy-media-fr.json -o out/
novarys audit --robots out/robots.txt --tdmrep out/.well-known/tdmrep.json --jurisdiction EU,FR,JP
python -m unittest discover -s tests      # 40 tests, incl. Google's reference suite
```

## Measured quality

| Benchmark | NOVARYS | Python urllib.robotparser | Protego (Scrapy) |
|---|---:|---:|---:|
| Google reference robots.txt test-suite (142 assertions) | **142 (100 %)** | 128 (90.1 %) | 130 (91.5 %) |

Reproduce: `python studies/benchmark.py --flagged <flagged-robots-files.jsonl.gz>` and
`python studies/market_gap.py <results.jsonl.gz>` (datasets: see `NOTICE`).

## Status of the knowledge base

Every agent and market carries a status: `verified` (checked on the vendor's
live page), `reported` (from search summaries of official pages) or
`unverified`/`unresearched`. Several vendor pages and primary legal sources could
not be opened from the research environment; see `docs/RAPPORT.md` §8.
**Research aid, not legal advice.**
