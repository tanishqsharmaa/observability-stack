from pathlib import Path

import yaml


def test_prometheus_configmap():
    path = Path("k8s/observability/prometheus-config.yaml")
    assert path.exists(), "prometheus-config.yaml missing"
    docs = list(yaml.safe_load_all(path.read_text()))
    cm = next(d for d in docs if d["kind"] == "ConfigMap")
    assert cm["metadata"]["namespace"] == "warden-observability"
    config = yaml.safe_load(cm["data"]["prometheus.yml"])

    assert config["global"]["scrape_interval"] == "10s"
    jobs = {j["job_name"]: j for j in config["scrape_configs"]}
    assert "otel-collector" in jobs
    assert "warden-microservices" in jobs

    ms_job = jobs["warden-microservices"]
    k8s_sd = ms_job["kubernetes_sd_configs"][0]
    assert "warden-apps" in k8s_sd["namespaces"]["names"]


def test_prometheus_deployment_and_pvc():
    dep_path = Path("k8s/observability/prometheus-deployment.yaml")
    svc_path = Path("k8s/observability/prometheus-service.yaml")
    assert dep_path.exists() and svc_path.exists()

    docs = list(yaml.safe_load_all(dep_path.read_text()))
    dep = next(d for d in docs if d["kind"] in ("Deployment", "StatefulSet"))
    pvc = next(d for d in docs if d["kind"] == "PersistentVolumeClaim")

    assert dep["metadata"]["namespace"] == "warden-observability"
    assert pvc["spec"]["resources"]["requests"]["storage"] == "10Gi"

    container = dep["spec"]["template"]["spec"]["containers"][0]
    assert container["resources"]["limits"]["memory"] == "1024Mi"
    args = " ".join(container.get("args", []))
    assert "--storage.tsdb.retention.time=15d" in args

    svc = yaml.safe_load(svc_path.read_text())
    assert svc["spec"]["ports"][0]["port"] == 9090
