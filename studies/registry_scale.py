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


def h(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def leaf_hash(data: bytes) -> bytes:
    return h(b"\x00" + data)


def node_hash(left: bytes, right: bytes) -> bytes:
    return h(b"\x01" + left + right)


def largest_pow2_below(n: int) -> int:
    k = 1
    while k << 1 < n:
        k <<= 1
    return k


class MerkleLog:
    """RFC 9162 Merkle tree with cached levels for fast proofs."""

    def __init__(self, leaves: list[bytes]):
        self.leaves = leaves

    def root(self) -> bytes:
        return self._mth(0, len(self.leaves))

    def _mth(self, lo: int, hi: int) -> bytes:
        n = hi - lo
        if n == 1:
            return self.leaves[lo]
        k = largest_pow2_below(n)
        return node_hash(self._mth(lo, lo + k), self._mth(lo + k, hi))

    def inclusion_proof(self, m: int) -> list[bytes]:
        return self._path(m, 0, len(self.leaves))

    def _path(self, m: int, lo: int, hi: int) -> list[bytes]:
        n = hi - lo
        if n == 1:
            return []
        k = largest_pow2_below(n)
        if m - lo < k:
            return self._path(m, lo, lo + k) + [self._mth(lo + k, hi)]
        return self._path(m, lo + k, hi) + [self._mth(lo, lo + k)]


def verify_inclusion(leaf: bytes, index: int, size: int, proof: list[bytes], root: bytes) -> bool:
    """RFC 9162 §2.1.3.2 verification algorithm."""
    if index >= size:
        return False
    fn, sn = index, size - 1
    r = leaf
    for p in proof:
        if sn == 0:
            return False
        if fn & 1 or fn == sn:
            r = node_hash(p, r)
            while not fn & 1 and fn != 0:
                fn >>= 1
                sn >>= 1
        else:
            r = node_hash(r, p)
        fn >>= 1
        sn >>= 1
    return sn == 0 and r == root


def canonical(rec: dict, snapshot: str) -> bytes:
    body = {"domain": rec["domain"], "snapshot": snapshot, "robots": bool(rec.get("has_robots")),
            "blocks": sorted(rec.get("blocks_ai") or []), "star_disallow_root": bool(rec.get("star_disallow_root"))}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


class FastMerkle(MerkleLog):
    """Same tree, built bottom-up once so that proofs are O(log n) lookups."""

    def __init__(self, leaves: list[bytes]):
        super().__init__(leaves)
        self.memo: dict[tuple[int, int], bytes] = {}

    def _mth(self, lo: int, hi: int) -> bytes:
        key = (lo, hi)
        v = self.memo.get(key)
        if v is None:
            v = super()._mth(lo, hi)
            if hi - lo >= 64:  # memoise only the upper levels to bound memory
                self.memo[key] = v
        return v


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
    log = FastMerkle(leaves)
    t1 = time.perf_counter()
    root = log.root()
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
    raw_bytes = sum(len(r) for r in records)
    return {
        "snapshot": snapshot, "records": len(records), "canonical_bytes_total": raw_bytes,
        "canonical_bytes_gzip_estimate": len(gzip.compress(b"\n".join(records[:100000]))) * len(records) // 100000,
        "root_sha256": root.hex(), "build_seconds": round(t_load + t_root, 2),
        "root_seconds": round(t_root, 2), "proof_hashes": len(proofs[0]), "proof_bytes": 32 * len(proofs[0]),
        "proof_ms": round(1000 * t_proof, 3), "verify_ms": round(1000 * t_verify, 3),
        "all_1000_proofs_verified": ok, "tamper_detected": tamper_detected,
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
