from fastapi.testclient import TestClient

from awep.server import create_app


def test_healthz(tmp_path) -> None:
    client = TestClient(create_app(tmp_path / ".awep"))
    assert client.get("/healthz").json() == {"status": "ok"}


def test_fetch_writes_receipt_and_runs_lists_it(tmp_path, httpx_mock) -> None:
    httpx_mock.add_response(
        url="http://127.0.0.1/source",
        html="<title>Fixture</title><p>Example Domain is used for illustrative examples. "
        + "text " * 120
        + "</p>",
    )
    client = TestClient(create_app(tmp_path / ".awep"))
    response = client.post(
        "/v1/fetch?allow_private=true",
        json={
            "url": "http://127.0.0.1/source",
            "run_id": "run-api",
            "claim": "Example Domain is used for illustrative examples",
            "agent_id": "test",
            "tool_name": "api-test",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == "run-api"
    assert data["quality_status"] == "ok"
    assert data["receipt_hash"]

    runs = client.get("/v1/runs")
    assert runs.status_code == 200
    assert runs.json()["runs"] == [
        {
            "run_id": "run-api",
            "created_at": runs.json()["runs"][0]["created_at"],
            "updated_at": runs.json()["runs"][0]["updated_at"],
            "receipt_count": 1,
        }
    ]


def test_report_evidence_and_verify_endpoints(tmp_path, httpx_mock) -> None:
    httpx_mock.add_response(
        url="http://127.0.0.1/source",
        text="Example Domain is used for illustrative examples. " + "text " * 120,
        headers={"content-type": "text/plain"},
    )
    client = TestClient(create_app(tmp_path / ".awep"))
    client.post(
        "/v1/fetch?allow_private=true",
        json={"url": "http://127.0.0.1/source", "run_id": "run-api"},
    )

    report_post = client.post("/v1/runs/run-api/report")
    assert report_post.status_code == 200
    assert report_post.json()["ok"] is True

    report = client.get("/v1/runs/run-api/report.md")
    assert report.status_code == 200
    assert "# Agent Web Evidence Report" in report.text

    evidence = client.get("/v1/runs/run-api/evidence.json")
    assert evidence.status_code == 200
    assert evidence.json()["run_id"] == "run-api"
    assert evidence.json()["receipts"][0]["run_id"] == "run-api"

    verify = client.post("/v1/runs/run-api/verify")
    assert verify.status_code == 200
    assert verify.json()["ok"] is True
    assert verify.json()["checked_receipts"] == 1


def test_missing_run_returns_404(tmp_path) -> None:
    client = TestClient(create_app(tmp_path / ".awep"))
    assert client.get("/v1/runs/missing/report.md").status_code == 404
    assert client.get("/v1/runs/missing/evidence.json").status_code == 404
    assert client.post("/v1/runs/missing/report").status_code == 404
    assert client.post("/v1/runs/missing/verify").status_code == 404
