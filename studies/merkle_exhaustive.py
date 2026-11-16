"""Exhaustive check of novarys.transparency proofs (backs the '7,598 checks' figure in docs/ARBITRE.md).

For every tree size in SIZES: every leaf's inclusion proof must verify and must
fail for a wrong index; every consistency proof from each smaller size must
verify and must fail for a forged old root. Deterministic (seeded leaves).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from novarys.transparency import Tree, leaf_hash, verify_consistency, verify_inclusion  # noqa: E402

SIZES = list(range(1, 70)) + [127, 128, 129, 1000]


def run() -> dict:
    checks = failures = 0
    for n in SIZES:
        leaves = [leaf_hash(hashlib.sha256(f"{n}:{i}".encode()).digest()) for i in range(n)]
        t = Tree(leaves)
        root = t.mth()
        for i in range(n):
            checks += 1
            proof = t.inclusion_proof(i)
            failures += not verify_inclusion(leaves[i], i, n, proof, root)
            if n > 1:
                failures += verify_inclusion(leaves[i], (i + 1) % n, n, proof, root)
        for m in range(1, n + 1):
            checks += 1
            proof = t.consistency_proof(m)
            failures += not verify_consistency(m, n, Tree(leaves[:m]).mth(), root, proof)
            if m < n:
                failures += verify_consistency(m, n, leaf_hash(b"forged"), root, proof)
    return {"sizes": len(SIZES), "max_size": max(SIZES), "checks": checks, "failures": failures}


if __name__ == "__main__":
    res = run()
    out = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "merkle_exhaustive.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print(json.dumps(res))
