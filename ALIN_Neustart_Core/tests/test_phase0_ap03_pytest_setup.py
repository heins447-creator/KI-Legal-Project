import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pytest_is_configured_in_pyproject():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pytest_config = pyproject["tool"]["pytest"]["ini_options"]
    assert pytest_config["testpaths"] == ["tests"]
    assert "--strict-config" in pytest_config["addopts"]
    assert "--strict-markers" in pytest_config["addopts"]


def test_tests_readme_documents_no_real_client_data():
    text = (ROOT / "tests" / "README.md").read_text(encoding="utf-8")
    assert "Keine echten Mandantendaten" in text
    assert "Keine Internetverbindungen" in text
