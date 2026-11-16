"""RFC 9309 (Robots Exclusion Protocol) parser and evaluator.

Pure standard library. Semantics follow RFC 9309 (2022):

* groups start with one or more ``user-agent`` lines; a ``user-agent`` line
  that follows a rule starts a new group; blank lines do NOT end a group
  (same behaviour as Google's reference parser);
* a crawler obeys the group(s) whose user-agent value matches its product
  token (case-insensitive); several matching groups are merged; only if none
  matches does it fall back to ``*``;
* within the selected rules the longest matching pattern wins and ``allow``
  wins a tie; ``*`` matches any sequence, ``$`` anchors the end;
* ``/robots.txt`` itself is always allowed.

Besides evaluation, :func:`escaped_wildcard_rules` reports the classic
"group-selection trap": rules of the ``*`` group that a named crawler no
longer has to follow because it has its own group.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable
from urllib.parse import quote

MAX_BYTES = 500 * 1024  # RFC 9309 §2.5: parse at least 500 KiB

_TOKEN_RE = re.compile(r"[A-Za-z_-]+")
_KEY_ALIASES = {
    "user-agent": "user-agent",
    "useragent": "user-agent",
    "user agent": "user-agent",
    "allow": "allow",
    "disallow": "disallow",
    "dissallow": "disallow",
    "dissalow": "disallow",
    "disalow": "disallow",
    "diasllow": "disallow",
    "disallaw": "disallow",
    "sitemap": "sitemap",
    "site-map": "sitemap",
}


@dataclass
class Rule:
    allow: bool
    pattern: str  # normalised pattern
    line: int
    raw: str

    @property
    def specificity(self) -> int:
        return len(self.pattern.encode("utf-8"))


@dataclass
class Group:
    agents: list[str]  # raw user-agent values as written
    rules: list[Rule] = field(default_factory=list)
    line: int = 0

    @property
    def tokens(self) -> list[str]:
        return [_ua_token(a) for a in self.agents]


@dataclass
class Lint:
    level: str  # "error" | "warning" | "info"
    code: str
    line: int
    message: str


@dataclass
class RobotsTxt:
    groups: list[Group]
    sitemaps: list[str]
    lints: list[Lint]
    other_records: list[tuple[int, str, str]]  # (line, key, value) e.g. Content-Signal, Content-Usage
    truncated: bool = False

    # ------------------------------------------------------------------
    def groups_for(self, token: str) -> list[Group]:
        """Groups that apply to *token* per RFC 9309 §2.2.1 (exact, merged)."""
        t = token.lower()
        named = [g for g in self.groups if t in g.tokens]
        if named:
            return named
        return [g for g in self.groups if "*" in g.tokens]

    def has_named_group(self, token: str) -> bool:
        t = token.lower()
        return any(t in g.tokens for g in self.groups)

    def rules_for(self, token: str) -> list[Rule]:
        rules: list[Rule] = []
        for g in self.groups_for(token):
            rules.extend(g.rules)
        return rules

    def decide(self, token: str, path: str) -> tuple[bool, Rule | None]:
        """Return (allowed, deciding_rule) for *token* fetching *path*."""
        return decide(self.rules_for(token), path)

    def can_fetch(self, token: str, path: str) -> bool:
        return self.decide(token, path)[0]

    def fully_blocked(self, token: str) -> bool:
        """True when the crawler may not fetch the site root."""
        return not self.can_fetch(token, "/")

    def records(self, key: str) -> list[str]:
        k = key.lower()
        return [v for (_, kk, v) in self.other_records if kk == k]


def _ua_token(value: str) -> str:
    value = value.strip()
    if value == "*":
        return "*"
    m = _TOKEN_RE.match(value)
    return m.group(0).lower() if m else value.lower()


_HEX = "0123456789ABCDEF"


def _normalise(pattern: str) -> str:
    """Escape a pattern like Google's reference parser (RFC 9309 §2.2.2).

    Non-ASCII characters become %XX (UTF-8, upper-case hex) and existing
    %xx escapes are upper-cased; nothing is decoded. Paths to be checked are
    expected to be already percent-encoded, as they appear in HTTP requests
    and server logs (see :func:`encode_path` for raw user input).
    """
    out = []
    b = pattern.encode("utf-8")
    i = 0
    while i < len(b):
        c = b[i]
        if c == 0x25 and i + 2 < len(b) and chr(b[i + 1]) in "0123456789abcdefABCDEF" and chr(b[i + 2]) in "0123456789abcdefABCDEF":
            out.append("%" + chr(b[i + 1]).upper() + chr(b[i + 2]).upper())
            i += 3
            continue
        if c >= 0x80:
            out.append("%" + _HEX[c >> 4] + _HEX[c & 15])
        else:
            out.append(chr(c))
        i += 1
    return "".join(out)


def encode_path(path: str) -> str:
    """Percent-encode a raw, human-typed path (e.g. '/café') like a browser would."""
    return quote(path, safe="/?&=;:@!$'()*+,-._~%#[]")


def parse(text: str | bytes) -> RobotsTxt:
    if isinstance(text, bytes):
        truncated = len(text) > MAX_BYTES
        text = text[:MAX_BYTES].decode("utf-8", errors="replace")
    else:
        raw = text.encode("utf-8")
        truncated = len(raw) > MAX_BYTES
        if truncated:
            text = raw[:MAX_BYTES].decode("utf-8", errors="ignore")
    if text.startswith("﻿"):
        text = text[1:]

    groups: list[Group] = []
    sitemaps: list[str] = []
    lints: list[Lint] = []
    others: list[tuple[int, str, str]] = []
    current: Group | None = None
    last_was_agent = False
    saw_blank_inside_group = False
    interrupted = ""  # what interrupted a run of user-agent lines (blank line / record)

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            if current is not None and current.rules:
                saw_blank_inside_group = True
            if last_was_agent and not interrupted:
                interrupted = "blank line"
            continue
        if ":" not in line:
            # Google accepts a missing colon for known keys ("disallow /")
            m = re.match(r"(?i)(user-agent|allow|disallow|sitemap)\s+(\S.*)$", line)
            if not m:
                lints.append(Lint("warning", "no-colon", lineno, f"line ignored (no ':'): {raw_line.strip()[:80]}"))
                continue
            lints.append(Lint("warning", "missing-colon", lineno, "key without ':' - accepted by Google, ignored by stricter parsers"))
            line = m.group(1) + ":" + m.group(2)
        key, value = line.split(":", 1)
        key_l = key.strip().lower()
        value = value.strip()
        norm_key = _KEY_ALIASES.get(key_l)
        if norm_key and norm_key != key_l and key_l not in ("useragent", "user agent"):
            lints.append(Lint("warning", "misspelled-key", lineno, f"'{key.strip()}' is not a standard key; some parsers will ignore it"))
        if norm_key == "user-agent":
            if current is None or not last_was_agent:
                current = Group(agents=[], line=lineno)
                groups.append(current)
                saw_blank_inside_group = False
            elif interrupted:
                lints.append(Lint("warning", "ambiguous-group-boundary", lineno,
                    f"user-agent '{value}' follows agents {current.agents} after a {interrupted} with no allow/disallow in between: "
                    "RFC 9309/Google merge them into ONE group (sharing the next rules), legacy parsers treat them as separate groups"))
            interrupted = ""
            current.agents.append(value)
            last_was_agent = True
            if value != "*":
                m = _TOKEN_RE.match(value)
                if not m:
                    lints.append(Lint("warning", "odd-agent", lineno, f"user-agent value '{value}' has no valid product token"))
                elif m.group(0) != value:
                    lints.append(Lint("info", "agent-with-version", lineno, f"user-agent '{value}' is matched as '{_ua_token(value)}'"))
            continue
        if norm_key in ("allow", "disallow"):
            last_was_agent = False
            interrupted = ""
            if current is None:
                lints.append(Lint("error", "rule-before-agent", lineno, f"{norm_key} before any user-agent line is ignored by RFC 9309 parsers"))
                continue
            if saw_blank_inside_group:
                lints.append(Lint("info", "blank-line-in-group", lineno, "rule after a blank line: RFC 9309/Google keep it in the group, legacy parsers may not"))
                saw_blank_inside_group = False
            if value == "":
                # empty disallow = no restriction; empty allow = no-op
                continue
            if not value.startswith("/") and not value.startswith("*"):
                lints.append(Lint("warning", "pattern-no-slash", lineno, f"pattern '{value}' does not start with '/' or '*'"))
                value = "/" + value
            current.rules.append(Rule(allow=(norm_key == "allow"), pattern=_normalise(value), line=lineno, raw=raw_line.strip()))
            if norm_key == "allow" and (value.endswith("/index.html") or value.endswith("/index.htm")):
                # Google extension: allowing the index file also allows the directory URL
                directory = value.rsplit("/", 1)[0] + "/$"
                current.rules.append(Rule(allow=True, pattern=_normalise(directory), line=lineno, raw=raw_line.strip()))
            continue
        # sitemap and unknown records (crawl-delay, content-signal, ...) do not change group structure
        if last_was_agent and not interrupted:
            interrupted = f"'{key.strip()}' record"
        if norm_key == "sitemap":
            sitemaps.append(value)
            continue
        others.append((lineno, key_l, value))

    seen: dict[str, int] = {}
    for g in groups:
        for t in g.tokens:
            if t in seen and t != "*":
                lints.append(Lint("info", "duplicate-agent", g.line, f"'{t}' appears in several groups (lines {seen[t]} and {g.line}); RFC 9309 merges them"))
            seen.setdefault(t, g.line)
    if truncated:
        lints.append(Lint("warning", "truncated", 0, "file larger than 500 KiB: rules beyond the limit may be ignored"))
    return RobotsTxt(groups=groups, sitemaps=sitemaps, lints=lints, other_records=others, truncated=truncated)


# ----------------------------------------------------------------------
# matching

def _match(pattern: str, path: str) -> bool:
    """Wildcard match without regular expressions (no catastrophic backtracking)."""
    anchored = pattern.endswith("$")
    if anchored:
        pattern = pattern[:-1]
    parts = pattern.split("*")
    # first part must be a prefix
    if not path.startswith(parts[0]):
        return False
    pos = len(parts[0])
    if len(parts) == 1:
        return (pos == len(path)) if anchored else True
    for i, part in enumerate(parts[1:], start=1):
        last = i == len(parts) - 1
        if part == "":
            if last:
                return True  # trailing '*' matches the rest (also with '$')
            continue
        if last and anchored:
            return path.endswith(part) and len(path) - len(part) >= pos
        idx = path.find(part, pos)
        if idx < 0:
            return False
        pos = idx + len(part)
    return True if not anchored else pos == len(path)


def decide(rules: Iterable[Rule], path: str) -> tuple[bool, Rule | None]:
    if not path:
        path = "/"
    if path == "/robots.txt" or path.startswith("/robots.txt?"):
        return True, None
    npath = path  # as sent on the wire (already percent-encoded), like Google
    best: Rule | None = None
    for r in rules:
        if _match(r.pattern, npath):
            if best is None or r.specificity > best.specificity or (
                r.specificity == best.specificity and r.allow and not best.allow
            ):
                best = r
    if best is None:
        return True, None
    return best.allow, best


def sample_path(pattern: str) -> str:
    """A concrete path that *pattern* matches (used to test rule escapes)."""
    p = pattern[:-1] if pattern.endswith("$") else pattern
    return p.replace("*", "x") or "/"


@dataclass
class Escape:
    token: str
    rule: Rule
    sample: str
    deciding_rule: Rule | None


def escaped_wildcard_rules(robots: RobotsTxt, token: str) -> list[Escape]:
    """Disallow rules of the ``*`` group that *token* escapes because it has its own group."""
    if not robots.has_named_group(token):
        return []
    star_rules: list[Rule] = []
    for g in robots.groups:
        if "*" in g.tokens:
            star_rules.extend(g.rules)
    if not star_rules:
        return []
    # a default-deny file ("*" blocks "/") with named exceptions is deliberate
    star_allows_root, _ = decide(star_rules, "/")
    own_rules = robots.rules_for(token)
    out: list[Escape] = []
    for r in star_rules:
        if r.allow or r.pattern in ("/", "/*"):
            continue
        sp = sample_path(r.pattern)
        star_ok, _ = decide(star_rules, sp)
        own_ok, own_rule = decide(own_rules, sp)
        if not star_ok and own_ok:
            out.append(Escape(token=token, rule=r, sample=sp, deciding_rule=own_rule))
    if not star_allows_root:
        return []
    return out


def interpret_status(status: int) -> str:
    """RFC 9309 §2.3.1: how a crawler must treat the robots.txt HTTP status."""
    if 200 <= status < 300:
        return "parse"
    if status == 429 or 500 <= status < 600:
        return "disallow-all"  # server error: assume complete disallow
    if 400 <= status < 500:
        return "allow-all"  # unavailable: crawler may access everything
    if status == 0:
        return "disallow-all"  # unreachable
    return "parse"
