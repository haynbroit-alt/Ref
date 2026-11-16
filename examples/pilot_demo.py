"""End-to-end pilot rehearsal on synthetic data, using exactly the commands of docs/pilote/RUNBOOK.md.

Six synthetic publishers each:
  1. record their robots.txt in their evidence ledger and in the public log (snapshot),
  2. analyse one month of access logs against the robots.txt in force (logs --json),
  3. produce and commit their monthly metering report (meter report / meter commit).
The operator then aggregates the reports (meter aggregate), publishes the tree head
(tlog head / tlog tsq), and any party can obtain a neutral constat and verify it.

Nothing here touches the network. Usage: python examples/pilot_demo.py [WORKDIR]
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERIOD = "pilot-month-1"
GPT_RANGE = "20.171.207.0/24"
CLAUDE_RANGE = "160.79.104.0/23"


def run(*args: str) -> str:
    r = subprocess.run([sys.executable, "-m", "novarys", *args], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"command failed: novarys {' '.join(args)}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def synthetic_log(rnd: random.Random, n_gpt: int, n_claude: int, n_spoof: int, n_ref: int) -> list[str]:
    lines = []
    start = datetime.now(timezone.utc) + timedelta(hours=1)  # logs AFTER the snapshot, so compliance is assessable

    def t(day, sec):
        return (start + timedelta(days=day - 1, seconds=sec)).strftime("%d/%b/%Y:%H:%M:%S +0000")
    for i in range(n_gpt):
        path = "/premium/a%d" % i if i % 10 == 0 else "/news/a%d" % i
        lines.append(f'20.171.207.{rnd.randint(1, 250)} - - [{t(rnd.randint(1, 28), i)}] "GET {path} HTTP/1.1" 200 900 "-" '
                     '"Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)"')
    for i in range(n_claude):
        lines.append(f'160.79.104.{rnd.randint(1, 250)} - - [{t(rnd.randint(1, 28), i)}] "GET /news/c{i} HTTP/1.1" 200 900 "-" '
                     '"Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)"')
    for i in range(n_spoof):
        lines.append(f'203.0.113.{rnd.randint(1, 250)} - - [{t(rnd.randint(1, 28), i)}] "GET /news/s{i} HTTP/1.1" 200 900 "-" '
                     '"Mozilla/5.0 (compatible; GPTBot/1.2)"')
    for i in range(n_ref):
        ref = rnd.choice(["https://chatgpt.com/", "https://www.perplexity.ai/search", "https://www.google.com/"])
        lines.append(f'198.51.100.{rnd.randint(1, 250)} - - [{t(rnd.randint(1, 28), i)}] "GET /news/r{i} HTTP/1.1" 200 900 "{ref}" '
                     '"Mozilla/5.0 Firefox/130"')
    rnd.shuffle(lines)
    return lines


def main(work: str) -> dict:
    os.makedirs(work, exist_ok=True)
    rnd = random.Random(2026)
    ranges = os.path.join(work, "ranges")
    os.makedirs(ranges, exist_ok=True)
    for name, cidr in (("gptbot", GPT_RANGE), ("claudebot", CLAUDE_RANGE)):
        with open(os.path.join(ranges, f"{name}.json"), "w") as fh:
            json.dump({"prefixes": [{"ipv4Prefix": cidr}]}, fh)
    public_log = os.path.join(work, "public-log")
    reports = []
    for p in range(6):
        pub = os.path.join(work, f"publisher-{p}")
        os.makedirs(pub, exist_ok=True)
        url = f"https://news{p}.example/robots.txt"
        robots_path = os.path.join(pub, "robots.txt")
        with open(robots_path, "w") as fh:
            fh.write("User-agent: GPTBot\nDisallow: /premium/\n\nUser-agent: *\nAllow: /\n")
        run("snapshot", os.path.join(pub, "ledger"), "--url", url, "--file", robots_path, "--tlog", public_log)
        log_path = os.path.join(pub, "access.log")
        with open(log_path, "w") as fh:
            fh.write("\n".join(synthetic_log(rnd, rnd.randint(200, 600), rnd.randint(50, 150), rnd.randint(5, 30), rnd.randint(20, 80))) + "\n")
        logs_json = os.path.join(pub, "logs.json")
        with open(logs_json, "w") as fh:
            fh.write(run("logs", log_path, "--ledger", os.path.join(pub, "ledger"), "--url", url,
                         "--ranges", f"GPTBot={ranges}/gptbot.json", "--ranges", f"ClaudeBot={ranges}/claudebot.json", "--json"))
        report = os.path.join(pub, "meter.json")
        run("meter", "report", logs_json, "--publisher", f"publisher-{p}", "--period", PERIOD, "-o", report)
        run("meter", "commit", report, "--tlog", public_log, "-o", os.path.join(pub, "meter-commit-proof.json"))
        reports.append(report)
    aggregate = os.path.join(work, "aggregate.json")
    run("meter", "aggregate", *reports, "-o", aggregate)
    head = json.loads(run("tlog", "head", public_log))
    run("tlog", "tsq", public_log, "-o", os.path.join(work, "tree-head.tsq"))
    # a neutral constat for publisher 0, requested by "the AI provider"
    constat = os.path.join(work, "constat-news0.json")
    run("constat", os.path.join(work, "publisher-0", "ledger"), "--url", "https://news0.example/robots.txt",
        "--as-of", "2100-01-01T00:00:00+00:00", "--tlog", public_log, "--logs-json", os.path.join(work, "publisher-0", "logs.json"),
        "--jurisdiction", "EU,FR", "--requested-by", "ai-provider", "-o", constat, "--md", os.path.join(work, "constat-news0.md"))
    verified = "VALID" in run("constat-verify", constat)
    proofs_ok = all("VALID" in run("check", os.path.join(work, f"publisher-{p}", "meter-commit-proof.json")) for p in range(6))
    with open(aggregate) as fh:
        agg = json.load(fh)
    summary = {"publishers": 6, "public_log_size": head["tree_size"], "tree_head_sha256": head["tree_head_sha256"],
               "aggregate_vendors": sorted(agg["vendors"]), "suppressed": agg["suppressed"],
               "openai": agg["vendors"].get("OpenAI"), "constat_verified": verified, "commit_proofs_verified": proofs_ok}
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="novarys-pilot-"))
