import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from lc_server.main import create_app
    return TestClient(create_app())

@pytest.fixture(autouse=True)
def isolate_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".creator" / "loops").mkdir(parents=True)
    (tmp_path / ".creator" / "skills").mkdir(parents=True)
    (tmp_path / ".creator" / "prompts").mkdir(parents=True)
