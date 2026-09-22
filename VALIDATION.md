# Validation Record

Validated locally on 2026-09-21 with Docker Desktop and Python 3.13.

## Results

| Check | Result |
| --- | --- |
| Python compilation with warnings treated as errors | PASS |
| Unit and configuration policy tests | PASS (6/6) |
| Docker Compose model rendering | PASS |
| Loki readiness endpoint | PASS (HTTP 200) |
| Alloy readiness endpoint | PASS (HTTP 200) |
| Grafana health endpoint | PASS (HTTP 200, v13.2.2) |
| Grafana dashboard provisioning | PASS (`SIEM Logging Pipeline`, 7 panels) |
| Synthetic mixed scenario | PASS (13 events generated) |
| Loki ingestion assertion | PASS (13 events queryable) |
| Brute-force threshold assertion | PASS (7 matching failures; threshold is 5) |

## Commands

```powershell
python -m py_compile scripts\generator.py scripts\verify_pipeline.py tests\test_pipeline.py
python -W error -m unittest discover -s tests -v
$env:GRAFANA_ADMIN_PASSWORD = "validation-only-password"
docker compose config --quiet
docker compose up -d --build loki alloy grafana
docker compose build generator
docker compose run --rm generator --mode mixed --count 12
python scripts\verify_pipeline.py --attempts 30 --delay 2
```

The verifier reported:

```text
PASS: Loki contains 13 recent events; 7 match the brute-force condition.
```

## Published verification

- Repository: <https://github.com/jfrance167/siem-logging-pipeline>
- Initial successful GitHub Actions run: <https://github.com/jfrance167/siem-logging-pipeline/actions/runs/35684377420>
