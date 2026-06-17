from fastapi.testclient import TestClient

from awep.server import create_app


def test_healthz(tmp_path) -> None:
    client = TestClient(create_app(tmp_path / ".awep"))
    assert client.get("/healthz").json() == {"status": "ok"}
