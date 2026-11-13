#!/usr/bin/env python3
"""Endpoint uptime checker. Prints human-readable report; exits 0 always.
First line of output is STATUS: OK or STATUS: FAIL."""
import urllib.request
import socket
import sys

CHECKS = [
    ("MausBot", "https://bot.caishen.today/api/health"),
    ("caishen.today", "https://caishen.today"),
    ("NowledgeMem", "https://nmem.caishen2049.us/health"),
    ("Hermes(小曼)", "https://hermes.zyenglish.cc"),
    ("Agent2api", "https://api.caisheng.art/health"),
]

TIMEOUT = 20


def check(name: str, url: str) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "caishen-ops/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return 200 <= r.status < 400, f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def main() -> None:
    results = []
    for name, url in CHECKS:
        ok, detail = check(name, url)
        results.append((name, url, ok, detail))
    for name, url, ok, detail in results:
        print(f"{'✅' if ok else '❌'} {name:14s} {detail:24s} {url}")
    failed = [r for r in results if not r[2]]
    print(f"STATUS: {'FAIL' if failed else 'OK'} ({len(failed)}/{len(results)} down)")


if __name__ == "__main__":
    sys.exit(0)
