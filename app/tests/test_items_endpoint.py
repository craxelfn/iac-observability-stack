"""
Unit tests for the /items endpoint.
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


class TestItemsEndpoint:
    """Tests for the /items endpoint."""

    def test_items_returns_200(self, client):
        """Test that /items returns HTTP 200 status code."""
        response = client.get("/items")
        assert response.status_code == 200

    def test_items_default_count(self, client):
        """Test that /items returns 10 items by default."""
        response = client.get("/items")
        data = response.json()
        
        assert "items" in data
        assert "count" in data
        assert data["count"] == 10
        assert len(data["items"]) == 10

    def test_items_custom_count(self, client):
        """Test that /items respects the count parameter."""
        response = client.get("/items?count=5")
        data = response.json()
        
        assert data["count"] == 5
        assert len(data["items"]) == 5

    def test_items_count_validation_min(self, client):
        """Test that count parameter has minimum validation."""
        response = client.get("/items?count=0")
        assert response.status_code == 422  # Validation error

    def test_items_count_validation_max(self, client):
        """Test that count parameter has maximum validation."""
        response = client.get("/items?count=101")
        assert response.status_code == 422  # Validation error

    def test_items_structure(self, client):
        """Test that each item has the expected structure."""
        response = client.get("/items?count=1")
        data = response.json()
        
        assert len(data["items"]) > 0
        item = data["items"][0]
        
        required_fields = ["id", "name", "description", "price", "category", "in_stock", "created_at"]
        for field in required_fields:
            assert field in item, f"Missing required field: {field}"

    def test_items_id_is_uuid(self, client):
        """Test that item ID is a valid UUID format."""
        response = client.get("/items?count=1")
        data = response.json()
        
        item = data["items"][0]
        item_id = item["id"]
        
        # UUID should have 36 characters with 4 dashes
        assert len(item_id) == 36
        assert item_id.count("-") == 4

    def test_items_price_is_numeric(self, client):
        """Test that item price is a number."""
        response = client.get("/items?count=1")
        data = response.json()
        
        item = data["items"][0]
        assert isinstance(item["price"], (int, float))
        assert item["price"] > 0

    def test_items_category_values(self, client):
        """Test that categories are from expected set."""
        response = client.get("/items?count=20")
        data = response.json()
        
        valid_categories = ["electronics", "clothing", "books", "food"]
        for item in data["items"]:
            assert item["category"] in valid_categories

    def test_items_in_stock_boolean(self, client):
        """Test that in_stock is a boolean."""
        response = client.get("/items?count=1")
        data = response.json()
        
        item = data["items"][0]
        assert isinstance(item["in_stock"], bool)

    def test_items_request_id_header(self, client):
        """Test that response includes X-Request-ID header."""
        response = client.get("/items")
        assert "X-Request-ID" in response.headers

    def test_items_response_contains_request_id(self, client):
        """Test that response body contains request_id."""
        response = client.get("/items")
        data = response.json()
        
        assert "request_id" in data
