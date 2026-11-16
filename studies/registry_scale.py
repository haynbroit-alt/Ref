"""Can a neutral reservation registry run at web scale and be verified by anyone?

Test: build an append-only Merkle transparency log (RFC 9162 / Certificate
Transparency hashing: leaf = H(0x00||data), node = H(0x01||left||right)) over
the reservation state of ~1M real domains (Crawlora AI-Crawler Blocking Index,
Tranco top 1M, CC BY 4.0), then measure build time, size, inclusion-proof size
and verification time, and check that tampering with one record is detected.

A publisher, an AI provider or a court can then verify "domain D reserved
against agent X in snapshot S" from the published root hash alone, without
trusting the operator: the property an arbiter needs.

Usage: python studies/registry_scale.py path/to/results.jsonl.gz [--out studies/results]
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import random
import time


import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from novarys.transparency import Tree, leaf_hash, verify_consistency, verify_inclusion  # noqa: E402


def canonical(rec: dict, snapshot: str) -> bytes:
    body = {"domain": rec["domain"], "snapshot": snapshot, "robots": bool(rec.get("has_robots")),
            "blocks": sorted(rec.get("blocks_ai") or []), "star_disallow_root": bool(rec.get("star_disallow_root"))}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


def run(path: str) -> dict:
    snapshot = "crawlora-2026-06-20"
    t0 = time.perf_counter()
    records, leaves = [], []
    for line in gzip.open(path, "rt", encoding="utf-8"):
        rec = json.loads(line)
        data = canonical(rec, snapshot)
        records.append(data)
        leaves.append(leaf_hash(data))
    t_load = time.perf_counter() - t0
    log = Tree(leaves)
    t1 = time.perf_counter()
    root = log.mth()
    t_root = time.perf_counter() - t1
    rnd = random.Random(42)
    idx = rnd.sample(range(len(leaves)), 1000)
    t2 = time.perf_counter()
    proofs = [log.inclusion_proof(i) for i in idx]
    t_proof = (time.perf_counter() - t2) / len(idx)
    t3 = time.perf_counter()
    ok = all(verify_inclusion(leaves[i], i, len(leaves), p, root) for i, p in zip(idx, proofs))
    t_verify = (time.perf_counter() - t3) / len(idx)
    # tamper test: change one record (e.g. pretend a domain did not block GPTBot)
    i = idx[0]
    forged = json.loads(records[i])
    forged["blocks"] = [b for b in forged["blocks"] if b != "gptbot"] + ["__forged__"]
    forged_leaf = leaf_hash(json.dumps(forged, sort_keys=True, separators=(",", ":")).encode())
    tamper_detected = not verify_inclusion(forged_leaf, i, len(leaves), proofs[0], root)
    # consistency: the full log only appended to its first 900,000 records
    m = 900_000
    old_root = log.mth(0, m)
    t4 = time.perf_counter()
    cproof = log.consistency_proof(m)
    consistent = verify_consistency(m, len(leaves), old_root, root, cproof)
    t_cons = time.perf_counter() - t4
    raw_bytes = sum(len(r) for r in records)
    return {
        "snapshot": snapshot, "records": len(records), "canonical_bytes_total": raw_bytes,
        "canonical_bytes_gzip_estimate": len(gzip.compress(b"\n".join(records[:100000]))) * len(records) // 100000,
        "root_sha256": root.hex(), "build_seconds": round(t_load + t_root, 2),
        "root_seconds": round(t_root, 2), "proof_hashes": len(proofs[0]), "proof_bytes": 32 * len(proofs[0]),
        "proof_ms": round(1000 * t_proof, 3), "verify_ms": round(1000 * t_verify, 3),
        "all_1000_proofs_verified": ok, "tamper_detected": tamper_detected,
        "consistency_900k_to_full_verified": consistent, "consistency_proof_hashes": len(cproof),
        "consistency_seconds": round(t_cons, 3), "implementation": "novarys.transparency",
        "example_record": records[i].decode(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results"))
    a = ap.parse_args()
    res = run(a.data)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "registry_scale.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
