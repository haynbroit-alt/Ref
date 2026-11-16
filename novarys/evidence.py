"""Tamper-evident evidence ledger for AI-usage signals.

In a dispute the question is often "was the reservation in place when the
crawler fetched the page?". The ledger stores dated snapshots of robots.txt,
TDMRep, headers and terms in an append-only, hash-chained log. The head hash
can be anchored with an RFC 3161 trusted timestamp: :func:`timestamp_request`
builds the DER request, which the user sends to any TSA (e.g. with curl) and
verifies with ``openssl ts -verify``.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

GENESIS = "0" * 64


def _canon(d: dict) -> bytes:
    return json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass
class Entry:
    seq: int
    ts: str
    kind: str
    url: str
    sha256: str
    size: int
    meta: dict
    prev: str
    hash: str


class Ledger:
    def __init__(self, directory: str):
        self.dir = directory
        self.log = os.path.join(directory, "ledger.jsonl")
        self.objects = os.path.join(directory, "objects")
        os.makedirs(self.objects, exist_ok=True)

    # ------------------------------------------------------------------
    def entries(self) -> list[Entry]:
        if not os.path.exists(self.log):
            return []
        out = []
        with open(self.log, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    out.append(Entry(**json.loads(line)))
        return out

    def head(self) -> str:
        e = self.entries()
        return e[-1].hash if e else GENESIS

    def add(self, url: str, content: bytes, kind: str = "snapshot", meta: dict | None = None, ts: str | None = None) -> Entry:
        digest = hashlib.sha256(content).hexdigest()
        obj = os.path.join(self.objects, digest)
        if not os.path.exists(obj):
            with open(obj, "wb") as fh:
                fh.write(content)
        prev_entries = self.entries()
        body = {
            "seq": len(prev_entries), "ts": ts or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "kind": kind, "url": url, "sha256": digest, "size": len(content), "meta": meta or {},
            "prev": prev_entries[-1].hash if prev_entries else GENESIS,
        }
        body["hash"] = hashlib.sha256(_canon(body)).hexdigest()
        with open(self.log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(body, ensure_ascii=False) + "\n")
        return Entry(**body)

    def content(self, entry: Entry) -> bytes:
        with open(os.path.join(self.objects, entry.sha256), "rb") as fh:
            return fh.read()

    def verify(self) -> list[str]:
        """Return a list of problems (empty = chain intact and every object matches)."""
        problems = []
        prev = GENESIS
        for i, e in enumerate(self.entries()):
            body = dict(e.__dict__)
            h = body.pop("hash")
            if e.seq != i:
                problems.append(f"entry {i}: sequence number {e.seq}")
            if e.prev != prev:
                problems.append(f"entry {i}: broken chain (prev={e.prev[:12]}, expected {prev[:12]})")
            if hashlib.sha256(_canon(body)).hexdigest() != h:
                problems.append(f"entry {i}: entry hash mismatch (entry was modified)")
            obj = os.path.join(self.objects, e.sha256)
            if not os.path.exists(obj):
                problems.append(f"entry {i}: missing object {e.sha256[:12]}")
            else:
                with open(obj, "rb") as fh:
                    if hashlib.sha256(fh.read()).hexdigest() != e.sha256:
                        problems.append(f"entry {i}: object {e.sha256[:12]} was modified")
            prev = h
        return problems

    def state_at(self, url: str, when: str) -> Entry | None:
        """Latest snapshot of *url* recorded at or before ISO time *when*."""
        t = _parse_ts(when)
        best = None
        for e in self.entries():
            if e.url == url and _parse_ts(e.ts) <= t:
                best = e
        return best


def _parse_ts(s: str) -> datetime:
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


# ----------------------------------------------------------------------
# RFC 3161 TimeStampReq (DER), no third-party dependency

def _der_len(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    b = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(b)]) + b


def _tlv(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + _der_len(len(value)) + value


def _der_int(n: int) -> bytes:
    b = n.to_bytes(max(1, (n.bit_length() + 8) // 8), "big", signed=False)
    if b[0] & 0x80:
        b = b"\x00" + b
    return _tlv(0x02, b)


SHA256_OID = bytes.fromhex("0609608648016503040201")


def timestamp_request(sha256_hex: str, nonce: int | None = None, cert_req: bool = True) -> bytes:
    digest = bytes.fromhex(sha256_hex)
    if len(digest) != 32:
        raise ValueError("expected a SHA-256 digest")
    alg = _tlv(0x30, SHA256_OID + b"\x05\x00")
    imprint = _tlv(0x30, alg + _tlv(0x04, digest))
    body = _der_int(1) + imprint + _der_int(nonce if nonce is not None else secrets.randbits(63))
    if cert_req:
        body += b"\x01\x01\xff"
    return _tlv(0x30, body)
