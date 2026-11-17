"""Simple integration test for alert API endpoint."""
import pytest
from fastapi.testclient import TestClient


def test_alert_endpoint_requires_auth(client: TestClient):
    """Test alert detail requires authentication."""
    response = client.get("/api/v1/alerts/1")
    assert response.status_code == 401


def test_alert_endpoint_404_for_missing(auth_client: TestClient):
    """Test alert detail returns 404 for non-existent alert."""
    response = auth_client.get("/api/v1/alerts/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
