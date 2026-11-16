"""Parsers for the non-robots.txt AI-usage signals a site can publish."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

TRAIN_KEYS = {"ai-train", "train-ai", "train-genai", "ai-training", "genai-train"}
INPUT_KEYS = {"ai-input", "ai-use", "ai-grounding", "grounding"}
SEARCH_KEYS = {"search", "ai-index"}
NO = {"no", "n", "false", "0", "disallow", "deny"}
YES = {"yes", "y", "true", "1", "allow"}


def parse_prefs(value: str) -> dict[str, bool]:
    """Parse 'search=yes, ai-train=no' (Content-Signal) or 'train-ai=n' (AIPREF Content-Usage)."""
    out: dict[str, bool] = {}
    for part in re.split(r"[,;]\s*|\s+", value.strip()):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        k, v = k.strip().lower(), v.strip().strip('"').lower()
        if v in NO:
            out[k] = False
        elif v in YES:
            out[k] = True
    return out


def training_denied(prefs: dict[str, bool]) -> bool | None:
    for k in TRAIN_KEYS:
        if k in prefs:
            return not prefs[k]
    return None


@dataclass
class PageSignals:
    robots_meta: list[str] = field(default_factory=list)   # values of <meta name=robots|googlebot>
    x_robots: list[str] = field(default_factory=list)      # X-Robots-Tag header values
    tdm_reservation: bool | None = None
    tdm_policy: str | None = None
    content_usage: dict[str, bool] = field(default_factory=dict)
    data_nosnippet: bool = False
    noai_meta: bool = False

    def directives(self) -> set[str]:
        out: set[str] = set()
        for v in self.robots_meta + self.x_robots:
            v = v.strip()
            # "googlebot: nosnippet" -> nosnippet (bot-scoped directives are kept with prefix too)
            m = re.match(r"^([A-Za-z_-]+)\s*:\s*(.*)$", v)
            if m and not m.group(1).lower().startswith("max-"):
                out.update(f"{m.group(1).lower()}:{d.strip().lower()}" for d in m.group(2).split(","))
                v = m.group(2)
            out.update(d.strip().lower() for d in v.split(",") if d.strip())
        return out

    @property
    def nosnippet(self) -> bool:
        return "nosnippet" in self.directives() or "none" in self.directives()

    @property
    def noindex(self) -> bool:
        return "noindex" in self.directives() or "none" in self.directives()

    @property
    def max_snippet(self) -> int | None:
        for d in self.directives():
            m = re.match(r"max-snippet:\s*(-?\d+)", d)
            if m:
                return int(m.group(1))
        return None


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.metas: list[tuple[str, str]] = []
        self.data_nosnippet = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            name = (a.get("name") or a.get("http-equiv") or "").lower()
            if name:
                self.metas.append((name, a.get("content", "")))
        if "data-nosnippet" in a:
            self.data_nosnippet = True


def parse_page(headers: dict[str, str] | None = None, html: str | None = None) -> PageSignals:
    ps = PageSignals()
    for k, v in (headers or {}).items():
        kl = k.lower()
        if kl == "x-robots-tag":
            ps.x_robots.append(v)
        elif kl == "tdm-reservation":
            ps.tdm_reservation = v.strip() == "1"
        elif kl == "tdm-policy":
            ps.tdm_policy = v.strip()
        elif kl == "content-usage":
            ps.content_usage.update(parse_prefs(v))
    if html:
        mp = _MetaParser()
        try:
            mp.feed(html)
        except Exception:  # malformed HTML: keep what was parsed
            pass
        ps.data_nosnippet = mp.data_nosnippet
        for name, content in mp.metas:
            if name in ("robots", "googlebot", "bingbot"):
                ps.robots_meta.append(content if name == "robots" else f"{name}: {content}")
                if "noai" in content.lower() or "noimageai" in content.lower():
                    ps.noai_meta = True
            elif name == "tdm-reservation":
                ps.tdm_reservation = content.strip() == "1"
            elif name == "tdm-policy":
                ps.tdm_policy = content.strip()
            elif name == "content-usage":
                ps.content_usage.update(parse_prefs(content))
    return ps


def parse_tdmrep(text: str) -> list[dict]:
    """W3C TDMRep /.well-known/tdmrep.json: list of {location, tdm-reservation, tdm-policy}."""
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return []
    if isinstance(data, dict):
        data = [data]
    out = []
    for item in data if isinstance(data, list) else []:
        if isinstance(item, dict) and "location" in item:
            out.append(item)
    return out


def tdmrep_reserves_root(entries: list[dict]) -> bool:
    for e in entries:
        loc = str(e.get("location", ""))
        if loc in ("/", "/*", "*", "") or loc.endswith("://") or re.fullmatch(r"https?://[^/]+/?\*?", loc):
            try:
                if int(e.get("tdm-reservation", 0)) == 1:
                    return True
            except (TypeError, ValueError):
                continue
    return False


RESERVATION_PATTERNS = [
    r"text\s+and\s+data\s+mining", r"\bTDM\b", r"article\s+4\s*\(?3\)?", r"art\.\s*4\s*\(3\)",
    r"fouille\s+de\s+textes", r"L\.?\s*122-5-3", r"§\s*44b", r"Nutzungsvorbehalt", r"Text-?\s*und\s*Data-?\s*Mining",
    r"machine[- ]learning", r"(train|training)\s+(of\s+)?(ai|artificial intelligence|models?)", r"entra[iî]nement",
]


def tos_has_reservation(text: str | None) -> bool:
    if not text:
        return False
    hits = sum(1 for p in RESERVATION_PATTERNS if re.search(p, text, re.I))
    return hits >= 2
