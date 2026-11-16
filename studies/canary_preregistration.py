"""Why a neutral pre-registration of canaries gives court-grade false-positive control.

Research context (see docs/ARBITRE.md): per-document membership inference is
not reliable evidence of training use because the "not trained" null cannot be
sampled (Duan et al. COLM 2024; Das, Zhang, Tramer 2025; Zhang et al. SaTML
2025). Randomised canary designs fix this: before publication, canaries are
generated in pairs, one of each pair is chosen at random to be published, the
other is withheld, and a commitment (hash) to the whole design is timestamped
by a neutral party. Later, model scores (e.g. per-token loss) are compared
within pairs; under the null hypothesis the published/withheld labels are
exchangeable, so a sign-flip test has an EXACT false-positive rate.

This script checks that claim numerically and contrasts it with a naive test
that compares published canaries to "other" text drawn with a small
distribution shift (the failure mode documented for MIAs). It also runs the
commit-reveal protocol on the ledger hashing used by novarys.evidence.

No real model is used: scores are simulated. The test establishes the
statistical property, not the detectability on any given model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import secrets


def commit(seed: bytes, canaries: list[tuple[str, str]]) -> str:
    blob = seed + json.dumps(canaries, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def assignment(seed: bytes, n: int) -> list[int]:
    """Deterministic, unpredictable choice of which member of each pair is published."""
    return [hashlib.sha256(seed + i.to_bytes(4, "big")).digest()[0] & 1 for i in range(n)]


def sign_flip_pvalue(diffs: list[float], rnd: random.Random, draws: int = 2000) -> float:
    obs = sum(diffs)
    hits = 1
    for _ in range(draws):
        s = sum(d if rnd.random() < 0.5 else -d for d in diffs)
        if s >= obs:
            hits += 1
    return hits / (draws + 1)


def z_pvalue(a: list[float], b: list[float]) -> float:
    """Naive one-sided two-sample z-test that mean(a) > mean(b)."""
    na, nb = len(a), len(b)
    ma, mb = sum(a) / na, sum(b) / nb
    va = sum((x - ma) ** 2 for x in a) / (na - 1)
    vb = sum((x - mb) ** 2 for x in b) / (nb - 1)
    z = (ma - mb) / math.sqrt(va / na + vb / nb)
    return 0.5 * math.erfc(z / math.sqrt(2))


def trial(rnd, n_pairs, effect, shift):
    # score = how much "better" the model predicts the text (higher = more memorised)
    published = [rnd.gauss(effect, 1) for _ in range(n_pairs)]
    withheld = [rnd.gauss(0, 1) for _ in range(n_pairs)]
    other_text = [rnd.gauss(-shift, 1) for _ in range(n_pairs)]  # e.g. older/other-domain text
    p_paired = sign_flip_pvalue([p - w for p, w in zip(published, withheld)], rnd, draws=400)
    p_naive = z_pvalue(published, other_text)
    return p_paired, p_naive


def run(trials: int = 400, n_pairs: int = 500, alpha: float = 0.05, seed: int = 11) -> dict:
    rnd = random.Random(seed)
    out = {"n_pairs": n_pairs, "alpha": alpha, "trials": trials, "scenarios": []}
    for effect, shift, label in [(0.0, 0.0, "null, no shift"), (0.0, 0.2, "null, 0.2 SD shift in comparison text"),
                                 (0.05, 0.0, "trained, effect 0.05 SD"), (0.1, 0.0, "trained, effect 0.1 SD"),
                                 (0.2, 0.0, "trained, effect 0.2 SD")]:
        rej_paired = rej_naive = 0
        for _ in range(trials):
            pp, pn = trial(rnd, n_pairs, effect, shift)
            rej_paired += pp <= alpha
            rej_naive += pn <= alpha
        out["scenarios"].append({"scenario": label, "true_effect_sd": effect, "comparison_shift_sd": shift,
                                 "rejection_rate_preregistered_paired": round(rej_paired / trials, 3),
                                 "rejection_rate_naive_unpaired": round(rej_naive / trials, 3)})
    # commit-reveal protocol check
    s = secrets.token_bytes(32)
    pairs = [(secrets.token_hex(16), secrets.token_hex(16)) for _ in range(5)]
    c = commit(s, pairs)
    out["commit_reveal"] = {"commitment_sha256": c, "reveal_verifies": commit(s, pairs) == c,
                            "tampered_pair_detected": commit(s, [("x", "y")] + pairs[1:]) != c,
                            "assignment_example": assignment(s, 5)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results"))
    a = ap.parse_args()
    res = run()
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "canary_preregistration.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
