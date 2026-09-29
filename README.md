# Project Warden: Observability Control Plane (`observability-stack`)

Autonomous Enterprise Single Source of Truth (SSOT) — Observability & Telemetry Control Plane (Tier 7).

---

## 1. Overview & Architectural Role

`observability-stack` is the Tier 7 self-hosted telemetry control plane for **Project Warden**. Designed natively for Azure Kubernetes Service (AKS) and local container testbeds, it provides complete, end-to-end distributed observability across all Warden runtime microservices. It ingests OpenTelemetry (OTel) traces and metrics over OTLP gRPC (Port 4317) and HTTP (Port 4318), stores distributed traces in Grafana Tempo, aggregates time-series metrics in Prometheus, and renders operational service-level dashboards in Grafana.

Crucially, `observability-stack` guarantees a **$0.00 cloud telemetry bill** by completely bypassing managed cloud observability offerings (Azure Monitor, Log Analytics workspaces, Datadog), protecting the project's strict **$150.00 USD Azure budget ceiling**.

### Core Architectural Invariants:

1. **Zero-Cloud-Cost Telemetry Isolation**:
   - 100% self-hosted on cluster worker nodes using open-source engines (`otel-collector-contrib`, `prometheus`, `tempo`, `grafana`).
   - Zero per-gigabyte log ingestion or metric ingestion fees.
2. **Namespace Isolation & Zero-Trust Placement**:
   - Deployed strictly into the dedicated Kubernetes namespace `warden-observability`.
   - Ingests telemetry via internal cluster networking without exposing control ports to external ingress.
3. **Collector Memory Ceiling & Backpressure**:
   - OTel Collector enforces a strict `memory_limiter` processor (`limit_percentage: 75`, `spike_limit_percentage: 20`) with a 256MB RSS ceiling, preventing node memory exhaustion during burst queries.
4. **Persistent Storage & Retention Floors**:
   - Prometheus: Backed by a 10Gi Azure Managed Disk PVC with 15-day time-series retention (`--storage.tsdb.retention.time=15d`).
   - Tempo: Backed by a 10Gi Azure Managed Disk PVC with 48-hour block retention (`compactor.compaction.block_retention: 48h`).
5. **Mandatory W3C Distributed Tracing Attributes**:
   - All microservices propagate W3C Trace Context headers (`traceparent`, `tracestate`).
   - Every span emitted records 7 mandatory enterprise attributes:
     - `warden.trace_id`: Global correlation UUID.
     - `warden.caller_role`: Caller security tier (`Employee` | `Manager` | `HR-Admin`).
     - `warden.query_hash`: SHA-256 hash of normalized query text.
     - `warden.chunks_retrieved_count`: Raw candidates pulled from Qdrant.
     - `warden.chunks_reranked_count`: Candidates post-Laya reranking.
     - `warden.reranker_fallback_active`: Boolean flag if circuit breaker tripped.
     - `warden.llm_time_to_first_token_ms`: Milliseconds to first generation token.

---

## 2. Directory Structure

```
observability-stack/
├── pyproject.toml                                  # Package definition & pytest configuration
├── README.md                                       # Subsystem documentation & runbooks
├── docker-compose.yml                              # Standalone local testbed for $0.00 dev
├── config/
│   ├── otel-collector/
│   │   └── config.yaml                             # Standalone OTel collector pipeline config
│   ├── prometheus/
│   │   └── prometheus.yml                          # Standalone Prometheus scrape configuration
│   ├── tempo/
│   │   └── tempo.yaml                              # Standalone Grafana Tempo storage config
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/datasources.yaml        # Automated datasource provisioning
│       │   └── dashboards/dashboards.yaml          # Automated dashboard provider
│       └── dashboards/
│           └── warden-sla-overview.json            # Master SLA Dashboard model
├── k8s/
│   └── observability/
│       ├── otel-collector-config.yaml              # OTel Collector ConfigMap
│       ├── otel-collector-deployment.yaml          # OTel Collector Deployment (256MB limit)
│       ├── otel-collector-service.yaml             # OTel Collector Service (4317, 4318, 8889)
│       ├── prometheus-config.yaml                  # Prometheus ConfigMap (10s scrape intervals)
│       ├── prometheus-deployment.yaml              # Prometheus Deployment & 10Gi PVC
│       ├── prometheus-service.yaml                 # Prometheus Service (9090)
│       ├── tempo-config.yaml                       # Grafana Tempo ConfigMap
│       ├── tempo-deployment.yaml                   # Grafana Tempo Deployment & 10Gi PVC
│       ├── tempo-service.yaml                      # Grafana Tempo Service (3200, 4317)
│       ├── grafana-datasources.yaml                # Grafana Datasources ConfigMap
│       ├── grafana-dashboards-configmap.yaml       # Embedded Dashboard JSON ConfigMap
│       └── grafana-deployment.yaml                 # Grafana Deployment & Service (3000)
├── scripts/
│   └── test_telemetry_pipeline.sh                  # Synthetic span and metric verification probe
└── tests/
    ├── conftest.py                                 # Shared test fixtures & sample trace payload
    ├── test_otel_collector_manifests.py            # Unit tests: OTel Collector manifests
    ├── test_prometheus_manifests.py                # Unit tests: Prometheus scrape configs & PVC
    ├── test_tempo_manifests.py                     # Unit tests: Tempo trace storage & ports
    ├── test_grafana_manifests.py                   # Unit tests: Datasources & Dashboard JSON
    └── test_telemetry_pipeline.py                  # Integration tests: Compose & test scripts
```

---

## 3. Subsystem Architecture & Port Map

| Component | Inbound Protocol | Port | Inbound Source | Outbound Destination |
|---|---|---|---|---|
| **OTel Collector** | OTLP gRPC | `4317` | Runtime Microservices | Tempo (`tempo:4317`) |
| **OTel Collector** | OTLP HTTP | `4318` | Runtime Microservices / HTTP | Prometheus Exporter (`:8889`) |
| **OTel Collector** | HTTP Metrics | `8889` | Prometheus Scraper | Internal Pipeline Exporter |
| **Prometheus** | HTTP Web/API | `9090` | Grafana / Operators | Local TSDB Storage (15d) |
| **Grafana Tempo** | OTLP gRPC | `4317` | OTel Collector Exporter | Local Block Storage (48h) |
| **Grafana Tempo** | HTTP Query | `3200` | Grafana Datasource | Trace Query Engine |
| **Grafana UI** | HTTP UI | `3000` | Web Browser / SRE Operators | Prometheus & Tempo APIs |

---

## 4. Quickstart: Local Standalone Testbed ($0.00 Spend)

```bash
# 1. Start all observability services locally via Docker Compose
docker compose up -d

# 2. Verify all 4 containers are healthy
docker compose ps

# 3. Access Web Dashboards
# Grafana UI:    http://localhost:3000 (Anonymous viewer or admin:warden-admin-2026)
# Prometheus UI: http://localhost:9090
# Tempo Query:   http://localhost:3200

# 4. Execute end-to-end synthetic telemetry test probe
bash scripts/test_telemetry_pipeline.sh http://localhost:4318 http://localhost:9090

# 5. Teardown testbed and clean volumes
docker compose down -v
```

---

## 5. Kubernetes Production Deployment Runbook

Deploy the complete observability control plane into AKS:

```bash
# 1. Create dedicated namespace if not present
kubectl create namespace warden-observability --dry-run=client -o yaml | kubectl apply -f -

# 2. Deploy OpenTelemetry Collector
kubectl apply -f k8s/observability/otel-collector-config.yaml
kubectl apply -f k8s/observability/otel-collector-deployment.yaml
kubectl apply -f k8s/observability/otel-collector-service.yaml

# 3. Deploy Prometheus Storage & Scraper
kubectl apply -f k8s/observability/prometheus-config.yaml
kubectl apply -f k8s/observability/prometheus-deployment.yaml
kubectl apply -f k8s/observability/prometheus-service.yaml

# 4. Deploy Grafana Tempo Distributed Tracing
kubectl apply -f k8s/observability/tempo-config.yaml
kubectl apply -f k8s/observability/tempo-deployment.yaml
kubectl apply -f k8s/observability/tempo-service.yaml

# 5. Deploy Grafana & Automated SLA Dashboard
kubectl apply -f k8s/observability/grafana-datasources.yaml
kubectl apply -f k8s/observability/grafana-dashboards-configmap.yaml
kubectl apply -f k8s/observability/grafana-deployment.yaml

# 6. Verify cluster pod readiness
kubectl get pods -n warden-observability
```

---

## 6. Automated Contract Test Suite

All manifests, configurations, Docker Compose definitions, and JSON models are mechanically tested via `pytest`:

```bash
# Activate virtual environment
.venv\Scripts\activate   # On Windows
# source .venv/bin/activate  # On Linux

# Run complete test suite (14 tests)
pytest tests/ -v
```

### Verified Test Matrix:

| Test Module | Tests | Verified Invariants |
|---|---|---|
| `test_otel_collector_manifests.py` | 2 | OTLP gRPC 4317, HTTP 4318, memory limiter 75%, batch size 256, 256Mi memory limit |
| `test_prometheus_manifests.py` | 2 | 10s scrape interval, warden-apps discovery, 10Gi PVC, 15d retention flag |
| `test_tempo_manifests.py` | 2 | OTLP gRPC ingestion, local storage backend, 48h block retention, 10Gi PVC |
| `test_grafana_manifests.py` | 4 | Prometheus & Tempo datasources, SLA overview dashboard JSON, ConfigMap embed |
| `test_telemetry_pipeline.py` | 3 | Docker compose topology, synthetic verification script syntax, README completeness |
| **Total** | **13** | **100% Passing (0 failures, 0 skipped)** |
