from pathlib import Path

import yaml


def test_docker_compose_observability_services():
    compose_path = Path("docker-compose.yml")
    assert compose_path.exists(), "docker-compose.yml missing"
    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))

    services = compose["services"]
    assert "otel-collector" in services
    assert "prometheus" in services
    assert "tempo" in services
    assert "grafana" in services

    # Ports
    assert "4317:4317" in services["otel-collector"]["ports"]
    assert "4318:4318" in services["otel-collector"]["ports"]
    assert "9090:9090" in services["prometheus"]["ports"]
    assert "3200:3200" in services["tempo"]["ports"]
    assert "3000:3000" in services["grafana"]["ports"]


def test_telemetry_verification_script_syntax():
    script_path = Path("scripts/test_telemetry_pipeline.sh")
    assert script_path.exists(), "test_telemetry_pipeline.sh missing"
    content = script_path.read_text(encoding="utf-8")

    assert "warden.trace_id" in content
    assert "warden.caller_role" in content
    assert "curl" in content
    assert "v1/traces" in content
    assert "v1/metrics" in content or "query" in content


def test_readme_documentation_completeness():
    readme_path = Path("README.md")
    assert readme_path.exists(), "README.md missing"
    text = readme_path.read_text(encoding="utf-8")

    assert "observability-stack" in text
    assert "OpenTelemetry Collector" in text
    assert "Prometheus" in text
    assert "Tempo" in text
    assert "Grafana" in text
    assert "docker compose up" in text
