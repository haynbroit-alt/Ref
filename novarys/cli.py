"""Command-line interface: python -m novarys <command> ..."""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__, audit as audit_mod, canary, compiler, constat, evidence, logs, metering, registry, robots, transparency

ICON = {"critical": "!!", "high": "! ", "medium": "~ ", "low": "- ", "info": "i "}


def _read(path: str | None) -> str | None:
    if not path:
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def cmd_audit(a) -> int:
    headers = json.loads(_read(a.headers)) if a.headers else {}
    inp = audit_mod.Inputs(robots_txt=_read(a.robots), robots_status=a.status, headers=headers, html=_read(a.html),
                           tdmrep_json=_read(a.tdmrep), tos_text=_read(a.tos),
                           jurisdictions=[j.strip().upper() for j in a.jurisdiction.split(",") if j.strip()],
                           intent_training=a.training)
    rep = audit_mod.audit(inp)
    d = rep.to_dict()
    if a.json:
        print(json.dumps(d, indent=2, ensure_ascii=False))
        return 0
    res = d["reservation"]
    print(f"NOVARYS OMNISEARCH audit  (registry {d['registry_version']}, robots.txt: {d['robots_interpretation']})")
    print(f"\nAI-training intent: {res['intent']}")
    if res["score"] is not None:
        print(f"Reservation robustness score: {res['score']}/100  {res['score_parts']}")
    print(f"\nFindings ({len(d['findings'])}):")
    for f in d["findings"]:
        print(f"  {ICON.get(f['severity'], '  ')}[{f['severity']}] {f['code']}: {f['title']}")
        print(f"      {f['detail']}")
        if f["fix"]:
            print(f"      fix: {f['fix']}")
    print("\nLegal effect of the reservation by market:")
    for j in d["jurisdictions"]:
        print(f"  {j['code']:3} {j.get('effect', '?'):9} {j.get('explanation', '')}")
    print("\nVisibility in AI answer surfaces (eligibility, not ranking):")
    for v in d["visibility"]:
        print(f"  {v['state']:9} {v['surface']}  [{v['decided_by']}, registry: {v['registry_status']}]")
    print(f"\n{d['disclaimer']}")
    return 1 if any(f["severity"] in ("critical", "high") for f in d["findings"]) and a.strict else 0


def cmd_compile(a) -> int:
    pol = compiler.Policy.from_dict(json.loads(_read(a.policy)))
    files = compiler.compile_all(pol)
    for name, content in files.items():
        path = os.path.join(a.out, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"wrote {path}")
    v = compiler.verify(pol, files["robots.txt"])
    print(f"self-verification: {'PASS' if v.ok else 'FAIL'} ({len(registry.agents())} agents x both parser dialects)")
    for m in v.mismatches + v.dialect_divergences + v.lints:
        print("  ", m)
    return 0 if v.ok else 2


def cmd_verify(a) -> int:
    pol = compiler.Policy.from_dict(json.loads(_read(a.policy)))
    v = compiler.verify(pol, _read(a.robots) or "")
    print(f"{'PASS' if v.ok else 'FAIL'}: {len(v.mismatches)} mismatch(es), {len(v.dialect_divergences)} dialect divergence(s), {len(v.lints)} lint(s)")
    for m in (v.mismatches + v.dialect_divergences + v.lints)[:50]:
        print("  ", m)
    return 0 if v.ok else 2


def cmd_logs(a) -> int:
    ranges = {}
    for spec in a.ranges or []:
        tok, path = spec.split("=", 1)
        ranges[tok] = logs.load_ranges(path)
    if a.ledger:
        led = evidence.Ledger(a.ledger)
        cache: dict[str, robots.RobotsTxt] = {}

        def robots_for(t):
            e = led.state_at(a.url, t.isoformat())
            if e is None:
                return None
            if e.sha256 not in cache:
                cache[e.sha256] = robots.parse(led.content(e).decode("utf-8", "replace"))
            return cache[e.sha256]
    else:
        rb = robots.parse(_read(a.robots) or "") if a.robots else None
        robots_for = lambda t: rb
    with open(a.log, encoding="utf-8", errors="replace") as fh:
        rep = logs.analyse(fh, robots_for, ranges)
    d = rep.to_dict()
    if a.json:
        print(json.dumps(d, indent=2, default=str))
        return 0
    print(f"{d['parsed']}/{d['lines']} lines parsed")
    print(f"{'agent':22} {'req':>7} {'verified':>8} {'spoofed':>7} {'unverif':>7} {'disallowed':>10}")
    for tok, s in d["agents"].items():
        print(f"{tok:22} {s['requests']:7d} {s['verified']:8d} {s['spoofed']:7d} {s['unverifiable']:7d} {s['disallowed_fetches']:10d}")
        for v in s["sample_disallowed_fetches"]:
            print(f"    {v}")
    print("AI referrals:", d["referrals"])
    print("crawl-to-referral ratio:", d["crawl_to_referral"])
    for n in d["notes"]:
        print("note:", n)
    return 0


def cmd_evidence(a) -> int:
    led = evidence.Ledger(a.dir)
    if a.action == "add":
        with open(a.file, "rb") as fh:
            e = led.add(a.url, fh.read(), kind=a.kind)
        print(f"#{e.seq} {e.ts} {e.url} sha256={e.sha256} head={e.hash}")
    elif a.action == "verify":
        probs = led.verify()
        print("ledger intact" if not probs else "\n".join(probs))
        return 0 if not probs else 3
    elif a.action == "tsq":
        head = led.head()
        with open(a.out, "wb") as fh:
            fh.write(evidence.timestamp_request(head))
        print(f"RFC 3161 request for head {head} written to {a.out}")
        print("Send it to a timestamp authority of your choice, e.g.:")
        print(f"  curl -H 'Content-Type: application/timestamp-query' --data-binary @{a.out} <TSA-URL> -o head.tsr")
    elif a.action == "list":
        for e in led.entries():
            print(f"#{e.seq} {e.ts} {e.kind:9} {e.url} {e.sha256[:16]}")
    return 0


def _write_json(obj, path):
    text = json.dumps(obj, indent=2, ensure_ascii=False)
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"wrote {path}")
    else:
        print(text)


def cmd_tlog(a) -> int:
    log = transparency.Log(a.dir)
    if a.action == "append":
        idx = log.append(json.loads(a.record))
        print(f"appended #{idx}; head {log.head().to_dict()}")
    elif a.action == "head":
        h = log.head()
        print(json.dumps({**h.to_dict(), "tree_head_sha256": h.digest()}, indent=2))
    elif a.action == "prove":
        _write_json(log.prove(a.index), a.out)
    elif a.action == "consistency":
        _write_json(log.prove_consistency(a.index), a.out)
    elif a.action == "tsq":
        h = log.head()
        with open(a.out or "tree-head.tsq", "wb") as fh:
            fh.write(evidence.timestamp_request(h.digest()))
        print(f"RFC 3161 request for tree head {h.digest()} (size {h.size}) written to {a.out or 'tree-head.tsq'}")
    return 0


def cmd_check(a) -> int:
    with open(a.proof, encoding="utf-8") as fh:
        p = json.load(fh)
    ok = transparency.check_consistency(p) if "old_size" in p else transparency.check_inclusion(p)
    print("VALID" if ok else "INVALID")
    return 0 if ok else 4


def cmd_snapshot(a) -> int:
    led = evidence.Ledger(a.ledger)
    with open(a.file, "rb") as fh:
        content = fh.read()
    e = led.add(a.url, content, kind=a.kind)
    print(f"ledger #{e.seq} {e.ts} sha256={e.sha256}")
    if a.tlog:
        idx = transparency.Log(a.tlog).append({"type": "signal-snapshot", "url": a.url, "kind": a.kind,
                                               "recorded_at": e.ts, "content_sha256": e.sha256})
        print(f"public commitment #{idx} in {a.tlog}")
    return 0


def cmd_constat(a) -> int:
    logs_report = None
    if a.logs_json:
        with open(a.logs_json, encoding="utf-8") as fh:
            logs_report = json.load(fh)
    rep = constat.build(a.ledger, a.url, a.as_of, [j.strip() for j in a.jurisdiction.split(",") if j.strip()],
                        logs_report, a.tlog, a.requested_by)
    bad = constat.neutral_wording(rep)
    if bad:
        print("refusing to emit a non-neutral report:", bad)
        return 5
    _write_json(rep, a.out)
    if a.md:
        with open(a.md, "w", encoding="utf-8") as fh:
            fh.write(constat.to_markdown(rep))
        print(f"wrote {a.md}")
    print(f"report sha256: {rep['report_sha256']}")
    return 0


def cmd_constat_verify(a) -> int:
    with open(a.report, encoding="utf-8") as fh:
        rep = json.load(fh)
    ok = constat.verify(rep)
    print("VALID" if ok else "INVALID (body was modified)")
    return 0 if ok else 4


def cmd_meter(a) -> int:
    if a.action == "report":
        with open(a.inputs[0], encoding="utf-8") as fh:
            lr = json.load(fh)
        _write_json(metering.publisher_report(lr, a.publisher, a.period), a.out)
    elif a.action == "commit":
        with open(a.inputs[0], encoding="utf-8") as fh:
            rep = json.load(fh)
        _write_json(metering.commit_report(rep, transparency.Log(a.tlog)), a.out)
    elif a.action == "aggregate":
        reps = []
        for path in a.inputs:
            with open(path, encoding="utf-8") as fh:
                reps.append(json.load(fh))
        _write_json(metering.aggregate(reps, a.k), a.out)
    return 0


def cmd_canary(a) -> int:
    if a.action == "create":
        d = canary.create(a.n)
        with open(a.secret, "w", encoding="utf-8") as fh:
            json.dump(d["secret"], fh)
        print(f"secret design (keep private) written to {a.secret}")
        if a.tlog:
            idx = transparency.Log(a.tlog).append(d["commitment"])
            print(f"commitment #{idx} appended to {a.tlog}")
        _write_json({"commitment": d["commitment"], "publish_these": d["published"]}, a.out)
    else:
        with open(a.secret, encoding="utf-8") as fh:
            secret = json.load(fh)
        if a.action == "verify":
            with open(a.inputs[0], encoding="utf-8") as fh:
                com = json.load(fh)
            ok = canary.verify_reveal(secret, com.get("commitment", com))
            print("VALID" if ok else "INVALID")
            return 0 if ok else 4
        with open(a.inputs[0], encoding="utf-8") as fh:
            scores = json.load(fh)
        _write_json(canary.test(secret, scores), a.out)
    return 0


def cmd_registry(a) -> int:
    for ag in registry.agents():
        if a.purpose and ag.purpose != a.purpose:
            continue
        flag = " (deprecated)" if ag.deprecated else ""
        print(f"{ag.token:30} {ag.purpose:11} {ag.operator:22} {ag.status:10}{flag}")
    return 0


def cmd_markets(a) -> int:
    for code, j in registry.jurisdictions().items():
        print(f"{code:3} {j['name']:28} {j['regime']:20} {j.get('status')}")
    print(registry.legal_disclaimer())
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="novarys", description="NOVARYS OMNISEARCH - AI visibility & content-rights compliance engine")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("audit", help="audit a site's AI-usage signals")
    s.add_argument("--robots"); s.add_argument("--status", type=int, default=200)
    s.add_argument("--headers", help="JSON file of response headers"); s.add_argument("--html"); s.add_argument("--tdmrep"); s.add_argument("--tos")
    s.add_argument("--jurisdiction", default="EU,US,UK,JP"); s.add_argument("--training", choices=["deny", "allow"])
    s.add_argument("--json", action="store_true"); s.add_argument("--strict", action="store_true", help="exit 1 on high/critical findings")
    s.set_defaults(fn=cmd_audit)

    s = sub.add_parser("compile", help="compile a policy into all machine-readable formats")
    s.add_argument("policy"); s.add_argument("-o", "--out", default="novarys-out"); s.set_defaults(fn=cmd_compile)

    s = sub.add_parser("verify", help="check that a robots.txt implements a policy")
    s.add_argument("policy"); s.add_argument("robots"); s.set_defaults(fn=cmd_verify)

    s = sub.add_parser("logs", help="analyse access logs for AI agents, compliance and referrals")
    s.add_argument("log"); s.add_argument("--robots"); s.add_argument("--ledger"); s.add_argument("--url", default="/robots.txt")
    s.add_argument("--ranges", action="append", help="TOKEN=ip-ranges.json (repeatable)"); s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_logs)

    s = sub.add_parser("evidence", help="tamper-evident ledger of published signals")
    s.add_argument("action", choices=["add", "verify", "tsq", "list"]); s.add_argument("dir")
    s.add_argument("--url"); s.add_argument("--file"); s.add_argument("--kind", default="snapshot"); s.add_argument("-o", "--out", default="head.tsq")
    s.set_defaults(fn=cmd_evidence)

    s = sub.add_parser("tlog", help="public append-only transparency log (RFC 9162)")
    s.add_argument("action", choices=["append", "head", "prove", "consistency", "tsq"]); s.add_argument("dir")
    s.add_argument("--record", help="JSON record to append"); s.add_argument("--index", type=int, default=0, help="leaf index (prove) or old size (consistency)")
    s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_tlog)

    s = sub.add_parser("check", help="verify an inclusion or consistency proof file offline"); s.add_argument("proof"); s.set_defaults(fn=cmd_check)

    s = sub.add_parser("snapshot", help="record a published signal file in the evidence ledger (+ public commitment)")
    s.add_argument("ledger"); s.add_argument("--url", required=True); s.add_argument("--file", required=True)
    s.add_argument("--kind", default="robots.txt"); s.add_argument("--tlog"); s.set_defaults(fn=cmd_snapshot)

    s = sub.add_parser("constat", help="neutral, deterministic technical report at a date")
    s.add_argument("ledger"); s.add_argument("--url", required=True); s.add_argument("--as-of", required=True)
    s.add_argument("--jurisdiction", default=""); s.add_argument("--logs-json"); s.add_argument("--tlog")
    s.add_argument("--requested-by"); s.add_argument("-o", "--out"); s.add_argument("--md"); s.set_defaults(fn=cmd_constat)

    s = sub.add_parser("constat-verify", help="check a constat's hash"); s.add_argument("report"); s.set_defaults(fn=cmd_constat_verify)

    s = sub.add_parser("meter", help="neutral usage metering (per publisher, committed, k-anonymous aggregate)")
    s.add_argument("action", choices=["report", "commit", "aggregate"]); s.add_argument("inputs", nargs="+")
    s.add_argument("--publisher"); s.add_argument("--period"); s.add_argument("--tlog"); s.add_argument("--k", type=int, default=metering.K_MIN)
    s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_meter)

    s = sub.add_parser("canary", help="pre-registered canaries with an exact paired test")
    s.add_argument("action", choices=["create", "verify", "test"]); s.add_argument("secret"); s.add_argument("inputs", nargs="*")
    s.add_argument("-n", type=int, default=200); s.add_argument("--tlog"); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_canary)

    s = sub.add_parser("registry", help="list known AI/search agents"); s.add_argument("--purpose"); s.set_defaults(fn=cmd_registry)
    s = sub.add_parser("markets", help="list the legal knowledge base"); s.set_defaults(fn=cmd_markets)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
