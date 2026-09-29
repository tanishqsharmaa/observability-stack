from pathlib import Path
import yaml


def test_tempo_configmap():
    path = Path("k8s/observability/tempo-config.yaml")
    assert path.exists(), "tempo-config.yaml missing"
    docs = list(yaml.safe_load_all(path.read_text()))
    cm = next(d for d in docs if d["kind"] == "ConfigMap")
    assert cm["metadata"]["namespace"] == "warden-observability"
    config = yaml.safe_load(cm["data"]["tempo.yaml"])

    assert config["distributor"]["receivers"]["otlp"]["protocols"]["grpc"]["endpoint"] == "0.0.0.0:4317"
    assert config["storage"]["trace"]["backend"] == "local"
    assert config["compactor"]["compaction"]["block_retention"] == "48h"


def test_tempo_deployment_and_service():
    dep_path = Path("k8s/observability/tempo-deployment.yaml")
    svc_path = Path("k8s/observability/tempo-service.yaml")
    assert dep_path.exists(), "tempo-deployment.yaml missing"
    assert svc_path.exists(), "tempo-service.yaml missing"

    docs = list(yaml.safe_load_all(dep_path.read_text()))
    dep = next(d for d in docs if d["kind"] == "Deployment")
    pvc = next(d for d in docs if d["kind"] == "PersistentVolumeClaim")

    assert pvc["spec"]["resources"]["requests"]["storage"] == "10Gi"
    container = dep["spec"]["template"]["spec"]["containers"][0]
    assert container["resources"]["limits"]["memory"] == "1024Mi"

    svc = yaml.safe_load(svc_path.read_text())
    ports = {p["name"]: p["port"] for p in svc["spec"]["ports"]}
    assert ports["tempo-query"] == 3200
    assert ports["otlp-grpc"] == 4317
