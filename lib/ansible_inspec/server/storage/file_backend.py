"""
File-based storage backend (existing implementation).
"""
import json
import aiofiles
from pathlib import Path
from typing import List, Optional
import logging

from .base import StorageBackend
from ..models import JobTemplate, Job, WorkflowTemplate, VCSCredential, User

logger = logging.getLogger(__name__)


class FileStorageBackend(StorageBackend):
    """File-based storage backend"""
    
    def __init__(self, data_dir: str = "./data"):
        """
        Initialize file storage
        
        Args:
            data_dir: Directory to store data files
        """
        self.data_dir = Path(data_dir)
        self.templates_dir = self.data_dir / "job_templates"
        self.jobs_dir = self.data_dir / "jobs"
        self.workflows_dir = self.data_dir / "workflow_templates"
        self.credentials_dir = self.data_dir / "vcs_credentials"
        self.users_dir = self.data_dir / "users"
        
        # Create directories
        for directory in [self.templates_dir, self.jobs_dir, self.workflows_dir,
                         self.credentials_dir, self.users_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"File storage initialized: {self.data_dir}")
    
    # Job Template methods
    async def save_job_template(self, template: JobTemplate) -> None:
        """Save a job template"""
        file_path = self.templates_dir / f"{template.id}.json"
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(template.to_dict(), indent=2))
    
    async def get_job_template(self, template_id: str) -> Optional[JobTemplate]:
        """Get a job template by ID"""
        file_path = self.templates_dir / f"{template_id}.json"
        if not file_path.exists():
            return None
        async with aiofiles.open(file_path, 'r') as f:
            data = json.loads(await f.read())
        return JobTemplate.from_dict(data)
    
    async def list_job_templates(self) -> List[JobTemplate]:
        """List all job templates"""
        templates = []
        for file_path in self.templates_dir.glob("*.json"):
            async with aiofiles.open(file_path, 'r') as f:
                data = json.loads(await f.read())
            templates.append(JobTemplate.from_dict(data))
        return sorted(templates, key=lambda t: t.created_at, reverse=True)
    
    async def delete_job_template(self, template_id: str) -> bool:
        """Delete a job template"""
        file_path = self.templates_dir / f"{template_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    # Job methods
    async def save_job(self, job: Job) -> None:
        """Save a job"""
        file_path = self.jobs_dir / f"{job.id}.json"
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(job.to_dict(), indent=2))
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        file_path = self.jobs_dir / f"{job_id}.json"
        if not file_path.exists():
            return None
        async with aiofiles.open(file_path, 'r') as f:
            data = json.loads(await f.read())
        return Job.from_dict(data)
    
    async def list_jobs(self) -> List[Job]:
        """List all jobs"""
        jobs = []
        for file_path in self.jobs_dir.glob("*.json"):
            try:
                async with aiofiles.open(file_path, 'r') as f:
                    data = json.loads(await f.read())
                jobs.append(Job.from_dict(data))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Skipping invalid job file {file_path}: {e}")
                continue
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        file_path = self.jobs_dir / f"{job_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    # Workflow Template methods
    async def save_workflow_template(self, workflow: WorkflowTemplate) -> None:
        """Save a workflow template"""
        file_path = self.workflows_dir / f"{workflow.id}.json"
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(workflow.to_dict(), indent=2))
    
    async def get_workflow_template(self, workflow_id: str) -> Optional[WorkflowTemplate]:
        """Get a workflow template by ID"""
        file_path = self.workflows_dir / f"{workflow_id}.json"
        if not file_path.exists():
            return None
        async with aiofiles.open(file_path, 'r') as f:
            data = json.loads(await f.read())
        return WorkflowTemplate.from_dict(data)
    
    async def list_workflow_templates(self) -> List[WorkflowTemplate]:
        """List all workflow templates"""
        workflows = []
        for file_path in self.workflows_dir.glob("*.json"):
            async with aiofiles.open(file_path, 'r') as f:
                data = json.loads(await f.read())
            workflows.append(WorkflowTemplate.from_dict(data))
        return sorted(workflows, key=lambda w: w.created_at, reverse=True)
    
    async def delete_workflow_template(self, workflow_id: str) -> bool:
        """Delete a workflow template"""
        file_path = self.workflows_dir / f"{workflow_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    # VCS Credential methods
    async def save_vcs_credential(self, credential: VCSCredential) -> None:
        """Save a VCS credential"""
        file_path = self.credentials_dir / f"{credential.id}.json"
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(credential.to_dict(), indent=2))
    
    async def get_vcs_credential(self, credential_id: str) -> Optional[VCSCredential]:
        """Get a VCS credential by ID"""
        file_path = self.credentials_dir / f"{credential_id}.json"
        if not file_path.exists():
            return None
        async with aiofiles.open(file_path, 'r') as f:
            data = json.loads(await f.read())
        return VCSCredential.from_dict(data)
    
    async def list_vcs_credentials(self) -> List[VCSCredential]:
        """List all VCS credentials"""
        credentials = []
        for file_path in self.credentials_dir.glob("*.json"):
            async with aiofiles.open(file_path, 'r') as f:
                data = json.loads(await f.read())
            credentials.append(VCSCredential.from_dict(data))
        return sorted(credentials, key=lambda c: c.created_at, reverse=True)
    
    async def delete_vcs_credential(self, credential_id: str) -> bool:
        """Delete a VCS credential"""
        file_path = self.credentials_dir / f"{credential_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    # User methods
    async def save_user(self, user: User) -> None:
        """Save a user"""
        file_path = self.users_dir / f"{user.id}.json"
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(user.to_dict(), indent=2))
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        file_path = self.users_dir / f"{user_id}.json"
        if not file_path.exists():
            return None
        async with aiofiles.open(file_path, 'r') as f:
            data = json.loads(await f.read())
        return User.from_dict(data)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        users = await self.list_users()
        for user in users:
            if user.username == username:
                return user
        return None
    
    async def list_users(self) -> List[User]:
        """List all users"""
        users = []
        for file_path in self.users_dir.glob("*.json"):
            async with aiofiles.open(file_path, 'r') as f:
                data = json.loads(await f.read())
            users.append(User.from_dict(data))
        return sorted(users, key=lambda u: u.created_at, reverse=True)
