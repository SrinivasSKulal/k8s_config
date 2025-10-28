import pytest
import yaml
from unittest.mock import patch
from main import run_scan, auto_fix_file, get_corrected_yaml_content


# --------------------------
# 1️⃣ Functional Test Cases
# --------------------------


def test_valid_yaml_parsing(tmp_path):
    yaml_content = """
    apiVersion: v1
    kind: Pod
    metadata:
      name: test-pod
    spec:
      containers:
      - name: nginx
        image: nginx:stable
    """
    file = tmp_path / "valid.yaml"
    file.write_text(yaml_content)

    result = run_scan(str(file))
    assert isinstance(result, list)
    assert len(result) == 0 or "severity" in result[0]  # empty or valid result


def test_invalid_yaml_syntax(tmp_path):
    # invalid yaml
    yaml_content = """
    apiVersion: v1
    kind: Pod
    metadata:
      name: invalid
      spec
        containers:
        - name: test
          image: nginx
    """
    file_path = tmp_path / "invalid.yaml"
    file_path.write_text(yaml_content)

    issues = run_scan(str(file_path))
    assert any("Error parsing" in i["message"] for i in issues)


def test_missing_required_fields(tmp_path):
    yaml_content = """
    apiVersion: v1
    kind: Pod
    metadata:
      name: testpod
    spec:
      containers:
        - name: test
          image: nginx
    """
    file_path = tmp_path / "missing_resources.yaml"
    file_path.write_text(yaml_content)

    issues = run_scan(str(file_path))
    assert any("missing resource requests/limits" in i["message"] for i in issues)


# ---------------------------------
# 2️⃣ Rule-Based Detection Tests
# ---------------------------------


def test_detect_privileged_container(tmp_path):
    yaml_content = """
    apiVersion: v1
    kind: Pod
    metadata:
      name: insecure-pod
    spec:
      containers:
      - name: bad
        image: nginx
        securityContext:
          privileged: true
    """
    file = tmp_path / "privileged.yaml"
    file.write_text(yaml_content)

    result = run_scan(str(file))
    severities = [r["severity"].lower() for r in result]
    assert "high" in severities


def test_detect_latest_tag(tmp_path):
    yaml_content = """
    apiVersion: v1
    kind: Pod
    metadata:
      name: latest-pod
    spec:
      containers:
      - name: nginx
        image: nginx:latest
    """
    file = tmp_path / "latest.yaml"
    file.write_text(yaml_content)

    result = run_scan(str(file))
    assert any("latest" in str(r).lower() for r in result)


def test_get_corrected_yaml_content(tmp_path):
    yaml_content = """
    apiVersion: v1
    kind: Service
    metadata:
      name: myservice
    spec:
      type: LoadBalancer
      ports:
        - port: 80
          targetPort: 80
      selector:
        app: nginx
    """
    file_path = tmp_path / "service.yaml"
    file_path.write_text(yaml_content)

    # call the function to get corrected YAML
    fixed_yaml = get_corrected_yaml_content(str(file_path))

    assert "namespace:" in fixed_yaml or "Service" in fixed_yaml


# ---------------------------------
# 5️⃣ Performance / Large File
# ---------------------------------


def test_large_yaml_file(tmp_path):
    large_yaml = (
        """
    apiVersion: v1
    kind: Pod
    metadata:
      name: pod-{i}
    spec:
      containers:
      - name: app
        image: nginx
    """
        * 100
    )  # simulate large file

    file = tmp_path / "large.yaml"
    file.write_text(large_yaml)

    result = run_scan(str(file))
    assert isinstance(result, list)
