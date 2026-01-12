"""Integration tests for health check endpoints.

Tests:
- GET /health returns 200 with status "healthy"
- GET /health/ready returns 200 with database connected
"""

import pytest


class TestHealthEndpoint:
    """Tests for the basic health check endpoint."""

    def test_health_returns_200(self, client):
        """Test GET /health returns 200 status code."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        """Test GET /health returns status 'healthy' in response body."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_includes_version(self, client):
        """Test GET /health includes version in response."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)


class TestReadinessEndpoint:
    """Tests for the readiness probe endpoint."""

    def test_ready_returns_200_when_db_connected(self, client):
        """Test GET /health/ready returns 200 when database is connected."""
        response = client.get("/health/ready")
        assert response.status_code == 200

    def test_ready_returns_ready_status(self, client):
        """Test GET /health/ready returns status 'ready' in response body."""
        response = client.get("/health/ready")
        data = response.json()
        assert data["status"] == "ready"

    def test_ready_confirms_database_connected(self, client):
        """Test GET /health/ready confirms database is connected."""
        response = client.get("/health/ready")
        data = response.json()
        assert data["database"] == "connected"


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_200(self, client):
        """Test GET / returns 200 status code."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_api_info(self, client):
        """Test GET / returns API name, version, and environment."""
        response = client.get("/")
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "environment" in data
