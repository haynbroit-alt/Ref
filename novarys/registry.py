"""Registry of AI and search agents, and of jurisdictions (data in novarys/data)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache

_DATA = os.path.join(os.path.dirname(__file__), "data")

# Training crawlers whose omission most weakens a training reservation (the
# seven most-blocked in the Tranco top-1M census, plus Cohere's crawler).
CORE_TRAINING = ["GPTBot", "ClaudeBot", "CCBot", "Google-Extended", "Applebot-Extended",
                 "meta-externalagent", "Bytespider", "cohere-training-data-crawler"]
VENDOR_NEUTRAL_TRAINING_TOKEN = "__usage_ai-training"


@dataclass(frozen=True)
class Agent:
    token: str
    operator: str
    purpose: str
    crawls: bool
    obeys_robots: str | None
    effect: str
    ip_ranges_url: str | None
    rdns: tuple[str, ...]
    doc_url: str | None
    status: str
    deprecated: bool = False
    replaced_by: tuple[str, ...] = field(default_factory=tuple)

    @property
    def key(self) -> str:
        return self.token.lower()


@lru_cache(maxsize=1)
def _load(name: str) -> dict:
    with open(os.path.join(_DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def agents() -> tuple[Agent, ...]:
    out = []
    for a in _load("agents.json")["agents"]:
        out.append(Agent(
            token=a["token"], operator=a["operator"], purpose=a["purpose"], crawls=a.get("crawls", True),
            obeys_robots=a.get("obeys_robots"), effect=a.get("effect", ""), ip_ranges_url=a.get("ip_ranges_url"),
            rdns=tuple(a.get("rdns") or ()), doc_url=a.get("doc_url"), status=a.get("status", "unverified"),
            deprecated=a.get("deprecated", False), replaced_by=tuple(a.get("replaced_by") or ()),
        ))
    return tuple(out)


def agent(token: str) -> Agent | None:
    t = token.lower()
    for a in agents():
        if a.key == t:
            return a
    return None


def by_purpose(purpose: str, include_deprecated: bool = False) -> list[Agent]:
    return [a for a in agents() if a.purpose == purpose and (include_deprecated or not a.deprecated)]


def ai_referrers() -> dict[str, str]:
    return dict(_load("agents.json")["ai_referrers"])


def registry_version() -> str:
    return _load("agents.json")["version"]


@lru_cache(maxsize=1)
def _jur() -> dict:
    with open(os.path.join(_DATA, "jurisdictions.json"), encoding="utf-8") as fh:
        return json.load(fh)


def jurisdiction(code: str) -> dict | None:
    m = _jur()["markets"].get(code.upper())
    if m is None:
        return None
    if "inherits" in m:
        base = dict(_jur()["markets"][m["inherits"]])
        base.update(m)
        return base
    return m


def jurisdictions() -> dict[str, dict]:
    return {k: jurisdiction(k) for k in _jur()["markets"]}


def legal_disclaimer() -> str:
    return _jur()["disclaimer"]
