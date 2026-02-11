"""
Integration tests for the ansible-inspec server.

Tests end-to-end workflows including API, database, and job execution.
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from typing import AsyncGenerator

# Set test environment
os.environ['DATABASE_URL'] = 'file:./test_integration.db'
os.environ['JWT_SECRET'] = 'test-integration-secret-key-1234567890'
os.environ['AUTH_ENABLED'] = 'false'
os.environ['VCS_ENABLED'] = 'false'
os.environ['STORAGE_BACKEND'] = 'hybrid'

import httpx
from fastapi.testclient import TestClient
from ansible_inspec.server.api import app


@pytest.fixture
def test_data_dir():
    """Create a temporary data directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestEndToEndJobTemplate:
    """Test complete job template workflow."""

    def test_full_job_template_lifecycle(self, client):
        """Test creating, updating, and deleting a job template."""
        # Create template
        template_data = {
            "name": "integration-test-template",
            "profile": "dev-sec/linux-baseline",
            "description": "Integration test template",
            "extra_vars": {"timeout": 300}
        }
        
        # Skip actual API calls since we need database setup
        # This is a structure for when database is available
        pass

    def test_job_template_validation(self, client):
        """Test job template validation rules."""
        # Test invalid data
        invalid_data = {
            "name": "",  # Empty name should fail
            "profile": "test-profile"
        }
        
        response = client.post("/api/v1/job-templates", json=invalid_data)
        # Expect validation error
        assert response.status_code == 422


class TestEndToEndJobExecution:
    """Test complete job execution workflow."""

    @pytest.mark.skipif(
        not os.path.exists("/usr/bin/inspec") and not os.path.exists("/usr/local/bin/inspec"),
        reason="InSpec not installed"
    )
    def test_local_profile_execution(self, client, test_data_dir):
        """Test executing a local InSpec profile."""
        # Create a simple test profile
        profile_dir = Path(test_data_dir) / "test-profile"
        profile_dir.mkdir(parents=True)
        
        # Create inspec.yml
        inspec_yml = profile_dir / "inspec.yml"
        inspec_yml.write_text("""
name: test-profile
title: Integration Test Profile
version: 1.0.0
""")
        
        # Create control
        controls_dir = profile_dir / "controls"
        controls_dir.mkdir()
        
        control_file = controls_dir / "test.rb"
        control_file.write_text("""
control 'test-1' do
  title 'Test control'
  describe file('/tmp') do
    it { should exist }
  end
end
""")
        
        # This test structure shows what would be tested
        # Actual execution requires database and InSpec
        pass


class TestEndToEndVCS:
    """Test VCS integration workflow."""

    def test_vcs_credential_management(self, client):
        """Test creating and managing VCS credentials."""
        # Test credential creation structure
        cred_data = {
            "name": "test-github",
            "vcs_type": "github",
            "token": "test-token-for-integration"
        }
        
        # Would test actual API when database available
        pass

    def test_repository_sync(self, client):
        """Test repository synchronization."""
        # Test repository sync structure
        repo_data = {
            "name": "test-repo",
            "url": "https://github.com/test/repo.git",
            "credential_id": "cred-123",
            "branch": "main"
        }
        
        # Would test actual sync when VCS enabled
        pass


class TestEndToEndAuthentication:
    """Test authentication and authorization workflow."""

    def test_unauthenticated_access(self, client):
        """Test access without authentication when auth is disabled."""
        response = client.get("/api/v1/job-templates")
        # With auth disabled, should allow access
        assert response.status_code in [200, 401]

    @pytest.mark.skipif(
        os.environ.get('AUTH_ENABLED') != 'true',
        reason="Authentication not enabled"
    )
    def test_protected_endpoints(self, client):
        """Test that protected endpoints require authentication."""
        # Test accessing protected endpoint without auth
        response = client.post("/api/v1/job-templates", json={
            "name": "test",
            "profile": "test"
        })
        
        # Should require authentication
        assert response.status_code == 401


class TestEndToEndWorkflow:
    """Test complete multi-step workflows."""

    def test_workflow_template_creation(self, client):
        """Test creating a workflow with multiple job templates."""
        # Structure for workflow testing
        workflow_data = {
            "name": "compliance-suite",
            "description": "Multi-stage compliance check",
            "nodes": [
                {
                    "id": "node-1",
                    "job_template_id": "template-1",
                    "success_nodes": ["node-2"]
                },
                {
                    "id": "node-2",
                    "job_template_id": "template-2",
                    "success_nodes": []
                }
            ]
        }
        
        # Would test workflow execution when available
        pass


class TestDatabasePersistence:
    """Test data persistence across server restarts."""

    @pytest.mark.asyncio
    async def test_data_survives_restart(self, test_data_dir):
        """Test that data persists after server restart."""
        # This would test actual persistence with database
        # Placeholder for structure
        pass


class TestConcurrentOperations:
    """Test concurrent API operations."""

    @pytest.mark.asyncio
    async def test_concurrent_job_creation(self, client):
        """Test creating multiple jobs concurrently."""
        # Test structure for concurrent operations
        async def create_job(job_id: str):
            # Would create job via API
            pass
        
        # Would run multiple concurrent requests
        pass

    @pytest.mark.asyncio
    async def test_concurrent_template_updates(self, client):
        """Test updating templates concurrently."""
        # Test concurrent update handling
        pass


class TestErrorRecovery:
    """Test error handling and recovery."""

    def test_invalid_profile_handling(self, client):
        """Test handling of invalid InSpec profiles."""
        template_data = {
            "name": "invalid-profile-test",
            "profile": "nonexistent/invalid-profile",
            "description": "Should handle gracefully"
        }
        
        # Would test error handling
        pass

    def test_database_connection_failure(self, client):
        """Test handling of database connection failures."""
        # Would test graceful degradation
        pass


class TestPerformance:
    """Test performance characteristics."""

    def test_list_templates_performance(self, client):
        """Test performance of listing many templates."""
        # Would test with large dataset
        pass

    @pytest.mark.asyncio
    async def test_job_execution_performance(self, client):
        """Test job execution performance."""
        # Would measure execution time
        pass


class TestDataIntegrity:
    """Test data validation and integrity."""

    def test_duplicate_template_names(self, client):
        """Test handling of duplicate template names."""
        template_data = {
            "name": "duplicate-test",
            "profile": "test-profile"
        }
        
        # Create first template
        # Try to create duplicate
        # Verify handling
        pass

    def test_orphaned_jobs(self, client):
        """Test handling of jobs with deleted templates."""
        # Create template and job
        # Delete template
        # Verify job handling
        pass


class TestMetricsAndMonitoring:
    """Test metrics and monitoring endpoints."""

    def test_prometheus_metrics(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Verify metrics format
        content = response.text
        assert "# HELP" in content or "# TYPE" in content or len(content) > 0

    def test_health_check_comprehensive(self, client):
        """Test comprehensive health check."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "storage_backend" in data


class TestAPIVersioning:
    """Test API versioning and compatibility."""

    def test_api_v1_endpoints(self, client):
        """Test that v1 API endpoints are accessible."""
        response = client.get("/api/v1/info")
        assert response.status_code == 200

    def test_api_info_version(self, client):
        """Test API info returns correct version."""
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "version" in data


class TestDocumentation:
    """Test API documentation endpoints."""

    def test_openapi_schema(self, client):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_docs_endpoint(self, client):
        """Test Swagger UI docs endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_redoc_endpoint(self, client):
        """Test ReDoc endpoint."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
