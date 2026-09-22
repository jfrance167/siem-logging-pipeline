#!/usr/bin/env python3
"""Generate deterministic, synthetic authentication telemetry for the SIEM lab."""

from __future__ import annotations

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

DOCUMENTATION_IPS = ("192.0.2.10", "198.51.100.24", "203.0.113.77")
USERS = ("analyst", "developer", "helpdesk", "service-backup")


def _event(base: datetime, index: int, *, username: str, source_ip: str,
           outcome: str, scenario: str, seed: int) -> dict[str, object]:
    timestamp = base + timedelta(seconds=index * 20)
    severity = "low" if outcome == "success" else "medium"
    return {
        "timestamp": timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "event_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"siem-lab:{seed}:{scenario}:{index}")),
        "event_type": "authentication",
        "host": "auth-lab-01",
        "service": "sshd",
        "username": username,
        "source_ip": source_ip,
        "source_port": 41000 + index,
        "destination_port": 22,
        "outcome": outcome,
        "severity": severity,
        "scenario": scenario,
        "message": f"Authentication {outcome} for {username} from {source_ip}",
    }


def generate_events(mode: str, count: int, seed: int, base: datetime) -> list[dict[str, object]]:
    if base.tzinfo is None:
        raise ValueError("base timestamp must include a timezone")
    rng = random.Random(seed)
    events: list[dict[str, object]] = []

    if mode in {"normal", "mixed"}:
        normal_count = count if mode == "normal" else max(5, count // 2)
        for index in range(normal_count):
            events.append(_event(
                base, len(events), username=rng.choice(USERS),
                source_ip=rng.choice(DOCUMENTATION_IPS), outcome="success",
                scenario="normal", seed=seed,
            ))

    if mode in {"brute-force", "mixed"}:
        attack_count = max(7, count if mode == "brute-force" else count // 2)
        for _ in range(attack_count):
            events.append(_event(
                base, len(events), username="admin", source_ip="203.0.113.200",
                outcome="failure", scenario="brute_force", seed=seed,
            ))

    if mode == "password-spray":
        for index in range(max(6, count)):
            events.append(_event(
                base, len(events), username=f"employee-{index + 1:02d}",
                source_ip="198.51.100.200", outcome="failure",
                scenario="password_spray", seed=seed,
            ))

    return events


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("normal", "brute-force", "password-spray", "mixed"), default="mixed")
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--base-time", type=parse_timestamp)
    parser.add_argument("--output", type=Path, default=Path("/data/security-events.jsonl"))
    parser.add_argument("--append", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 1 <= args.count <= 10_000:
        raise SystemExit("--count must be between 1 and 10000")
    # Keep the complete generated sequence in the recent past so Loki accepts
    # every sample and time-window queries immediately include the attack burst.
    base = args.base_time or datetime.now(timezone.utc) - timedelta(minutes=5)
    events = generate_events(args.mode, args.count, args.seed, base)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.append else "w"
    with args.output.open(mode, encoding="utf-8", newline="\n") as stream:
        for event in events:
            stream.write(json.dumps(event, separators=(",", ":"), sort_keys=True) + "\n")
    print(f"Wrote {len(events)} synthetic events to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
