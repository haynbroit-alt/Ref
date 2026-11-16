"""Pre-registered canaries: an evidence design with an exact false-positive rate.

Per-document membership inference cannot prove training use (the "not trained"
null cannot be sampled; Duan et al. COLM 2024, Das et al. 2025, Zhang et al.
SaTML 2025). A randomised design can: canaries are generated in pairs, a
secret seed decides which member of each pair is published, and a commitment
to (seed, pairs) is made public BEFORE publication (transparency log + RFC 3161
timestamp). Later, any party can supply model scores (e.g. per-token loss or
log-likelihood, higher = better predicted) and run a paired sign-flip test:
under the null hypothesis the labels are exchangeable, so the p-value is exact.

Detection power depends on access to the model (log-probabilities or weights)
and on how often the canaries were seen during training; with text-only access
only heavy memorisation is detectable. See studies/canary_preregistration.py.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import random
import secrets

SYLLABLES = ["ka", "lo", "mi", "ve", "tor", "zu", "pra", "nel", "qui", "sha", "dro", "fen", "gal", "rix", "bo", "tem"]


def _word(rnd: random.Random) -> str:
    return "".join(rnd.choice(SYLLABLES) for _ in range(rnd.randint(2, 4)))


def make_canary(rnd: random.Random, words: int = 12) -> str:
    return " ".join(_word(rnd) for _ in range(words)) + " " + "".join(rnd.choice("0123456789abcdef") for _ in range(12))


def create(n_pairs: int, seed: bytes | None = None) -> dict:
    """Return the secret design (keep private) and its public commitment."""
    seed = seed or secrets.token_bytes(32)
    rnd = random.Random(hashlib.sha256(seed + b"text").digest())
    pairs = [(make_canary(rnd), make_canary(rnd)) for _ in range(n_pairs)]
    secret = {"seed_hex": seed.hex(), "pairs": pairs}
    return {"secret": secret, "commitment": commitment(secret), "published": published(secret)}


def commitment(secret: dict) -> dict:
    blob = json.dumps(secret, sort_keys=True, separators=(",", ":")).encode()
    return {"type": "canary-commitment", "n_pairs": len(secret["pairs"]), "sha256": hashlib.sha256(blob).hexdigest()}


def assignment(secret: dict) -> list[int]:
    seed = bytes.fromhex(secret["seed_hex"])
    return [hashlib.sha256(seed + b"pick" + i.to_bytes(4, "big")).digest()[0] & 1 for i in range(len(secret["pairs"]))]


def published(secret: dict) -> list[str]:
    return [pair[a] for pair, a in zip(secret["pairs"], assignment(secret))]


def withheld(secret: dict) -> list[str]:
    return [pair[1 - a] for pair, a in zip(secret["pairs"], assignment(secret))]


def verify_reveal(secret: dict, public_commitment: dict) -> bool:
    return commitment(secret)["sha256"] == public_commitment["sha256"]


def test(secret: dict, scores: dict[str, float], draws: int = 20000, rng_seed: int = 0) -> dict:
    """Paired sign-flip test; exact enumeration for up to 20 pairs, seeded Monte Carlo otherwise."""
    pub, wit = published(secret), withheld(secret)
    diffs = [scores[p] - scores[w] for p, w in zip(pub, wit) if p in scores and w in scores]
    n = len(diffs)
    if n == 0:
        raise ValueError("no scored pairs")
    obs = sum(diffs)
    if n <= 20:
        total = hits = 0
        for signs in itertools.product((1, -1), repeat=n):
            total += 1
            hits += sum(s * d for s, d in zip(signs, diffs)) >= obs - 1e-12
        p, mode = hits / total, "exact"
    else:
        rnd = random.Random(rng_seed)
        hits = 1 + sum(1 for _ in range(draws) if sum(d if rnd.random() < 0.5 else -d for d in diffs) >= obs - 1e-12)
        p, mode = hits / (draws + 1), f"monte-carlo ({draws} draws, seed {rng_seed})"
    return {"pairs_scored": n, "mean_difference": obs / n, "p_value": p, "mode": mode,
            "reading": "small p-values indicate the model predicts published canaries better than their withheld twins"}
