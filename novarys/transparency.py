"""Append-only Merkle transparency log (RFC 9162 hashing) for public commitments.

Anyone holding a published tree head (size + root hash) can verify, without
trusting the operator:
- inclusion: "this record is in the log" (O(log n) hashes);
- consistency: "the newer log only appended to the older one" (no rewriting),
  which is the property that makes an operator credible as a neutral party.

Tree heads are anchored with an RFC 3161 timestamp request (see
novarys.evidence.timestamp_request) and can be published anywhere (e.g. in a
public git history). Hashing follows RFC 9162 §2.1: leaf = SHA-256(0x00 || d),
node = SHA-256(0x01 || left || right).
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass


def _h(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def leaf_hash(data: bytes) -> bytes:
    return _h(b"\x00" + data)


def node_hash(left: bytes, right: bytes) -> bytes:
    return _h(b"\x01" + left + right)


def _split(n: int) -> int:
    """Largest power of two strictly smaller than n (n >= 2)."""
    k = 1
    while k << 1 < n:
        k <<= 1
    return k


def canonical(record: dict) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class Tree:
    """Merkle tree over a list of leaf hashes, with memoised subtree roots."""

    def __init__(self, leaves: list[bytes]):
        self.leaves = leaves
        self._memo: dict[tuple[int, int], bytes] = {}

    def mth(self, lo: int = 0, hi: int | None = None) -> bytes:
        hi = len(self.leaves) if hi is None else hi
        n = hi - lo
        if n == 0:
            return _h(b"")
        if n == 1:
            return self.leaves[lo]
        key = (lo, hi)
        v = self._memo.get(key)
        if v is None:
            k = _split(n)
            v = node_hash(self.mth(lo, lo + k), self.mth(lo + k, hi))
            if n >= 32:
                self._memo[key] = v
        return v

    def inclusion_proof(self, index: int, size: int | None = None) -> list[bytes]:
        size = len(self.leaves) if size is None else size
        if not 0 <= index < size <= len(self.leaves):
            raise IndexError("index outside tree")
        return self._path(index, 0, size)

    def _path(self, m: int, lo: int, hi: int) -> list[bytes]:
        n = hi - lo
        if n == 1:
            return []
        k = _split(n)
        if m - lo < k:
            return self._path(m, lo, lo + k) + [self.mth(lo + k, hi)]
        return self._path(m, lo + k, hi) + [self.mth(lo, lo + k)]

    def consistency_proof(self, old_size: int, new_size: int | None = None) -> list[bytes]:
        new_size = len(self.leaves) if new_size is None else new_size
        if not 0 < old_size <= new_size <= len(self.leaves):
            raise ValueError("invalid sizes")
        if old_size == new_size:
            return []
        return self._subproof(old_size, 0, new_size, True)

    def _subproof(self, m: int, lo: int, hi: int, complete: bool) -> list[bytes]:
        n = hi - lo
        if m == n:
            return [] if complete else [self.mth(lo, hi)]
        k = _split(n)
        if m <= k:
            return self._subproof(m, lo, lo + k, complete) + [self.mth(lo + k, hi)]
        return self._subproof(m - k, lo + k, hi, False) + [self.mth(lo, lo + k)]


def verify_inclusion(leaf: bytes, index: int, size: int, proof: list[bytes], root: bytes) -> bool:
    """RFC 9162 §2.1.3.2."""
    if index >= size or size < 1:
        return False
    fn, sn, r = index, size - 1, leaf
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


def verify_consistency(old_size: int, new_size: int, old_root: bytes, new_root: bytes, proof: list[bytes]) -> bool:
    """RFC 9162 §2.1.4.2."""
    if old_size < 1 or old_size > new_size:
        return False
    if old_size == new_size:
        return not proof and old_root == new_root
    path = list(proof)
    if old_size & (old_size - 1) == 0:  # exact power of two
        path = [old_root] + path
    if not path:
        return False
    fn, sn = old_size - 1, new_size - 1
    while fn & 1:
        fn >>= 1
        sn >>= 1
    fr = sr = path[0]
    for c in path[1:]:
        if sn == 0:
            return False
        if fn & 1 or fn == sn:
            fr = node_hash(c, fr)
            sr = node_hash(c, sr)
            while not fn & 1 and fn != 0:
                fn >>= 1
                sn >>= 1
        else:
            sr = node_hash(sr, c)
        fn >>= 1
        sn >>= 1
    return fr == old_root and sr == new_root and sn == 0


@dataclass
class TreeHead:
    size: int
    root: str  # hex

    def to_dict(self) -> dict:
        return {"tree_size": self.size, "root_sha256": self.root, "hashing": "RFC 9162 (SHA-256)"}

    def digest(self) -> str:
        return hashlib.sha256(canonical(self.to_dict())).hexdigest()


class Log:
    """File-backed append-only log: records.jsonl (one canonical record per line)."""

    def __init__(self, directory: str):
        self.dir = directory
        os.makedirs(directory, exist_ok=True)
        self.path = os.path.join(directory, "records.jsonl")
        self._records: list[bytes] | None = None
        self._tree: Tree | None = None

    def records(self) -> list[bytes]:
        if self._records is None:
            self._records = []
            if os.path.exists(self.path):
                with open(self.path, "rb") as fh:
                    self._records = [line.rstrip(b"\n") for line in fh if line.strip()]
        return self._records

    def tree(self) -> Tree:
        if self._tree is None or len(self._tree.leaves) != len(self.records()):
            self._tree = Tree([leaf_hash(r) for r in self.records()])
        return self._tree

    def append(self, record: dict) -> int:
        data = canonical(record)
        recs = self.records()  # load existing records BEFORE writing, or the new one is counted twice
        with open(self.path, "ab") as fh:
            fh.write(data + b"\n")
        recs.append(data)
        self._tree = None
        return len(self.records()) - 1

    def head(self) -> TreeHead:
        return TreeHead(len(self.records()), self.tree().mth().hex())

    def find(self, predicate) -> list[int]:
        return [i for i, r in enumerate(self.records()) if predicate(json.loads(r))]

    def prove(self, index: int) -> dict:
        t = self.tree()
        return {"index": index, "record": json.loads(self.records()[index]), "tree_size": len(t.leaves),
                "root_sha256": t.mth().hex(), "proof": [p.hex() for p in t.inclusion_proof(index)]}

    def prove_consistency(self, old_size: int) -> dict:
        t = self.tree()
        return {"old_size": old_size, "old_root_sha256": t.mth(0, old_size).hex(), "new_size": len(t.leaves),
                "new_root_sha256": t.mth().hex(), "proof": [p.hex() for p in t.consistency_proof(old_size)]}


def check_inclusion(proof: dict) -> bool:
    """Verify a proof produced by Log.prove using only the proof itself and its root."""
    return verify_inclusion(leaf_hash(canonical(proof["record"])), proof["index"], proof["tree_size"],
                            [bytes.fromhex(p) for p in proof["proof"]], bytes.fromhex(proof["root_sha256"]))


def check_consistency(proof: dict) -> bool:
    return verify_consistency(proof["old_size"], proof["new_size"], bytes.fromhex(proof["old_root_sha256"]),
                              bytes.fromhex(proof["new_root_sha256"]), [bytes.fromhex(p) for p in proof["proof"]])
