import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import sys
sys.path.insert(0, str(ROOT / "scripts"))

import generator


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.base = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def test_mixed_mode_contains_normal_and_detectable_attack(self):
        events = generator.generate_events("mixed", 12, 42, self.base)
        attacks = [event for event in events if event["scenario"] == "brute_force"]
        self.assertGreaterEqual(len(attacks), 5)
        self.assertTrue(all(event["outcome"] == "failure" for event in attacks))
        self.assertIn("normal", {event["scenario"] for event in events})

    def test_generator_is_deterministic(self):
        first = generator.generate_events("password-spray", 6, 42, self.base)
        second = generator.generate_events("password-spray", 6, 42, self.base)
        self.assertEqual(first, second)
        self.assertEqual(6, len({event["username"] for event in first}))

    def test_cli_writes_valid_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "events.jsonl"
            result = generator.main([
                "--mode", "brute-force", "--count", "7", "--seed", "7",
                "--base-time", "2026-01-01T00:00:00Z", "--output", str(output),
            ])
            records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(0, result)
            self.assertEqual(7, len(records))
            self.assertTrue(all(record["source_ip"] == "203.0.113.200" for record in records))


class ConfigurationTests(unittest.TestCase):
    def test_dashboard_is_valid_and_contains_detection_query(self):
        dashboard = json.loads((ROOT / "grafana/provisioning/dashboards/siem-dashboard.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(dashboard["panels"]), 6)
        expressions = json.dumps(dashboard)
        self.assertIn("brute_force", expressions)
        self.assertIn("count_over_time", expressions)

    def test_images_are_version_pinned_and_ports_are_local(self):
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertNotIn(":latest", compose)
        self.assertEqual(3, compose.count('"127.0.0.1:'))
        self.assertIn("grafana/alloy:v1.19.2", compose)
        self.assertIn("grafana/loki:3.7.8", compose)
        self.assertIn("grafana/grafana:13.2.2", compose)

    def test_alloy_does_not_promote_high_cardinality_fields(self):
        config = (ROOT / "alloy/config.alloy").read_text(encoding="utf-8")
        labels = config.split('stage.labels {', 1)[1].split('}', 2)[0]
        self.assertNotIn("source_ip", labels)
        self.assertNotIn("username", labels)


if __name__ == "__main__":
    unittest.main()

