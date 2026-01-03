"""
Unit tests for the /error endpoint.
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


class TestErrorEndpoint:
    """Tests for the /error endpoint."""

    def test_error_returns_500(self, client):
        """Test that /error returns HTTP 500 status code."""
        response = client.get("/error")
        assert response.status_code == 500

    def test_error_contains_error_field(self, client):
        """Test that /error response contains error field."""
        response = client.get("/error")
        data = response.json()
        
        assert "error" in data
        assert isinstance(data["error"], str)
        assert len(data["error"]) > 0

    def test_error_contains_message(self, client):
        """Test that /error response contains message field."""
        response = client.get("/error")
        data = response.json()
        
        assert "message" in data
        assert "intentional" in data["message"].lower()

    def test_error_contains_request_id(self, client):
        """Test that /error response contains request_id."""
        response = client.get("/error")
        data = response.json()
        
        assert "request_id" in data

    def test_error_contains_timestamp(self, client):
        """Test that /error response contains timestamp."""
        response = client.get("/error")
        data = response.json()
        
        assert "timestamp" in data
        # Check ISO format
        assert "T" in data["timestamp"]

    def test_error_request_id_header(self, client):
        """Test that response includes X-Request-ID header."""
        response = client.get("/error")
        assert "X-Request-ID" in response.headers

    def test_error_is_json_response(self, client):
        """Test that /error returns JSON content type."""
        response = client.get("/error")
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type
