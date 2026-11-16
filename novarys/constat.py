"""Neutral technical report ("constat technique") on a site's AI-usage signals at a date.

Design rules that make the report usable by either side and by a decider
(arbitral tribunal, mediator, regulator, court):

1. Deterministic: the body depends only on its inputs (no wall-clock time, sorted
   keys); its SHA-256 is printed, and `verify` recomputes it from the body.
2. Requester-independent: who asked for the report is kept outside the hashed
   body, so a publisher and an AI provider asking the same question get the
   same report hash.
3. Facts, not conclusions: it states what was published, how RFC 9309 and a
   legacy parser read it, and what the logs show. It lists the applicable
   provisions with sources but draws no legal conclusion (no personalised
   legal advice; see docs/ARBITRE.md).
4. Its own limits are part of the report.
5. Rule-based only (no machine learning), which keeps the tool outside the
   AI Act definition of an "AI system" (Art. 3(1), Recital 12) and therefore
   outside Annex III point 8(a) when used in alternative dispute resolution.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from . import __version__, dialects, evidence, registry, robots, transparency

FORBIDDEN_WORDS = ("infringement", "infringe", "illegal", "unlawful", "violation", "violated", "guilty", "liable",
                   "contrefaçon", "illicite", "coupable")

LIMITS = [
    "Establishes what the site published and how parsers read it at the stated date; it does not establish that any AI model was trained on, or answered with, the site's content.",
    "Crawler identity is reported as verified only against the IP-range files supplied as input; unverifiable requests are reported separately.",
    "Robots.txt expresses a preference; legal effect depends on the jurisdiction and on facts outside this report.",
    "Contains no legal advice; applicable provisions are listed for reference only.",
]


def _canon(d: dict) -> bytes:
    return json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build(ledger_dir: str, url: str, as_of: str, jurisdictions: list[str] | None = None,
          logs_report: dict | None = None, log_dir: str | None = None, requested_by: str | None = None) -> dict:
    led = evidence.Ledger(ledger_dir)
    chain_problems = led.verify()
    entry = led.state_at(url, as_of)
    body: dict = {
        "type": "novarys-constat", "method_version": __version__, "registry_version": registry.registry_version(),
        "subject": {"url": url, "as_of": as_of},
        "ledger": {"entries": len(led.entries()), "chain_intact": not chain_problems, "problems": chain_problems,
                   "head": led.head()},
        "limits": LIMITS,
    }
    if entry is None:
        body["observation"] = {"found": False, "statement": f"No snapshot of {url} recorded at or before {as_of}."}
    else:
        text = led.content(entry).decode("utf-8", "replace")
        rb = robots.parse(text)
        tokens = [a.token for a in registry.agents()]
        div = dialects.root_divergence(text, tokens)
        agents = []
        for a in registry.agents():
            b = rb.fully_blocked(a.token)
            agents.append({"token": a.token, "operator": a.operator, "purpose": a.purpose,
                           "named_in_file": rb.has_named_group(a.token), "blocked_at_root_rfc9309": b,
                           "blocked_at_root_legacy_parser": div[a.token][1] if a.token in div else b,
                           "registry_status": a.status})
        body["observation"] = {
            "found": True, "snapshot_recorded_at": entry.ts, "ledger_seq": entry.seq, "ledger_entry_hash": entry.hash,
            "content_sha256": entry.sha256, "content_bytes": entry.size,
            "records": {"content-signal": rb.records("content-signal"), "content-usage": rb.records("content-usage"),
                        "license": rb.records("license")},
            "vendor_neutral_training_group": rb.has_named_group(registry.VENDOR_NEUTRAL_TRAINING_TOKEN)
            and rb.fully_blocked(registry.VENDOR_NEUTRAL_TRAINING_TOKEN),
            "agents": agents,
            "parser_divergences": sorted(div),
            "syntax_notes": sorted({f"{l.code}@{l.line}" for l in rb.lints if l.level != "info"}),
        }
        if log_dir:
            tl = transparency.Log(log_dir)
            idx = tl.find(lambda r: r.get("content_sha256") == entry.sha256 and r.get("url") == url)
            if idx:
                p = tl.prove(idx[0])
                body["observation"]["public_commitment"] = {"inclusion_proof": p, "verified": transparency.check_inclusion(p)}
    if logs_report:
        body["crawler_activity"] = {k: logs_report[k] for k in ("lines", "parsed", "agents", "referrals", "crawl_to_referral") if k in logs_report}
    if jurisdictions:
        rows = []
        for code in jurisdictions:
            j = registry.jurisdiction(code)
            if j:
                rows.append({"code": code.upper(), "market": j.get("name"), "regime": j.get("regime"),
                             "provisions": j.get("law"), "sources": j.get("sources", []), "status": j.get("status")})
        body["applicable_framework_for_reference"] = rows
    digest = hashlib.sha256(_canon(body)).hexdigest()
    return {"body": body, "report_sha256": digest,
            "envelope": {"requested_by": requested_by, "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                         "note": "The envelope is not part of the hashed body."}}


def verify(report: dict) -> bool:
    return hashlib.sha256(_canon(report["body"])).hexdigest() == report.get("report_sha256")


def neutral_wording(report: dict) -> list[str]:
    """Words that would turn a factual report into a legal conclusion (must be empty)."""
    body = {k: v for k, v in report["body"].items() if k != "applicable_framework_for_reference"}  # quoted law may use these words
    text = json.dumps(body, ensure_ascii=False).lower()
    return [w for w in FORBIDDEN_WORDS if w in text]


def to_markdown(report: dict) -> str:
    b = report["body"]
    lines = [f"# Constat technique NOVARYS — {b['subject']['url']}", "",
             f"- Date de référence : {b['subject']['as_of']}",
             f"- Empreinte du constat (SHA-256) : `{report['report_sha256']}`",
             f"- Méthode {b['method_version']}, registre {b['registry_version']}",
             f"- Registre de preuves : {b['ledger']['entries']} entrées, chaîne intègre : {b['ledger']['chain_intact']}", ""]
    o = b["observation"]
    if not o["found"]:
        lines.append(o["statement"])
    else:
        lines += ["## Observation", f"- Instantané enregistré le {o['snapshot_recorded_at']} (entrée #{o['ledger_seq']}),"
                  f" contenu SHA-256 `{o['content_sha256']}` ({o['content_bytes']} octets)"]
        if "public_commitment" in o:
            pc = o["public_commitment"]
            lines.append(f"- Engagement public : inclus dans le journal de taille {pc['inclusion_proof']['tree_size']},"
                         f" racine `{pc['inclusion_proof']['root_sha256']}`, preuve vérifiée : {pc['verified']}")
        lines += ["", "| Agent | Opérateur | Finalité | Bloqué (RFC 9309) | Bloqué (parseur ancien) |", "|---|---|---|---|---|"]
        for a in o["agents"]:
            if a["named_in_file"] or a["blocked_at_root_rfc9309"] or a["blocked_at_root_legacy_parser"] != a["blocked_at_root_rfc9309"]:
                lines.append(f"| {a['token']} | {a['operator']} | {a['purpose']} | {'oui' if a['blocked_at_root_rfc9309'] else 'non'} | {'oui' if a['blocked_at_root_legacy_parser'] else 'non'} |")
        lines.append(f"\nGroupe neutre `__usage_ai-training` : {'présent' if o['vendor_neutral_training_group'] else 'absent'}")
        if o["parser_divergences"]:
            lines.append(f"Divergences d'interprétation entre parseurs : {', '.join(o['parser_divergences'])}")
    if "crawler_activity" in b:
        lines += ["", "## Activité des robots (journaux fournis)"]
        for tok, s in b["crawler_activity"].get("agents", {}).items():
            lines.append(f"- {tok} : {s['requests']} requêtes, {s['verified']} vérifiées, {s['spoofed']} usurpées, "
                         f"{s['disallowed_fetches']} accès à des chemins exclus à la date de la requête, "
                         f"{s.get('not_assessable', 0)} non évaluables (aucun instantané en vigueur)")
    if "applicable_framework_for_reference" in b:
        lines += ["", "## Dispositions applicables (pour référence, sans conclusion juridique)"]
        for j in b["applicable_framework_for_reference"]:
            lines.append(f"- {j['code']} ({j['market']}) : {j['provisions'] or 'non étudié'} [{j['status']}]")
    lines += ["", "## Limites"] + [f"- {l}" for l in b["limits"]]
    return "\n".join(lines) + "\n"
