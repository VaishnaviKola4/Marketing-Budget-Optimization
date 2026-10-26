"""
Integration tests for FastAPI endpoints using TestClient.
"""

from fastapi.testclient import TestClient
from marketing_budget_optimizer.api.app import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_channels_endpoint():
    response = client.get("/api/v1/channels")
    assert response.status_code == 200
    channels = response.json()
    assert isinstance(channels, list)
    assert len(channels) > 0


def test_optimize_endpoint():
    payload = {
        "budget_scaling_factor": 1.0,
        "objective": "maximize_revenue",
        "max_channel_shift_pct": 0.35
    }
    response = client.post("/api/v1/optimize", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "total_current_spend" in res
    assert "total_recommended_spend" in res
    assert "channel_allocations" in res


def test_predict_endpoint():
    payload = {
        "Google_Search": 3000.0,
        "Meta_Ads": 2500.0,
        "Email_Marketing": 500.0
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "total_predicted_revenue" in res
    assert res["total_predicted_revenue"] > 0


def test_inefficiencies_endpoint():
    response = client.get("/api/v1/inefficiencies")
    assert response.status_code == 200
    flags = response.json()
    assert isinstance(flags, list)

