"""
Unit tests for server models, storage, and business logic.
"""

import pytest
import tempfile
import os
import json
from datetime import datetime
from pathlib import Path

from ansible_inspec.server.models import (
    JobTemplate,
    Job,
    JobStatus,
    JobType,
    WorkflowTemplate
)
from ansible_inspec.server.storage import FileStorageBackend
from ansible_inspec.server.encryption import EncryptionService


class TestJobTemplate:
    """Test JobTemplate model."""

    def test_create_job_template(self):
        """Test creating a basic job template."""
        template = JobTemplate(
            id="test-123",
            name="linux-baseline",
            profile_path="dev-sec/linux-baseline",
            description="Test Linux compliance"
        )
        
        assert template.id == "test-123"
        assert template.name == "linux-baseline"
        assert template.profile_path == "dev-sec/linux-baseline"
        assert template.description == "Test Linux compliance"

    def test_job_template_to_dict(self):
        """Test converting job template to dictionary."""
        template = JobTemplate(
            id="test-123",
            name="test",
            profile_path="profile",
            extra_vars={"key": "value"}
        )
        
        template_dict = template.to_dict()
        assert isinstance(template_dict, dict)
        assert template_dict["id"] == "test-123"
        assert template_dict["name"] == "test"
        assert "extra_vars" in template_dict

    def test_job_template_with_inventory(self):
        """Test job template with inventory configuration."""
        template = JobTemplate(
            id="inv-123",
            name="inventory-profile",
            profile_path="my-profile",
            inventory="inventory.yml"
        )
        
        assert template.inventory == "inventory.yml"


class TestJob:
    """Test Job model."""

    def test_create_job(self):
        """Test creating a job instance."""
        job = Job(
            id="job-123",
            template_id="template-456",
            status=JobStatus.PENDING
        )
        
        assert job.id == "job-123"
        assert job.template_id == "template-456"
        assert job.status == JobStatus.PENDING

    def test_job_status_enum(self):
        """Test job status enumeration."""
        assert JobStatus.PENDING == "pending"
        assert JobStatus.RUNNING == "running"
        assert JobStatus.SUCCESSFUL == "successful"
        assert JobStatus.FAILED == "failed"

    def test_job_to_dict(self):
        """Test converting job to dictionary."""
        job = Job(
            id="job-123",
            template_id="template-456",
            status=JobStatus.RUNNING,
            result_summary={"passed": 5, "failed": 0}
        )
        
        job_dict = job.to_dict()
        assert isinstance(job_dict, dict)
        assert job_dict["id"] == "job-123"
        assert job_dict["status"] == "running"
        assert "result_summary" in job_dict


class TestWorkflowTemplate:
    """Test WorkflowTemplate model."""

    def test_create_workflow_template(self):
        """Test creating a workflow template."""
        workflow = WorkflowTemplate(
            id="workflow-123",
            name="compliance-workflow",
            description="Multi-step compliance check"
        )
        
        assert workflow.id == "workflow-123"
        assert workflow.name == "compliance-workflow"
        assert workflow.description == "Multi-step compliance check"


class TestStorage:
    """Test file-based storage backend."""

    def setup_method(self):
        """Setup temporary storage directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = FileStorageBackend(data_dir=self.temp_dir)

    def teardown_method(self):
        """Cleanup temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_storage_initialization(self):
        """Test storage initializes with correct directories."""
        assert Path(self.temp_dir).exists()
        assert Path(self.temp_dir, "job_templates").exists()
        assert Path(self.temp_dir, "jobs").exists()

    def test_save_and_get_job_template(self):
        """Test saving and retrieving a job template."""
        template = JobTemplate(
            id="test-123",
            name="test-template",
            profile_path="test-profile"
        )
        
        self.storage.save_job_template(template)
        retrieved = self.storage.get_job_template("test-123")
        
        assert retrieved is not None
        assert retrieved.id == template.id
        assert retrieved.name == template.name
        assert retrieved.profile_path == template.profile_path

    def test_list_job_templates(self):
        """Test listing all job templates."""
        template1 = JobTemplate(id="t1", name="template1", profile_path="profile1")
        template2 = JobTemplate(id="t2", name="template2", profile_path="profile2")
        
        self.storage.save_job_template(template1)
        self.storage.save_job_template(template2)
        
        templates = self.storage.list_job_templates()
        assert len(templates) == 2
        template_ids = [t.id for t in templates]
        assert "t1" in template_ids
        assert "t2" in template_ids

    def test_delete_job_template(self):
        """Test deleting a job template."""
        template = JobTemplate(id="delete-123", name="to-delete", profile_path="profile")
        
        self.storage.save_job_template(template)
        assert self.storage.get_job_template("delete-123") is not None
        
        result = self.storage.delete_job_template("delete-123")
        assert result is True
        assert self.storage.get_job_template("delete-123") is None

    def test_save_and_get_job(self):
        """Test saving and retrieving a job."""
        job = Job(
            id="job-123",
            template_id="template-456",
            status=JobStatus.PENDING
        )
        
        self.storage.save_job(job)
        retrieved = self.storage.get_job("job-123")
        
        assert retrieved is not None
        assert retrieved.id == job.id
        assert retrieved.template_id == job.template_id
        assert retrieved.status == job.status

    def test_list_jobs(self):
        """Test listing all jobs."""
        job1 = Job(id="j1", template_id="t1", status=JobStatus.PENDING)
        job2 = Job(id="j2", template_id="t1", status=JobStatus.RUNNING)
        
        self.storage.save_job(job1)
        self.storage.save_job(job2)
        
        jobs = self.storage.list_jobs()
        assert len(jobs) == 2

    def test_get_nonexistent_template(self):
        """Test getting a template that doesn't exist."""
        retrieved = self.storage.get_job_template("nonexistent")
        assert retrieved is None

    def test_delete_nonexistent_template(self):
        """Test deleting a template that doesn't exist."""
        result = self.storage.delete_job_template("nonexistent")
        assert result is False


class TestEncryption:
    """Test encryption service for sensitive data."""

    def test_encryption_initialization(self):
        """Test initializing encryption service with a key."""
        key = EncryptionService.generate_key()
        encryption = EncryptionService(key=key)
        assert encryption is not None

    def test_generate_key(self):
        """Test key generation."""
        key = EncryptionService.generate_key()
        assert isinstance(key, str)
        assert len(key) > 0

    def test_encrypt_decrypt(self):
        """Test encryption and decryption roundtrip."""
        key = EncryptionService.generate_key()
        encryption = EncryptionService(key=key)
        
        original_text = "my-secret-password-123"
        encrypted = encryption.encrypt(original_text)
        
        assert encrypted != original_text
        assert len(encrypted) > 0
        
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original_text

    def test_encrypt_empty_string(self):
        """Test encrypting an empty string."""
        key = EncryptionService.generate_key()
        encryption = EncryptionService(key=key)
        
        encrypted = encryption.encrypt("")
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == ""

    def test_encrypt_special_characters(self):
        """Test encrypting text with special characters."""
        key = EncryptionService.generate_key()
        encryption = EncryptionService(key=key)
        
        original = "p@ssw0rd!#$%^&*(){}[]|\\:;\"'<>,.?/~`"
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_unicode(self):
        """Test encrypting Unicode text."""
        key = EncryptionService.generate_key()
        encryption = EncryptionService(key=key)
        
        original = "密码🔐パスワード"
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original

    def test_different_keys_produce_different_ciphertext(self):
        """Test that different keys produce different encrypted results."""
        key1 = EncryptionService.generate_key()
        key2 = EncryptionService.generate_key()
        
        encryption1 = EncryptionService(key=key1)
        encryption2 = EncryptionService(key=key2)
        
        text = "secret-data"
        encrypted1 = encryption1.encrypt(text)
        encrypted2 = encryption2.encrypt(text)
        
        assert encrypted1 != encrypted2


class TestJobExecution:
    """Test job execution logic."""

    def test_job_lifecycle(self):
        """Test job status transitions."""
        job = Job(
            id="job-123",
            template_id="template-456",
            status=JobStatus.PENDING
        )
        
        assert job.status == JobStatus.PENDING
        
        job.status = JobStatus.RUNNING
        assert job.status == JobStatus.RUNNING
        
        job.status = JobStatus.SUCCESSFUL
        assert job.status == JobStatus.SUCCESSFUL


class TestWorkflow:
    """Test workflow functionality."""

    def test_workflow_template_creation(self):
        """Test creating workflow templates."""
        workflow = WorkflowTemplate(
            id="wf-123",
            name="compliance-suite",
            description="Complete compliance check workflow"
        )
        
        assert workflow.id == "wf-123"
        assert workflow.name == "compliance-suite"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
