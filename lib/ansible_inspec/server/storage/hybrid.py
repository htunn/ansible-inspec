"""
Hybrid storage backend combining file and database storage.

This module implements a hybrid storage approach where data is written to both
file and database backends simultaneously, with validation to ensure consistency.
Used for migration from file storage to database storage with a validation period.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ansible_inspec.server.storage.base import StorageBackend
from ansible_inspec.server.storage.file_backend import FileStorageBackend
from ansible_inspec.server.storage.prisma_backend import PrismaStorageBackend
from ansible_inspec.server.models import (
    JobTemplate,
    Job,
    WorkflowTemplate,
    User,
    VCSCredential,
)
from ansible_inspec.server.monitoring import record_consistency_error, update_validation_days_remaining

logger = logging.getLogger(__name__)


@dataclass
class ValidationMetrics:
    """Metrics for hybrid storage validation."""
    
    total_reads: int = 0
    total_writes: int = 0
    consistency_errors: int = 0
    file_errors: int = 0
    db_errors: int = 0
    last_validation: Optional[datetime] = None
    validation_start: datetime = datetime.now()
    validation_days: int = 30  # Default validation period


class HybridStorage(StorageBackend):
    """
    Hybrid storage backend for safe migration from file to database.
    
    Writes go to both backends (dual-write).
    Reads come from database with validation against file storage.
    Tracks consistency metrics for cutover decision.
    """

    def __init__(
        self,
        file_backend: FileStorageBackend,
        db_backend: PrismaStorageBackend,
        validation_days: int = 30,
    ):
        """
        Initialize hybrid storage backend.
        
        Args:
            file_backend: File storage backend
            db_backend: Database storage backend
            validation_days: Number of days to validate before cutover
        """
        self.file_backend = file_backend
        self.db_backend = db_backend
        self.metrics = ValidationMetrics(validation_days=validation_days)
        logger.info(f"Initialized hybrid storage with {validation_days}-day validation period")

    def _compare_templates(self, file_obj: Optional[JobTemplate], db_obj: Optional[JobTemplate]) -> bool:
        """
        Compare job templates from file and database.
        
        Args:
            file_obj: JobTemplate from file storage
            db_obj: JobTemplate from database storage
            
        Returns:
            True if consistent, False otherwise
        """
        if file_obj is None and db_obj is None:
            return True
        if file_obj is None or db_obj is None:
            return False
        
        # Compare key fields (ignore timestamps as they may differ slightly)
        return (
            file_obj.name == db_obj.name and
            file_obj.description == db_obj.description and
            file_obj.profile == db_obj.profile and
            file_obj.extra_vars == db_obj.extra_vars
        )

    def _compare_jobs(self, file_obj: Optional[Job], db_obj: Optional[Job]) -> bool:
        """
        Compare jobs from file and database.
        
        Args:
            file_obj: Job from file storage
            db_obj: Job from database storage
            
        Returns:
            True if consistent, False otherwise
        """
        if file_obj is None and db_obj is None:
            return True
        if file_obj is None or db_obj is None:
            return False
        
        return (
            file_obj.template_id == db_obj.template_id and
            file_obj.template_name == db_obj.template_name and
            file_obj.status == db_obj.status and
            file_obj.target == db_obj.target and
            file_obj.exit_code == db_obj.exit_code
        )

    def _record_consistency_check(self, consistent: bool, resource_type: str):
        """Record consistency check result."""
        self.metrics.total_reads += 1
        self.metrics.last_validation = datetime.now()
        
        if not consistent:
            self.metrics.consistency_errors += 1
            record_consistency_error(backend="hybrid", resource_type=resource_type)
            logger.warning(f"Consistency error detected in {resource_type}")

    def get_validation_status(self) -> dict:
        """
        Get validation status and metrics.
        
        Returns:
            Dict with validation metrics and cutover readiness
        """
        elapsed = datetime.now() - self.metrics.validation_start
        days_elapsed = elapsed.days
        days_remaining = max(0, self.metrics.validation_days - days_elapsed)
        
        # Update Prometheus metric
        update_validation_days_remaining(days_remaining)
        
        # Calculate error rate
        error_rate = (
            self.metrics.consistency_errors / self.metrics.total_reads
            if self.metrics.total_reads > 0
            else 0
        )
        
        # Cutover criteria:
        # 1. Validation period completed (30 days)
        # 2. Consistency error rate < 0.1% (1 error per 1000 reads)
        # 3. At least 1000 reads performed
        # 4. Both backends operational
        cutover_ready = (
            days_remaining == 0 and
            error_rate < 0.001 and
            self.metrics.total_reads >= 1000 and
            self.metrics.file_errors < 10 and
            self.metrics.db_errors < 10
        )
        
        return {
            "validation_start": self.metrics.validation_start.isoformat(),
            "validation_days": self.metrics.validation_days,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "total_reads": self.metrics.total_reads,
            "total_writes": self.metrics.total_writes,
            "consistency_errors": self.metrics.consistency_errors,
            "file_errors": self.metrics.file_errors,
            "db_errors": self.metrics.db_errors,
            "error_rate": error_rate,
            "cutover_ready": cutover_ready,
            "last_validation": self.metrics.last_validation.isoformat() if self.metrics.last_validation else None,
        }

    # ==================== Job Template Operations ====================

    async def save_job_template(self, template: JobTemplate) -> None:
        """Save job template to both backends."""
        self.metrics.total_writes += 1
        
        # Write to both backends
        try:
            await self.file_backend.save_job_template(template)
        except Exception as e:
            self.metrics.file_errors += 1
            logger.error(f"File backend write error: {e}")
        
        try:
            await self.db_backend.save_job_template(template)
        except Exception as e:
            self.metrics.db_errors += 1
            logger.error(f"Database backend write error: {e}")

    async def get_job_template(self, template_id: str) -> Optional[JobTemplate]:
        """Get job template from database and validate against file storage."""
        # Read from both backends
        file_template = await self.file_backend.get_job_template(template_id)
        db_template = await self.db_backend.get_job_template(template_id)
        
        # Validate consistency
        consistent = self._compare_templates(file_template, db_template)
        self._record_consistency_check(consistent, "job_template")
        
        # Return database result (primary)
        return db_template

    async def list_job_templates(self) -> List[JobTemplate]:
        """List job templates from database."""
        return await self.db_backend.list_job_templates()

    async def delete_job_template(self, template_id: str) -> bool:
        """Delete job template from both backends."""
        file_result = await self.file_backend.delete_job_template(template_id)
        db_result = await self.db_backend.delete_job_template(template_id)
        return db_result

    # ==================== Job Operations ====================

    async def save_job(self, job: Job) -> None:
        """Save job to both backends."""
        self.metrics.total_writes += 1
        
        try:
            await self.file_backend.save_job(job)
        except Exception as e:
            self.metrics.file_errors += 1
            logger.error(f"File backend write error: {e}")
        
        try:
            await self.db_backend.save_job(job)
        except Exception as e:
            self.metrics.db_errors += 1
            logger.error(f"Database backend write error: {e}")

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job from database and validate against file storage."""
        file_job = await self.file_backend.get_job(job_id)
        db_job = await self.db_backend.get_job(job_id)
        
        consistent = self._compare_jobs(file_job, db_job)
        self._record_consistency_check(consistent, "job")
        
        return db_job

    async def list_jobs(self) -> List[Job]:
        """List jobs from database."""
        return await self.db_backend.list_jobs()

    async def delete_job(self, job_id: str) -> bool:
        """Delete job from both backends."""
        await self.file_backend.delete_job(job_id)
        return await self.db_backend.delete_job(job_id)

    # ==================== Workflow Template Operations ====================

    async def save_workflow_template(self, workflow: WorkflowTemplate) -> None:
        """Save workflow template to both backends."""
        self.metrics.total_writes += 1
        
        try:
            await self.file_backend.save_workflow_template(workflow)
        except Exception as e:
            self.metrics.file_errors += 1
            logger.error(f"File backend write error: {e}")
        
        try:
            await self.db_backend.save_workflow_template(workflow)
        except Exception as e:
            self.metrics.db_errors += 1
            logger.error(f"Database backend write error: {e}")

    async def get_workflow_template(self, workflow_id: str) -> Optional[WorkflowTemplate]:
        """Get workflow template from database."""
        return await self.db_backend.get_workflow_template(workflow_id)

    async def list_workflow_templates(self) -> List[WorkflowTemplate]:
        """List workflow templates from database."""
        return await self.db_backend.list_workflow_templates()

    async def delete_workflow_template(self, workflow_id: str) -> bool:
        """Delete workflow template from both backends."""
        await self.file_backend.delete_workflow_template(workflow_id)
        return await self.db_backend.delete_workflow_template(workflow_id)

    # ==================== VCS Credential Operations ====================

    async def save_vcs_credential(self, credential: VCSCredential) -> None:
        """Save VCS credential to both backends."""
        self.metrics.total_writes += 1
        
        try:
            await self.file_backend.save_vcs_credential(credential)
        except Exception as e:
            self.metrics.file_errors += 1
            logger.error(f"File backend write error: {e}")
        
        try:
            await self.db_backend.save_vcs_credential(credential)
        except Exception as e:
            self.metrics.db_errors += 1
            logger.error(f"Database backend write error: {e}")

    async def get_vcs_credential(self, credential_id: str) -> Optional[VCSCredential]:
        """Get VCS credential from database."""
        return await self.db_backend.get_vcs_credential(credential_id)

    async def list_vcs_credentials(self) -> List[VCSCredential]:
        """List VCS credentials from database."""
        return await self.db_backend.list_vcs_credentials()

    async def delete_vcs_credential(self, credential_id: str) -> bool:
        """Delete VCS credential from both backends."""
        await self.file_backend.delete_vcs_credential(credential_id)
        return await self.db_backend.delete_vcs_credential(credential_id)

    # ==================== User Operations ====================

    async def save_user(self, user: User) -> None:
        """Save user to both backends."""
        self.metrics.total_writes += 1
        
        try:
            await self.file_backend.save_user(user)
        except Exception as e:
            self.metrics.file_errors += 1
            logger.error(f"File backend write error: {e}")
        
        try:
            await self.db_backend.save_user(user)
        except Exception as e:
            self.metrics.db_errors += 1
            logger.error(f"Database backend write error: {e}")

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user from database."""
        return await self.db_backend.get_user(user_id)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username from database."""
        return await self.db_backend.get_user_by_username(username)

    async def list_users(self) -> List[User]:
        """List users from database."""
        return await self.db_backend.list_users()
