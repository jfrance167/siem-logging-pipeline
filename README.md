# SIEM Logging Pipeline Lab

A local, containerized security-monitoring pipeline that generates synthetic authentication telemetry, ships it with Grafana Alloy, stores it in Grafana Loki, and visualizes detection evidence in Grafana.

This complements the separate SIEM Detection Engineering Lab: that project focuses on offline correlation and ATT&CK-mapped alerts, while this project demonstrates live collection, transport, storage, querying, and dashboards.

## Architecture

```text
Synthetic JSONL events
        │
        ▼
  Grafana Alloy ──────► Grafana Loki ──────► Grafana dashboard
  tail + parse          indexed storage       LogQL analysis
        │                       ▲
        └── labels              └── automated pipeline verifier
```

| Component | Pinned version | Purpose |
| --- | --- | --- |
| Python generator | 3.13.7 | Produces deterministic normal, brute-force, and password-spray telemetry |
| Grafana Alloy | 1.19.2 | Tails JSONL, parses fields, adds bounded labels, and forwards events |
| Grafana Loki | 3.7.8 | Retains and queries logs using LogQL |
| Grafana | 13.2.2 | Provisions the Loki data source and seven-panel SOC dashboard |

## Security scenarios

- Normal successful SSH authentication
- Repeated failures against one account from one source (brute force)
- One source failing against multiple accounts (password spray)
- Five-failures-in-five-minutes detection threshold

All identities are fictional and every address comes from an RFC 5737 documentation range. No real credentials or authentication logs are required.

## Quick start

Prerequisites: Docker Desktop with Compose and Python 3.10+.

1. Create the ignored environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

   Replace the placeholder with a strong local Grafana password.

2. Start Loki, Alloy, and Grafana:

   ```powershell
   docker compose --env-file .env up -d loki alloy grafana
   ```

3. Generate mixed normal and brute-force events:

   ```powershell
   docker compose --env-file .env run --rm generator --mode mixed --count 12
   ```

4. Verify ingestion and the detection threshold:

   ```powershell
   python scripts\verify_pipeline.py
   ```

5. Open [Grafana on localhost](http://localhost:3001), sign in as `admin`, and open **Security Operations / SIEM Logging Pipeline**.

The Alloy component UI is available at [localhost:12345](http://localhost:12345), and Loki readiness is available at [localhost:3100/ready](http://localhost:3100/ready). Every published port binds only to `127.0.0.1`.

## Generate individual scenarios

```powershell
# Replace the log with routine activity
docker compose --env-file .env run --rm generator --mode normal --count 10

# Append a detectable brute-force sequence
docker compose --env-file .env run --rm generator --mode brute-force --count 7 --append

# Append a password-spray sequence
docker compose --env-file .env run --rm generator --mode password-spray --count 6 --append
```

The generator is a one-shot utility container. An `Exited (0)` result is expected.

## Dashboard and queries

The provisioned dashboard includes:

1. Total authentication events
2. Failed authentication count
3. Five-minute brute-force threshold
4. Authentication outcomes over time
5. Top failure source addresses
6. Normalized authentication events
7. Failed-authentication evidence

Example LogQL queries:

```logql
{job="authentication-lab"} | json
```

```logql
sum by (source_ip) (
  count_over_time({job="authentication-lab"} | json | outcome="failure" [5m])
) >= 5
```

`source_ip` and `username` remain parsed fields rather than Loki labels, avoiding unbounded label cardinality. Only bounded dimensions such as outcome, scenario, severity, host, and event type become labels.

## Validation

```powershell
python -m py_compile scripts\generator.py scripts\verify_pipeline.py tests\test_pipeline.py
python -W error -m unittest discover -s tests -v
$env:GRAFANA_ADMIN_PASSWORD = "validation-only"
docker compose config --quiet
```

GitHub Actions repeats these checks on Windows and Ubuntu with Python 3.10 and 3.13, validates the Compose model, and scans the repository for secrets. Every action is pinned to an immutable commit or container digest.

## Operations

```powershell
docker compose --env-file .env ps
docker compose --env-file .env logs --tail 100 alloy loki grafana
docker compose --env-file .env down
docker compose --env-file .env down --volumes  # also removes local lab data
```

## Project structure

```text
alloy/config.alloy                              Alloy collection pipeline
grafana/provisioning/dashboards/                Dashboard provisioning and JSON
grafana/provisioning/datasources/loki.yml       Loki data source
loki/config.yml                                 Single-node Loki configuration
scripts/generator.py                            Synthetic event generator
scripts/verify_pipeline.py                      End-to-end Loki assertion
tests/test_pipeline.py                          Unit and policy tests
docker-compose.yml                              Local service topology
Dockerfile                                      Non-root generator image
```

## Scope and limitations

This is an educational home lab, not a production SIEM. It deliberately omits TLS, centralized identity, multi-tenancy, high availability, backups, production alert routing, and formal evidence handling. Loki and Grafana are bound to localhost, but you must still use synthetic data and keep `.env` private. See [SECURITY.md](SECURITY.md).

## Portfolio talking points

- Built an end-to-end, four-component security logging pipeline with deterministic simulations.
- Normalized JSON telemetry in Alloy and controlled Loki label cardinality.
- Provisioned a reusable Grafana dashboard and expressed detections in LogQL.
- Added an automated verifier that proves logs reached Loki and crossed the brute-force threshold.
- Secured the repository with local-only ports, a non-root generator, secret scanning, pinned dependencies, tests, and CI.

## License

Released under the [MIT License](LICENSE).
