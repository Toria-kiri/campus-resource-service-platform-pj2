"""Exercise the M3 health endpoint through the real ASGI application."""

from fastapi.testclient import TestClient

from backend.modules.m3.main import app


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"status": "ok"}


def test_health_rejects_post() -> None:
    with TestClient(app) as client:
        response = client.post("/health")

    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}
    assert "GET" in response.headers["allow"]


def test_unknown_route_returns_not_found() -> None:
    with TestClient(app) as client:
        response = client.get("/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
