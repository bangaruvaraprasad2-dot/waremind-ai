"""
Integration tests for Flask API Routes & Page Endpoints.
Run: python -m pytest tests/test_api_routes.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_landing_page_route(client):
    """GET / should return 200 OK."""
    res = client.get("/")
    assert res.status_code == 200


def test_dashboard_page_route(client):
    """GET /dashboard should return 200 OK."""
    res = client.get("/dashboard")
    assert res.status_code == 200


def test_api_dashboard_endpoint(client):
    """GET /api/dashboard should return 200 OK with valid KPI data structure."""
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.get_json()
    assert "kpis" in data


def test_api_inventory_endpoint(client):
    """GET /api/inventory should return 200 OK with inventory items."""
    res = client.get("/api/inventory")
    assert res.status_code == 200
    data = res.get_json()
    assert "items" in data
    assert "summary" in data


def test_api_orders_endpoint(client):
    """GET /api/orders should return 200 OK with orders list."""
    res = client.get("/api/orders")
    assert res.status_code == 200
    data = res.get_json()
    assert "orders" in data


def test_api_exceptions_endpoint(client):
    """GET /api/exceptions should return 200 OK with exceptions summary."""
    res = client.get("/api/exceptions")
    assert res.status_code == 200
    data = res.get_json()
    assert "exceptions" in data


def test_api_analytics_endpoint(client):
    """GET /api/analytics should return 200 OK with operational analytics metrics."""
    res = client.get("/api/analytics")
    assert res.status_code == 200
    data = res.get_json()
    assert "summary" in data or "fulfillment_rate" in data or "bottleneck" in data


def test_api_copilot_endpoint(client):
    """POST /api/copilot should process query and return response object."""
    res = client.post("/api/copilot", json={"message": "What products need replenishment?"})
    assert res.status_code == 200
    data = res.get_json()
    assert "message" in data
    assert "type" in data


def test_api_crisis_simulation(client):
    """POST /api/simulation/crisis should generate crisis scenario object."""
    res = client.post("/api/simulation/crisis", json={})
    assert res.status_code == 200
    data = res.get_json()
    assert "decision" in data or "scenario" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
