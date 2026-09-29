import json
from pathlib import Path
import yaml


def test_grafana_datasources():
    path = Path("k8s/observability/grafana-datasources.yaml")
    assert path.exists(), "grafana-datasources.yaml missing"
    docs = list(yaml.safe_load_all(path.read_text()))
    cm = next(d for d in docs if d["kind"] == "ConfigMap")
    ds_config = yaml.safe_load(cm["data"]["datasources.yaml"])

    ds_map = {d["name"]: d for d in ds_config["datasources"]}
    assert "Prometheus" in ds_map
    assert "Tempo" in ds_map
    assert ds_map["Prometheus"]["url"] == "http://prometheus.warden-observability.svc.cluster.local:9090"
    assert ds_map["Tempo"]["url"] == "http://tempo.warden-observability.svc.cluster.local:3200"


def test_grafana_sla_overview_dashboard_json():
    json_path = Path("config/grafana/dashboards/warden-sla-overview.json")
    assert json_path.exists(), "warden-sla-overview.json missing"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    assert data["title"] == "Project Warden — Master SLA & Operational Overview"
    panel_titles = [p["title"] for p in data.get("panels", [])]

    assert any("p50/p95/p99 Query Latency" in t for t in panel_titles)
    assert any("Cache Hit Ratio" in t for t in panel_titles)
    assert any("Laya ModernBERT Inference" in t for t in panel_titles)
    assert any("Presidio PII Redactions" in t for t in panel_titles)


def test_grafana_deployment_and_service():
    dep_path = Path("k8s/observability/grafana-deployment.yaml")
    assert dep_path.exists(), "grafana-deployment.yaml missing"
    docs = list(yaml.safe_load_all(dep_path.read_text()))
    dep = next(d for d in docs if d["kind"] == "Deployment")
    svc = next(d for d in docs if d["kind"] == "Service")

    assert dep["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]["memory"] == "256Mi"
    assert svc["spec"]["ports"][0]["port"] == 3000


def test_grafana_dashboards_configmap():
    path = Path("k8s/observability/grafana-dashboards-configmap.yaml")
    assert path.exists(), "grafana-dashboards-configmap.yaml missing"
    docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    cm = next(d for d in docs if d["kind"] == "ConfigMap")
    assert cm["metadata"]["namespace"] == "warden-observability"
    assert "warden-sla-overview.json" in cm["data"]
    raw_json = cm["data"]["warden-sla-overview.json"]
    parsed = json.loads(raw_json)
    assert parsed["title"] == "Project Warden — Master SLA & Operational Overview"
