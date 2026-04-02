"""
Unit tests for health check endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from tradingagents_crypto.api.health import app
import tradingagents_crypto.api.health as health_module


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_returns_200(self, client):
        """Test /health returns 200 with expected fields."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_health_live_returns_200(self, client):
        """Test /health/live returns 200."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "live"
        assert "timestamp" in data

    @patch("tradingagents_crypto.api.health._do_health_check")
    def test_health_ready_returns_200(self, mock_check, client):
        """Test /health/ready returns 200 when all checks pass."""
        mock_check.return_value = {
            "redis": {"status": "ok", "latency_ms": 2},
            "hyperliquid": {"status": "ok", "latency_ms": 45},
            "llm": {"status": "ok", "latency_ms": 0},
        }
        health_module._cache.clear()
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "checks" in data
        assert "timestamp" in data
        assert "status" in data

    def test_health_structure(self, client):
        """Test /health response structure."""
        response = client.get("/health")
        data = response.json()

        assert set(data.keys()) == {"status", "timestamp", "version"}
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

    def test_health_live_structure(self, client):
        """Test /health/live response structure."""
        response = client.get("/health/live")
        data = response.json()

        assert set(data.keys()) == {"status", "timestamp"}
        assert data["status"] == "live"

    @patch("tradingagents_crypto.api.health._do_health_check")
    def test_health_ready_with_mock_checks(self, mock_check, client):
        """Test /health/ready with mocked check results."""
        mock_check.return_value = {
            "redis": {"status": "ok", "latency_ms": 2},
            "hyperliquid": {"status": "ok", "latency_ms": 45},
            "llm": {"status": "ok", "latency_ms": 0},
        }

        # Clear the cache to force re-check
        # Clear the module-level cache
        health_module._cache.clear()

        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["redis"]["status"] == "ok"

    @patch("tradingagents_crypto.api.health._do_health_check")
    def test_health_ready_degraded_on_error(self, mock_check, client):
        """Test /health/ready returns 503 degraded when a check fails."""
        mock_check.return_value = {
            "redis": {"status": "error", "message": "connection refused"},
            "hyperliquid": {"status": "ok", "latency_ms": 45},
            "llm": {"status": "ok", "latency_ms": 0},
        }

        # Clear the module-level cache
        health_module._cache.clear()

        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
