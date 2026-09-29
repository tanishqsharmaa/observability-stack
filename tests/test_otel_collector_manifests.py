from pathlib import Path

import yaml


def test_otel_collector_configmap():
    path = Path("k8s/observability/otel-collector-config.yaml")
    assert path.exists(), "otel-collector-config.yaml missing"
    docs = list(yaml.safe_load_all(path.read_text()))
    cm = next(d for d in docs if d["kind"] == "ConfigMap")
    assert cm["metadata"]["namespace"] == "warden-observability"
    config = yaml.safe_load(cm["data"]["otel-collector-config.yaml"])

    # Receivers
    assert "otlp" in config["receivers"]
    assert config["receivers"]["otlp"]["protocols"]["grpc"]["endpoint"] == "0.0.0.0:4317"
    assert config["receivers"]["otlp"]["protocols"]["http"]["endpoint"] == "0.0.0.0:4318"

    # Processors
    assert "memory_limiter" in config["processors"]
    mem = config["processors"]["memory_limiter"]
    assert mem["limit_percentage"] == 75
    assert mem["spike_limit_percentage"] == 20
    assert config["processors"]["batch"]["send_batch_size"] == 256

    # Exporters
    assert config["exporters"]["prometheus"]["endpoint"] == "0.0.0.0:8889"
    assert "tempo.warden-observability.svc.cluster.local:4317" in config["exporters"]["otlp/tempo"]["endpoint"]

    # Pipelines
    assert "traces" in config["service"]["pipelines"]
    assert "metrics" in config["service"]["pipelines"]


def test_otel_collector_deployment_and_service():
    dep_path = Path("k8s/observability/otel-collector-deployment.yaml")
    svc_path = Path("k8s/observability/otel-collector-service.yaml")
    assert dep_path.exists(), "otel-collector-deployment.yaml missing"
    assert svc_path.exists(), "otel-collector-service.yaml missing"

    dep = yaml.safe_load(dep_path.read_text())
    assert dep["metadata"]["namespace"] == "warden-observability"
    container = dep["spec"]["template"]["spec"]["containers"][0]
    assert container["resources"]["limits"]["memory"] == "256Mi"
    assert container["resources"]["requests"]["cpu"] == "100m"

    svc = yaml.safe_load(svc_path.read_text())
    ports = {p["name"]: p["port"] for p in svc["spec"]["ports"]}
    assert ports["otlp-grpc"] == 4317
    assert ports["otlp-http"] == 4318
    assert ports["metrics"] == 8889
