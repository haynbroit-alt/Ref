"""Compare how different real-world robots.txt parsers read the same file.

A reservation of rights is only robust if every crawler reads it the same
way. Two implementations are compared:

* ``rfc9309``  - :mod:`novarys.robots` (RFC 9309 / Google reference semantics:
  merged groups, longest match, blank lines ignored);
* ``legacy``   - Python's :mod:`urllib.robotparser` (pre-RFC behaviour still
  used by many crawlers: blank lines end a record, first matching rule wins,
  user-agent matched by substring).
"""
from __future__ import annotations

import urllib.robotparser
from dataclasses import dataclass

from . import robots as rfc


@dataclass
class Divergence:
    token: str
    path: str
    rfc9309: bool
    legacy: bool


def _legacy_parser(text: str) -> urllib.robotparser.RobotFileParser:
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(text.splitlines())
    return rp


def compare(text: str, tokens: list[str], paths: list[str] | None = None) -> list[Divergence]:
    parsed = rfc.parse(text)
    legacy = _legacy_parser(text)
    probe_paths = list(paths or [])
    if not probe_paths:
        probe_paths = ["/"]
        for g in parsed.groups:
            for r in g.rules:
                sp = rfc.sample_path(r.pattern)
                if sp not in probe_paths:
                    probe_paths.append(sp)
        probe_paths = probe_paths[:200]
    out: list[Divergence] = []
    for t in tokens:
        for p in probe_paths:
            a = parsed.can_fetch(t, p)
            try:
                b = legacy.can_fetch(t, "https://example.invalid" + p)
            except Exception:  # pragma: no cover - stdlib edge cases
                continue
            if a != b:
                out.append(Divergence(t, p, a, b))
    return out


def root_divergence(text: str, tokens: list[str]) -> dict[str, tuple[bool, bool]]:
    """For each token: (blocked_at_root_rfc9309, blocked_at_root_legacy) when they differ."""
    res: dict[str, tuple[bool, bool]] = {}
    for d in compare(text, tokens, ["/"]):
        res[d.token] = (not d.rfc9309, not d.legacy)
    return res
