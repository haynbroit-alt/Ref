"""Conformance benchmark against Google's reference robots.txt test-suite.

The fixture ``google_robots_conformance.json`` is extracted (read as data, not
executed) from ``robots_test.cc`` of github.com/google/robotstxt (Apache-2.0).
Tests named ``ID_*`` check RFC 9309 behaviour; ``GoogleOnly_*`` check Google
extensions (e.g. accepting a missing colon). The RFC part must pass entirely;
Google-only deviations are reported, not hidden.
"""
import json
import os
import unittest
from urllib.parse import urlsplit

from novarys.robots import parse

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "google_robots_conformance.json")


def path_of(url: str) -> str:
    if not url:
        return "/"
    if url.startswith("/"):
        p = url
    else:
        if "://" not in url:
            url = "//" + url
        parts = urlsplit(url)
        p = parts.path or "/"
        if parts.query:
            p += "?" + parts.query
        return p
    return p.split("#", 1)[0]


def run_suite():
    with open(FIXTURE, encoding="utf-8") as fh:
        data = json.load(fh)
    results = {"ID": [0, 0, []], "GoogleOnly": [0, 0, []]}
    for test in data:
        bucket = "GoogleOnly" if test["test"].startswith("GoogleOnly") else "ID"
        for case in test["cases"]:
            got = parse(case["robots"]).can_fetch(case["agent"], path_of(case["url"])) if case["agent"] else True
            ok = got == case["expected"]
            results[bucket][0] += ok
            results[bucket][1] += 1
            if not ok:
                results[bucket][2].append((test["test"], case["agent"], case["url"], case["expected"]))
    return results


class TestGoogleConformance(unittest.TestCase):
    def test_rfc_cases_pass(self):
        res = run_suite()
        passed, total, failures = res["ID"]
        print(f"\nRFC 9309 (ID_*) conformance: {passed}/{total}")
        print(f"Google-only extensions:      {res['GoogleOnly'][0]}/{res['GoogleOnly'][1]}")
        for f in res["GoogleOnly"][2]:
            print("  google-only deviation:", f)
        self.assertEqual(failures, [], failures)


if __name__ == "__main__":
    unittest.main()
