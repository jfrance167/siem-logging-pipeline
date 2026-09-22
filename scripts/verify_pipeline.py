#!/usr/bin/env python3
"""Verify Loki readiness, ingestion, and brute-force detection evidence."""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request


def request_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=5) as response:  # nosec B310: lab URL is operator-supplied
        return json.load(response)


def query_loki(base_url: str, query: str) -> list[dict[str, object]]:
    url = f"{base_url.rstrip('/')}/loki/api/v1/query?{urllib.parse.urlencode({'query': query})}"
    document = request_json(url)
    if document.get("status") != "success":
        raise RuntimeError(f"Loki query failed: {document}")
    return document["data"]["result"]  # type: ignore[index]


def scalar_count(results: list[dict[str, object]]) -> int:
    return sum(int(float(item["value"][1])) for item in results)  # type: ignore[index]


def verify(base_url: str, attempts: int, delay: float) -> tuple[int, int]:
    total_query = 'sum(count_over_time({job="authentication-lab"}[15m]))'
    brute_query = 'sum(count_over_time({job="authentication-lab",scenario="brute_force",outcome="failure"}[5m]))'
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            total = scalar_count(query_loki(base_url, total_query))
            brute_force = scalar_count(query_loki(base_url, brute_query))
            if total > 0 and brute_force >= 5:
                return total, brute_force
        except (OSError, KeyError, TypeError, ValueError, RuntimeError) as error:
            last_error = error
        time.sleep(delay)
    raise RuntimeError(f"pipeline verification failed after {attempts} attempts; last error: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loki-url", default="http://localhost:3100")
    parser.add_argument("--attempts", type=int, default=20)
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()
    total, brute_force = verify(args.loki_url, args.attempts, args.delay)
    print(f"PASS: Loki contains {total} recent events; {brute_force} match the brute-force condition.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

