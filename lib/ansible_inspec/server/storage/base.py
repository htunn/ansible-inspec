"""
Abstract storage backend interface for ansible-inspec server.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from ..models import JobTemplate, Job, WorkflowTemplate, VCSCredential, User


class StorageBackend(ABC):
    """Abstract storage backend interface"""
    
    # Job Template methods
    @abstractmethod
    async def save_job_template(self, template: JobTemplate) -> None:
        """Save a job template"""
        pass
    
    @abstractmethod
    async def get_job_template(self, template_id: str) -> Optional[JobTemplate]:
        """Get a job template by ID"""
        pass
    
    @abstractmethod
    async def list_job_templates(self) -> List[JobTemplate]:
        """List all job templates"""
        pass
    
    @abstractmethod
    async def delete_job_template(self, template_id: str) -> bool:
        """Delete a job template"""
        pass
    
    # Job methods
    @abstractmethod
    async def save_job(self, job: Job) -> None:
        """Save a job"""
        pass
    
    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        pass
    
    @abstractmethod
    async def list_jobs(self) -> List[Job]:
        """List all jobs"""
        pass
    
    @abstractmethod
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        pass
    
    # Workflow Template methods
    @abstractmethod
    async def save_workflow_template(self, workflow: WorkflowTemplate) -> None:
        """Save a workflow template"""
        pass
    
    @abstractmethod
    async def get_workflow_template(self, workflow_id: str) -> Optional[WorkflowTemplate]:
        """Get a workflow template by ID"""
        pass
    
    @abstractmethod
    async def list_workflow_templates(self) -> List[WorkflowTemplate]:
        """List all workflow templates"""
        pass
    
    @abstractmethod
    async def delete_workflow_template(self, workflow_id: str) -> bool:
        """Delete a workflow template"""
        pass
    
    # VCS Credential methods
    @abstractmethod
    async def save_vcs_credential(self, credential: VCSCredential) -> None:
        """Save a VCS credential"""
        pass
    
    @abstractmethod
    async def get_vcs_credential(self, credential_id: str) -> Optional[VCSCredential]:
        """Get a VCS credential by ID"""
        pass
    
    @abstractmethod
    async def list_vcs_credentials(self) -> List[VCSCredential]:
        """List all VCS credentials"""
        pass
    
    @abstractmethod
    async def delete_vcs_credential(self, credential_id: str) -> bool:
        """Delete a VCS credential"""
        pass
    
    # User methods
    @abstractmethod
    async def save_user(self, user: User) -> None:
        """Save a user"""
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        pass
    
    @abstractmethod
    async def list_users(self) -> List[User]:
        """List all users"""
        pass
