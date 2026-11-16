"""Audit a site's AI-usage signals: effective access, contradictions, legal effect, visibility.

Input is what a site publishes (robots.txt, headers/HTML of a page, TDMRep file,
terms of service). Output is a structured report; nothing is fetched here.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from . import dialects, registry, robots, signals

SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

# Surfaces where content can be cited in AI answers, and the agent that decides eligibility.
VISIBILITY_SURFACES = [
    ("Google AI Overviews / AI Mode", "Googlebot", "snippet"),
    ("Google Search", "Googlebot", None),
    ("Gemini Apps grounding", "Google-Extended", None),
    ("ChatGPT search", "OAI-SearchBot", None),
    ("Claude answers (search)", "Claude-SearchBot", None),
    ("Perplexity", "PerplexityBot", None),
    ("Bing / Microsoft Copilot", "bingbot", None),
    ("Apple (Siri, Spotlight)", "Applebot", None),
    ("DuckDuckGo DuckAssist", "DuckAssistBot", None),
]


@dataclass
class Finding:
    severity: str
    code: str
    title: str
    detail: str
    fix: str = ""
    agents: list[str] = field(default_factory=list)


@dataclass
class Inputs:
    robots_txt: str | None = None
    robots_status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    html: str | None = None
    tdmrep_json: str | None = None
    tos_text: str | None = None
    jurisdictions: list[str] = field(default_factory=lambda: ["EU", "US", "UK", "JP"])
    intent_training: str | None = None   # "deny" | "allow" | None (infer)


@dataclass
class Report:
    registry_version: str
    robots_interpretation: str
    agents: list[dict]
    findings: list[Finding]
    reservation: dict
    jurisdictions: list[dict]
    visibility: list[dict]
    lints: list[dict]
    disclaimer: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["findings"] = sorted(d["findings"], key=lambda f: SEV_ORDER.get(f["severity"], 9))
        return d

    def counts(self) -> dict[str, int]:
        c: dict[str, int] = {}
        for f in self.findings:
            c[f.severity] = c.get(f.severity, 0) + 1
        return c


def _robots(inp: Inputs) -> tuple[robots.RobotsTxt, str]:
    mode = robots.interpret_status(inp.robots_status) if inp.robots_txt is not None or inp.robots_status != 200 else "allow-all"
    if inp.robots_txt is None and inp.robots_status == 200:
        mode = "allow-all"
    if mode == "parse":
        return robots.parse(inp.robots_txt or ""), "parse"
    if mode == "disallow-all":
        return robots.parse("User-agent: *\nDisallow: /\n"), "disallow-all"
    return robots.parse(""), "allow-all"


def audit(inp: Inputs) -> Report:
    rb, mode = _robots(inp)
    page = signals.parse_page(inp.headers, inp.html)
    tdm = signals.parse_tdmrep(inp.tdmrep_json) if inp.tdmrep_json else []
    findings: list[Finding] = []
    text = inp.robots_txt or ""

    # ---- per-agent effective access ------------------------------------
    tokens = [a.token for a in registry.agents()]
    divergent = dialects.root_divergence(text, tokens) if mode == "parse" else {}
    agent_rows = []
    blocked: dict[str, bool] = {}
    for a in registry.agents():
        b = rb.fully_blocked(a.token)
        blocked[a.key] = b
        esc = robots.escaped_wildcard_rules(rb, a.token) if not b else []
        agent_rows.append({
            "token": a.token, "operator": a.operator, "purpose": a.purpose, "registry_status": a.status,
            "named_in_robots": rb.has_named_group(a.token), "blocked_at_root": b,
            "legacy_parser_blocked_at_root": (divergent[a.token][1] if a.token in divergent else b),
            "escaped_wildcard_rules": len(esc), "deprecated": a.deprecated, "effect": a.effect,
        })

    # ---- training reservation --------------------------------------------
    core = [registry.agent(t) for t in registry.CORE_TRAINING]
    core = [c for c in core if c is not None]
    core_blocked = [c.token for c in core if blocked[c.key]]
    core_open = [c.token for c in core if not blocked[c.key]]
    usage_group = rb.has_named_group(registry.VENDOR_NEUTRAL_TRAINING_TOKEN) and rb.fully_blocked(registry.VENDOR_NEUTRAL_TRAINING_TOKEN)
    cs = {}
    for v in rb.records("content-signal"):
        cs.update(signals.parse_prefs(v))
    cu = dict(page.content_usage)
    for v in rb.records("content-usage"):
        cu.update(signals.parse_prefs(v))
    tdm_root = bool(page.tdm_reservation) or signals.tdmrep_reserves_root(tdm)
    tos = signals.tos_has_reservation(inp.tos_text)
    star_root = not rb.can_fetch("*-no-such-bot-*", "/")
    neutral = {
        "__usage_ai-training robots.txt group": usage_group,
        "TDMRep (tdm-reservation)": tdm_root,
        "AIPREF Content-Usage train-ai=n": signals.training_denied(cu) is True,
        "Cloudflare Content-Signal ai-train=no": signals.training_denied(cs) is True,
        "Terms-of-service reservation text": tos,
        "robots.txt blocks every unnamed bot (User-agent: *)": star_root,
    }
    any_signal = bool(core_blocked) or any(neutral.values())
    intent = inp.intent_training or ("deny" if any_signal else "unknown")

    if mode == "disallow-all":
        findings.append(Finding("critical", "ROBOTS_SERVER_ERROR", "robots.txt returns a server error",
            f"HTTP {inp.robots_status}: RFC 9309 tells crawlers to assume a complete disallow, so search engines stop crawling the whole site.",
            "Serve robots.txt with HTTP 200."))
    elif mode == "allow-all" and inp.robots_status != 200:
        findings.append(Finding("medium", "ROBOTS_UNAVAILABLE", "robots.txt unavailable",
            f"HTTP {inp.robots_status}: crawlers may fetch everything; no machine-readable reservation exists.",
            "Publish a robots.txt (HTTP 200)."))

    if intent == "deny":
        if core_open:
            sev = "high" if core_blocked else "medium"
            findings.append(Finding(sev, "TRAINING_PARTIAL", "Training opt-out leaves major AI-training crawlers allowed",
                f"{len(core_blocked)}/{len(core)} core training agents are blocked; still allowed: {', '.join(core_open)}.",
                "Add a 'Disallow: /' group for each listed agent (see `novarys compile`).", core_open))
        def open_replacements(a):
            # replacements serving the same purpose that are still allowed
            return [r for r in a.replaced_by
                    if registry.agent(r) and registry.agent(r).purpose == a.purpose and not blocked[registry.agent(r).key]]
        dep = [a for a in registry.agents() if a.deprecated and blocked[a.key] and open_replacements(a)]
        for a in dep:
            repl = open_replacements(a)
            findings.append(Finding("high", "OBSOLETE_TOKEN", f"Blocks legacy token '{a.token}' but not its replacement",
                f"'{a.token}' is no longer documented by {a.operator}; {', '.join(repl)} remain allowed.",
                f"Add 'User-agent: {repl[0]}' / 'Disallow: /'.", [a.token] + repl))
        if not any(v for k, v in neutral.items() if k != "robots.txt blocks every unnamed bot (User-agent: *)") and not star_root:
            findings.append(Finding("high", "NAMED_BOTS_ONLY", "Reservation relies only on named bots",
                "No vendor-neutral signal (TDMRep, __usage_ai-training, AIPREF, ToS clause). A robots.txt naming only some bots may not reserve rights against the others: in a Dutch case where the robots.txt named only some AI bots, the court found the scraper was not effectively excluded; commentators read it as requiring the opt-out to target the bots concerned (Rb Amsterdam, 30 Oct 2024, ECLI:NL:RBAMS:2024:6563; appeal reported pending).",
                "Publish /.well-known/tdmrep.json, a __usage_ai-training group and a reservation clause in the terms of service."))
        if not usage_group:
            findings.append(Finding("medium", "NO_USAGE_TOKEN", "No vendor-neutral __usage_ai-training group",
                "Reported to be honoured by Microsoft from 1 Feb 2027 and planned by Google for 2027 (draft-kelley-aipref-training-preference-signal).",
                "Add 'User-agent: __usage_ai-training' / 'Disallow: /'."))
        if any(j.upper() in ("EU", "DE", "FR", "IT", "ES", "NL", "PL", "BE", "SE", "VN") for j in inp.jurisdictions) and not tdm_root:
            findings.append(Finding("medium", "NO_TDMREP", "No TDMRep reservation",
                "W3C TDMRep is the machine-readable protocol designed for DSM Art. 4(3) reservations; it is on the Commission's consultation list of opt-out protocols.",
                "Publish /.well-known/tdmrep.json and the 'tdm-reservation: 1' header."))
        if cs and signals.training_denied(cs) is True and not core_blocked and not usage_group:
            findings.append(Finding("medium", "SIGNAL_NOT_HONOURED", "Content-Signal is the only training opt-out",
                "No major AI vendor has stated that it honours Content-Signal; Google said the syntax is ignored.",
                "Back it with per-agent groups and a __usage_ai-training group."))

    # ---- interpretation robustness ---------------------------------------
    div_core = {t: v for t, v in divergent.items()}
    if div_core:
        findings.append(Finding("high", "PARSER_DIVERGENCE", "Crawlers using different parsers read this file differently",
            "; ".join(f"{t}: blocked per RFC 9309/Google={v[0]}, per legacy parser={v[1]}" for t, v in sorted(div_core.items())),
            "Rewrite with `novarys compile` (canonical groups, no ambiguous boundaries).", sorted(div_core)))
    amb = [l for l in rb.lints if l.code == "ambiguous-group-boundary"]
    if amb:
        findings.append(Finding("medium", "AMBIGUOUS_GROUPS", "Ambiguous group boundaries",
            f"{len(amb)} user-agent line(s) follow a blank line or a non-standard record without rules in between (first at line {amb[0].line}); RFC 9309/Google merge them with the next group.",
            "Give every user-agent its own explicit rules."))
    esc_agents = [r["token"] for r in agent_rows if r["escaped_wildcard_rules"]]
    if esc_agents:
        n = max(r["escaped_wildcard_rules"] for r in agent_rows)
        findings.append(Finding("medium", "WILDCARD_ESCAPE", "Named groups cancel the site-wide rules",
            f"{', '.join(esc_agents)} have their own group, so they no longer follow up to {n} 'User-agent: *' rule(s) (RFC 9309 §2.2.1: groups are not combined).",
            "Repeat the wildcard rules inside each named group.", esc_agents))

    # ---- trade-offs / misconceptions ------------------------------------------
    if blocked["google-extended"] and not blocked["googlebot"] and not (page.nosnippet or (page.max_snippet is not None and page.max_snippet >= 0)):
        findings.append(Finding("info", "GOOGLE_EXTENDED_SCOPE", "Google-Extended does not keep content out of AI Overviews",
            "Google-Extended controls Gemini training/grounding only; AI Overviews and AI Mode follow Googlebot and snippet controls.",
            "Use nosnippet / data-nosnippet / max-snippet on pages to limit AI Overviews, or the Search Console generative-AI control (reported)."))
    for tok in ("Googlebot", "bingbot"):
        if blocked[tok.lower()] and not star_root:
            findings.append(Finding("high", "SEARCH_BLOCKED", f"{tok} is blocked",
                f"{registry.agent(tok).effect}", "Allow it unless removal from search is intended.", [tok]))
    ans_blocked = [a.token for a in registry.by_purpose("ai_answers") if blocked[a.key]]
    if ans_blocked:
        findings.append(Finding("info", "AI_ANSWERS_BLOCKED", "Excluded from some AI answer engines",
            f"Blocked: {', '.join(ans_blocked)}. The site will not be cited by these engines' search features.", "", ans_blocked))
    uf_blocked = [a.token for a in registry.by_purpose("user_fetch") if blocked[a.key] and a.obeys_robots in ("no", "partial", None)]
    if uf_blocked:
        findings.append(Finding("low", "USER_FETCH_NOT_ENFORCED", "Blocks of user-triggered fetchers may be ignored",
            f"{', '.join(uf_blocked)}: vendors state robots.txt may not apply to user-triggered fetches; enforce at the server/CDN if needed.", "", uf_blocked))
    for l in rb.lints:
        if l.code in ("rule-before-agent", "misspelled-key", "truncated", "missing-colon"):
            findings.append(Finding("medium" if l.level != "error" else "high", "LINT_" + l.code.upper().replace("-", "_"), l.message, f"line {l.line}"))

    # ---- reservation robustness score (transparent) -----------------------
    score = None
    parts = {}
    if intent == "deny":
        parts["coverage"] = round(40 * len(core_blocked) / len(core))
        parts["vendor_neutral"] = 20 if any(v for k, v in neutral.items()) else 0
        parts["unambiguous"] = 20 - (10 if div_core else 0) - (10 if amb else 0)
        parts["current_tokens"] = 10 if not any(f.code == "OBSOLETE_TOKEN" for f in findings) else 0
        parts["legal_notice"] = 10 if tos else 0
        score = sum(parts.values())
    reservation = {
        "intent": intent, "core_training_blocked": core_blocked, "core_training_allowed": core_open,
        "vendor_neutral_signals": neutral, "score": score, "score_parts": parts,
        "score_formula": "coverage 40 + vendor-neutral signal 20 + unambiguous 20 + current tokens 10 + legal notice 10",
    }

    # ---- legal effect per jurisdiction --------------------------------------
    jur_rows = []
    for code in inp.jurisdictions:
        j = registry.jurisdiction(code)
        if not j:
            jur_rows.append({"code": code, "assessment": "unknown market code"})
            continue
        jur_rows.append(_legal_effect(code, j, intent, core_open, neutral, tdm_root, tos, page))

    # ---- visibility eligibility ---------------------------------------------
    vis = []
    for surface, tok, kind in VISIBILITY_SURFACES:
        b = blocked[tok.lower()]
        state = "blocked" if b else "eligible"
        note = registry.agent(tok).effect
        if kind == "snippet" and not b:
            if page.noindex:
                state, note = "blocked", "noindex on the audited page"
            elif page.nosnippet:
                state, note = "blocked", "nosnippet prevents use as direct input for AI Overviews/AI Mode"
            elif page.max_snippet is not None and page.max_snippet >= 0:
                state, note = "limited", f"max-snippet:{page.max_snippet} limits direct input"
        vis.append({"surface": surface, "decided_by": tok, "state": state, "note": note,
                    "registry_status": registry.agent(tok).status})

    return Report(
        registry_version=registry.registry_version(), robots_interpretation=mode, agents=agent_rows,
        findings=findings, reservation=reservation, jurisdictions=jur_rows, visibility=vis,
        lints=[asdict(l) for l in rb.lints], disclaimer=registry.legal_disclaimer(),
    )


def _legal_effect(code, j, intent, core_open, neutral, tdm_root, tos, page) -> dict:
    regime = j.get("regime")
    any_neutral = any(neutral.values())
    if regime == "eu-optout":
        if intent != "deny":
            eff, why = "none", "No reservation expressed: commercial TDM is permitted (opt-out regime)."
        elif not core_open and any_neutral:
            eff, why = "strong", "Machine-readable reservation covering the core training agents plus a vendor-neutral signal."
        elif any_neutral:
            eff, why = "partial", "Vendor-neutral signal present, but some training agents are not named in robots.txt (the only protocol the GPAI Code makes mandatory)."
        else:
            eff, why = "weak", "Only named bots are blocked; " + (j.get("named_bot_risk") or "a named-bot list may not be a general reservation.")
    elif regime == "no-optout-exception":
        eff = "limited"
        why = "No opt-out exists; a reservation is not legally decisive. " + (j.get("named_bot_risk") or "Lawful-access conditions and technical measures matter more.")
    elif regime == "fair-use":
        eff, why = "limited", "No statutory opt-out; robots.txt and terms are evidence for contract claims and fair-use factors (market harm, access conditions)."
    elif regime == "no-exception":
        eff, why = "notice", "No commercial TDM exception: training on protected works needs a licence regardless; signals serve as notice and evidence."
    elif regime == "pending":
        eff, why = "uncertain", "Legislation pending."
    else:
        eff, why = "unknown", "Market not researched: obtain local legal advice."
    return {"code": code, "market": j.get("name"), "regime": regime, "effect": eff, "explanation": why,
            "law": j.get("law"), "search_rules": j.get("search"), "labelling": j.get("labelling"),
            "sources": j.get("sources", []), "status": j.get("status")}
