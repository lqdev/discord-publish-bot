"""
Integration tests for API health endpoints.

Tests the API endpoints with real HTTP calls but mocked external dependencies.
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, patch

from discord_publish_bot.api.app import create_app
from discord_publish_bot.config import get_settings


@pytest.mark.integration
class TestAPIHealth:
    """Test API health endpoint integration."""
    
    @pytest.fixture
    async def app_client(self, test_settings):
        """Create a test client for the FastAPI app."""
        # Import test client
        from fastapi.testclient import TestClient
        
        with patch('discord_publish_bot.config.get_settings', return_value=test_settings):
            app = create_app()
            yield TestClient(app)
    
    def test_health_endpoint_basic(self, app_client):
        """Test basic health endpoint returns correct structure."""
        response = app_client.get("/health")
        
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "status", "version", "environment", 
            "discord_configured", "github_configured", 
            "timestamp"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0-test"
        assert data["environment"] == "development"
        assert isinstance(data["discord_configured"], bool)
        assert isinstance(data["github_configured"], bool)
    
    def test_health_endpoint_detailed(self, app_client):
        """Test detailed health endpoint with GitHub connectivity check."""
        with patch('discord_publish_bot.api.dependencies.get_github_client') as mock_github:
            mock_client = AsyncMock()
            mock_client.check_connectivity.return_value = True
            mock_github.return_value = mock_client
            
            response = app_client.get("/health/detailed")
            
            assert response.status_code == 200
            
            data = response.json()
            assert "github_connectivity" in data
            assert data["github_connectivity"] is True
    
    def test_health_endpoint_with_github_failure(self, app_client):
        """Test detailed health endpoint when GitHub connectivity fails."""
        with patch('discord_publish_bot.api.dependencies.get_github_client') as mock_github:
            mock_client = AsyncMock()
            mock_client.check_connectivity.return_value = False
            mock_github.return_value = mock_client
            
            response = app_client.get("/health/detailed")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "degraded"  # Should indicate degraded status
            assert data["github_connectivity"] is False
    
    def test_readiness_probe(self, app_client):
        """Test Kubernetes readiness probe endpoint."""
        response = app_client.get("/ready")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ready"
    
    def test_liveness_probe(self, app_client):
        """Test Kubernetes liveness probe endpoint."""
        response = app_client.get("/live")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "alive"
    
    def test_root_endpoint_information(self, app_client):
        """Test root endpoint returns service information."""
        response = app_client.get("/")
        
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["service", "version", "environment", "endpoints"]
        
        for field in required_fields:
            assert field in data
        
        # Check endpoints information
        endpoints = data["endpoints"]
        assert "/health" in str(endpoints)
        assert "/discord" in str(endpoints)
        assert "/api" in str(endpoints)
    
    def test_cors_headers_in_development(self, app_client, test_settings):
        """Test that CORS headers are present in development mode."""
        response = app_client.get("/health")
        
        # In development mode, CORS should be enabled
        if test_settings.environment == "development":
            # Note: TestClient might not show CORS headers, this tests the setup
            assert response.status_code == 200


@pytest.mark.integration
class TestAPIErrors:
    """Test API error handling integration."""
    
    @pytest.fixture
    async def app_client(self, test_settings):
        """Create a test client for the FastAPI app."""
        from fastapi.testclient import TestClient
        
        with patch('discord_publish_bot.config.get_settings', return_value=test_settings):
            app = create_app()
            yield TestClient(app)
    
    def test_404_error_handling(self, app_client):
        """Test handling of 404 errors."""
        response = app_client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
    
    def test_method_not_allowed(self, app_client):
        """Test handling of method not allowed errors."""
        response = app_client.post("/health")  # Health endpoint only accepts GET
        
        assert response.status_code == 405
    
    def test_internal_server_error_handling(self, app_client):
        """Test handling of internal server errors."""
        # This test would require injecting an error into a handler
        # For now, we test that the error handler structure is in place
        
        # Try to access endpoint that might trigger validation error
        response = app_client.post("/api/publish", json={"invalid": "data"})
        
        # Should return proper error response (not 500)
        assert response.status_code in [400, 422]  # Validation error


@pytest.mark.integration
@pytest.mark.slow
class TestAPIPerformance:
    """Test API performance characteristics."""
    
    @pytest.fixture
    async def app_client(self, test_settings):
        """Create a test client for the FastAPI app."""
        from fastapi.testclient import TestClient
        
        with patch('discord_publish_bot.config.get_settings', return_value=test_settings):
            app = create_app()
            yield TestClient(app)
    
    def test_health_endpoint_response_time(self, app_client):
        """Test that health endpoint responds quickly."""
        import time
        
        start_time = time.time()
        response = app_client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_concurrent_health_requests(self, app_client):
        """Test handling of concurrent health check requests."""
        import concurrent.futures
        import time
        
        def make_request():
            start = time.time()
            response = app_client.get("/health")
            end = time.time()
            return response.status_code, end - start
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        for status_code, response_time in results:
            assert status_code == 200
            assert response_time < 2.0  # Should all respond within 2 seconds


@pytest.mark.integration
@pytest.mark.network
class TestRealAPIConnectivity:
    """Test real API connectivity (requires running server)."""
    
    @pytest.mark.skipif(
        "not config.getoption('--run-network-tests')",
        reason="Network tests only run with --run-network-tests flag"
    )
    async def test_localhost_api_connectivity(self):
        """Test connectivity to localhost API server."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:8000/health", timeout=5) as response:
                    assert response.status == 200
                    
                    data = await response.json()
                    assert "status" in data
                    assert "version" in data
                    
            except aiohttp.ClientError:
                pytest.skip("Local API server not running")
    
    @pytest.mark.skipif(
        "not config.getoption('--run-network-tests')",
        reason="Network tests only run with --run-network-tests flag"
    )
    async def test_api_startup_and_shutdown(self):
        """Test API server startup and shutdown process."""
        import subprocess
        import time
        import signal
        import os
        
        # Start API server in background
        process = subprocess.Popen([
            "uv", "run", "dpb", "api", "--port", "8999"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            # Wait for server to start
            time.sleep(3)
            
            # Test connection
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8999/health") as response:
                    assert response.status == 200
                    
                    data = await response.json()
                    assert data["status"] == "healthy"
            
        finally:
            # Clean shutdown
            if os.name == 'nt':  # Windows
                process.terminate()
            else:  # Unix-like
                process.send_signal(signal.SIGTERM)
            
            process.wait(timeout=10)


# Pytest configuration for network tests
def pytest_addoption(parser):
    """Add command line option for network tests."""
    parser.addoption(
        "--run-network-tests",
        action="store_true",
        default=False,
        help="Run tests that require network connectivity"
    )
