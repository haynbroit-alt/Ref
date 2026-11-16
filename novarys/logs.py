"""Server-log analysis: which AI agents came, were they genuine, did they obey, what came back.

Works offline on standard access logs (combined format). Crawler identity is
verified against the vendors' published IP-range files that the user
downloads (JSON with ipv4Prefix/ipv6Prefix entries or any list of CIDRs).
Only bot and referral statistics are produced: client IPs of humans are
never stored in the output (data minimisation).
"""
from __future__ import annotations

import ipaddress
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Iterable
from urllib.parse import urlsplit

from . import registry, robots

LOG_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>[A-Z]+) (?P<path>\S+)(?: [^"]*)?" (?P<status>\d{3}) \S+'
    r'(?: "(?P<referer>[^"]*)" "(?P<ua>[^"]*)")?'
)


@dataclass
class Hit:
    ip: str
    time: datetime
    method: str
    path: str
    status: int
    referer: str
    ua: str


def parse_line(line: str) -> Hit | None:
    m = LOG_RE.match(line.strip())
    if not m:
        return None
    try:
        t = datetime.strptime(m.group("time"), "%d/%b/%Y:%H:%M:%S %z")
    except ValueError:
        return None
    return Hit(m.group("ip"), t, m.group("method"), m.group("path"), int(m.group("status")),
               m.group("referer") or "", m.group("ua") or "")


_TOKENS = sorted((a for a in registry.agents() if a.crawls), key=lambda a: -len(a.token))


def identify(ua: str) -> registry.Agent | None:
    """Registry agent whose token appears in the User-Agent string (longest token wins)."""
    low = ua.lower()
    for a in _TOKENS:
        for m in re.finditer(re.escape(a.key), low):
            i, j = m.start(), m.end()
            before = low[i - 1] if i > 0 else " "
            after = low[j] if j < len(low) else " "
            if not (before.isalnum() or before == "-") and not (after.isalnum() or after == "-"):
                return a
    return None


def load_ranges(path: str) -> list[ipaddress._BaseNetwork]:
    """Accept Google/OpenAI-style {"prefixes":[{"ipv4Prefix":..}]} or any JSON/text containing CIDRs."""
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    nets = []
    try:
        data = json.loads(raw)
        stack = [data]
        while stack:
            x = stack.pop()
            if isinstance(x, dict):
                stack.extend(x.values())
            elif isinstance(x, list):
                stack.extend(x)
            elif isinstance(x, str):
                try:
                    nets.append(ipaddress.ip_network(x, strict=False))
                except ValueError:
                    pass
    except ValueError:
        for tok in re.findall(r"[0-9a-fA-F:.]+/\d+", raw):
            try:
                nets.append(ipaddress.ip_network(tok, strict=False))
            except ValueError:
                pass
    return nets


@dataclass
class AgentStats:
    token: str
    operator: str
    purpose: str
    requests: int = 0
    verified: int = 0
    spoofed: int = 0
    unverifiable: int = 0
    disallowed_fetches: int = 0
    disallowed_fetches_verified: int = 0
    sample_violations: list[str] = field(default_factory=list)


@dataclass
class LogReport:
    lines: int
    parsed: int
    agents: dict[str, AgentStats]
    referrals: dict[str, int]
    crawl_to_referral: dict[str, float | None]
    robots_versions_used: int
    notes: list[str]

    def to_dict(self) -> dict:
        return {
            "lines": self.lines, "parsed": self.parsed,
            "agents": {k: v.__dict__ for k, v in sorted(self.agents.items(), key=lambda kv: -kv[1].requests)},
            "referrals": self.referrals, "crawl_to_referral": self.crawl_to_referral,
            "robots_versions_used": self.robots_versions_used, "notes": self.notes,
        }


def analyse(lines: Iterable[str], robots_for: Callable[[datetime], robots.RobotsTxt | None],
            ranges: dict[str, list] | None = None, max_samples: int = 5) -> LogReport:
    """*robots_for(time)* returns the robots.txt in force at that time (e.g. from the evidence ledger)."""
    ranges = {k.lower(): v for k, v in (ranges or {}).items()}
    referrers = registry.ai_referrers()
    stats: dict[str, AgentStats] = {}
    refs: Counter = Counter()
    n = parsed = 0
    versions = set()
    for line in lines:
        n += 1
        h = parse_line(line)
        if h is None:
            continue
        parsed += 1
        if h.referer:
            host = (urlsplit(h.referer).hostname or "").lower()
            if host in referrers:
                refs[referrers[host]] += 1
        a = identify(h.ua)
        if a is None:
            continue
        s = stats.setdefault(a.token, AgentStats(a.token, a.operator, a.purpose))
        s.requests += 1
        nets = ranges.get(a.key)
        state = "unverifiable"
        if nets:
            try:
                ip = ipaddress.ip_address(h.ip)
                state = "verified" if any(ip in net for net in nets) else "spoofed"
            except ValueError:
                state = "spoofed"
        setattr(s, state, getattr(s, state) + 1)
        rb = robots_for(h.time)
        if rb is not None:
            versions.add(id(rb))
            if h.path != "/robots.txt" and not rb.can_fetch(a.token, h.path) and state != "spoofed":
                s.disallowed_fetches += 1
                if state == "verified":
                    s.disallowed_fetches_verified += 1
                if len(s.sample_violations) < max_samples:
                    s.sample_violations.append(f"{h.time.isoformat()} {h.method} {h.path} ({state})")
    by_op_crawl: Counter = Counter()
    for s in stats.values():
        if s.purpose in ("training", "ai_answers", "mixed"):
            by_op_crawl[s.operator] += s.requests - s.spoofed
    ctr = {}
    for op in set(by_op_crawl) | set(refs):
        ctr[op] = round(by_op_crawl[op] / refs[op], 1) if refs[op] else None
    notes = ["Spoofed requests (claimed AI user agent from an IP outside the vendor's published ranges) are excluded from violation counts.",
             "User-triggered fetchers (ChatGPT-User, Perplexity-User, ...) are documented by some vendors as not bound by robots.txt."]
    return LogReport(n, parsed, stats, dict(refs), ctr, len(versions), notes)
