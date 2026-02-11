"""
Unit tests for the ansible-inspec server API.

Tests the FastAPI endpoints, authentication, and business logic.
"""

import pytest
import os
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

# Set test environment variables before importing the app
os.environ['DATABASE_URL'] = 'file:./test.db'
os.environ['JWT_SECRET'] = 'test-secret-key-for-testing-only-1234567890'
os.environ['AUTH_ENABLED'] = 'false'
os.environ['VCS_ENABLED'] = 'false'

from ansible_inspec.server.api import app
from ansible_inspec.server.models import JobTemplate, Job


class TestHealthCheck:
    """Test health check endpoints."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_root_redirect(self):
        """Test that root redirects to /docs."""
        response = self.client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"

    def test_health_endpoint(self):
        """Test health check endpoint returns proper status."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        assert "storage_backend" in data


class TestAPIInfo:
    """Test API info endpoint."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_api_info(self):
        """Test API info endpoint returns correct information."""
        response = self.client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert data["name"] == "ansible-inspec"


class TestJobTemplateEndpoints:
    """Test job template CRUD endpoints."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    @pytest.mark.asyncio
    async def test_list_job_templates_empty(self):
        """Test listing job templates when none exist."""
        with patch('ansible_inspec.server.api.get_db') as mock_db:
            mock_prisma = AsyncMock()
            mock_prisma.jobtemplate.find_many = AsyncMock(return_value=[])
            
            async def mock_get_db():
                yield mock_prisma
            
            mock_db.return_value = mock_get_db()
            
            response = self.client.get("/api/v1/job-templates")
            assert response.status_code == 200
            assert response.json() == []

    def test_create_job_template_minimal(self):
        """Test creating a job template with minimal data."""
        template_data = {
            "name": "test-template",
            "profile": "dev-sec/linux-baseline",
            "description": "Test template"
        }
        
        with patch('ansible_inspec.server.api.get_db') as mock_db:
            mock_prisma = AsyncMock()
            mock_created = Mock()
            mock_created.id = "test-id-123"
            mock_created.name = template_data["name"]
            mock_created.profile = template_data["profile"]
            mock_created.description = template_data["description"]
            mock_created.extraVars = {}
            mock_created.createdAt = "2026-02-03T00:00:00Z"
            mock_created.updatedAt = "2026-02-03T00:00:00Z"
            
            mock_prisma.jobtemplate.create = AsyncMock(return_value=mock_created)
            
            async def mock_get_db_gen():
                yield mock_prisma
            
            mock_db.return_value = mock_get_db_gen()
            
            response = self.client.post("/api/v1/job-templates", json=template_data)
            assert response.status_code == 201

    def test_create_job_template_with_vcs(self):
        """Test creating a job template with VCS integration."""
        template_data = {
            "name": "vcs-template",
            "profile": "my-profile",
            "vcs_repo_id": "repo-123",
            "vcs_path": "profiles/my-profile",
            "vcs_sync": True,
            "description": "VCS-backed template"
        }
        
        with patch('ansible_inspec.server.api.get_db') as mock_db:
            mock_prisma = AsyncMock()
            mock_created = Mock()
            mock_created.id = "vcs-template-id"
            mock_created.name = template_data["name"]
            
            mock_prisma.jobtemplate.create = AsyncMock(return_value=mock_created)
            
            async def mock_get_db_gen():
                yield mock_prisma
            
            mock_db.return_value = mock_get_db_gen()
            
            response = self.client.post("/api/v1/job-templates", json=template_data)
            assert response.status_code == 201


class TestJobEndpoints:
    """Test job execution endpoints."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_list_jobs(self):
        """Test listing jobs."""
        with patch('ansible_inspec.server.api.get_db') as mock_db:
            mock_prisma = AsyncMock()
            mock_prisma.job.find_many = AsyncMock(return_value=[])
            
            async def mock_get_db_gen():
                yield mock_prisma
            
            mock_db.return_value = mock_get_db_gen()
            
            response = self.client.get("/api/v1/jobs")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_create_job(self):
        """Test creating a job from a template."""
        job_data = {
            "template_id": "template-123",
            "extra_vars": {"target": "localhost"}
        }
        
        with patch('ansible_inspec.server.api.get_db') as mock_db:
            mock_prisma = AsyncMock()
            
            # Mock template lookup
            mock_template = Mock()
            mock_template.id = "template-123"
            mock_template.profile = "test-profile"
            mock_prisma.jobtemplate.find_unique = AsyncMock(return_value=mock_template)
            
            # Mock job creation
            mock_job = Mock()
            mock_job.id = "job-123"
            mock_job.status = "pending"
            mock_prisma.job.create = AsyncMock(return_value=mock_job)
            
            async def mock_get_db_gen():
                yield mock_prisma
            
            mock_db.return_value = mock_get_db_gen()
            
            with patch('ansible_inspec.server.api.storage') as mock_storage:
                response = self.client.post("/api/v1/jobs", json=job_data)
                assert response.status_code == 201


class TestVCSEndpoints:
    """Test VCS credential and repository endpoints."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_list_vcs_credentials(self):
        """Test listing VCS credentials."""
        with patch('ansible_inspec.server.api.get_db') as mock_db:
            mock_prisma = AsyncMock()
            mock_prisma.vcscredential.find_many = AsyncMock(return_value=[])
            
            async def mock_get_db_gen():
                yield mock_prisma
            
            mock_db.return_value = mock_get_db_gen()
            
            response = self.client.get("/api/v1/vcs/credentials")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_create_vcs_credential(self):
        """Test creating VCS credentials."""
        cred_data = {
            "name": "github-creds",
            "vcs_type": "github",
            "token": "test-token-123"
        }
        
        with patch('ansible_inspec.server.api.get_db') as mock_db, \
             patch('ansible_inspec.server.api.encryption') as mock_encryption:
            
            mock_encryption.encrypt = Mock(return_value="encrypted-token")
            
            mock_prisma = AsyncMock()
            mock_created = Mock()
            mock_created.id = "cred-123"
            mock_created.name = cred_data["name"]
            mock_created.vcsType = cred_data["vcs_type"]
            
            mock_prisma.vcscredential.create = AsyncMock(return_value=mock_created)
            
            async def mock_get_db_gen():
                yield mock_prisma
            
            mock_db.return_value = mock_get_db_gen()
            
            response = self.client.post("/api/v1/vcs/credentials", json=cred_data)
            assert response.status_code == 201

    def test_list_vcs_repositories(self):
        """Test listing VCS repositories."""
        with patch('ansible_inspec.server.api.get_db') as mock_db:
            mock_prisma = AsyncMock()
            mock_prisma.vcsrepository.find_many = AsyncMock(return_value=[])
            
            async def mock_get_db_gen():
                yield mock_prisma
            
            mock_db.return_value = mock_get_db_gen()
            
            response = self.client.get("/api/v1/vcs/repositories")
            assert response.status_code == 200
            assert isinstance(response.json(), list)


class TestAuthentication:
    """Test authentication endpoints and middleware."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_login_endpoint_exists(self):
        """Test that login endpoint exists."""
        response = self.client.get("/auth/login", follow_redirects=False)
        # With auth disabled, might redirect or return specific message
        assert response.status_code in [200, 307, 401]

    def test_logout_endpoint(self):
        """Test logout endpoint."""
        response = self.client.post("/auth/logout")
        assert response.status_code in [200, 401]


class TestMetrics:
    """Test Prometheus metrics endpoint."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_metrics_endpoint(self):
        """Test that metrics endpoint returns Prometheus format."""
        response = self.client.get("/metrics")
        assert response.status_code == 200
        # Prometheus metrics should be plain text
        assert "text/plain" in response.headers.get("content-type", "")


class TestErrorHandling:
    """Test error handling and validation."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_invalid_json(self):
        """Test handling of invalid JSON input."""
        response = self.client.post(
            "/api/v1/job-templates",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_fields(self):
        """Test validation of required fields."""
        template_data = {
            "name": "test"
            # Missing required 'profile' field
        }
        response = self.client.post("/api/v1/job-templates", json=template_data)
        assert response.status_code == 422

    def test_nonexistent_endpoint(self):
        """Test 404 for nonexistent endpoints."""
        response = self.client.get("/api/v1/nonexistent")
        assert response.status_code == 404


class TestCORS:
    """Test CORS middleware configuration."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_cors_headers(self):
        """Test that CORS headers are set correctly."""
        response = self.client.options(
            "/api/v1/job-templates",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        assert "access-control-allow-origin" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
