"""
Unit tests for the /health endpoint.
"""

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
import sys
sys.path.insert(0, '..')
from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        """Test that /health returns HTTP 200 status code."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        """Test that /health returns status: healthy."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_contains_required_fields(self, client):
        """Test that /health response contains all required fields."""
        response = client.get("/health")
        data = response.json()
        
        required_fields = ["status", "timestamp", "service", "version"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_health_timestamp_format(self, client):
        """Test that timestamp is in ISO 8601 format."""
        response = client.get("/health")
        data = response.json()
        
        # Check timestamp contains expected ISO format components
        timestamp = data["timestamp"]
        assert "T" in timestamp, "Timestamp should be in ISO format"
        assert ":" in timestamp, "Timestamp should contain time"

    def test_health_service_name(self, client):
        """Test that service name is returned correctly."""
        response = client.get("/health")
        data = response.json()
        
        assert "service" in data
        assert isinstance(data["service"], str)
        assert len(data["service"]) > 0

    def test_health_version_format(self, client):
        """Test that version is in expected format."""
        response = client.get("/health")
        data = response.json()
        
        assert "version" in data
        assert data["version"] == "1.0.0"
