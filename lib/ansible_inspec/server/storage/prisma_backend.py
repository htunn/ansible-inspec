"""
Database storage backend using Prisma ORM.

This module implements the storage interface using Prisma Python client
for PostgreSQL database operations.
"""

import logging
from datetime import datetime
from typing import List, Optional
import json

from prisma import Prisma
from prisma.models import (
    User, JobTemplate, Job, WorkflowTemplate, WorkflowNode,
    VCSCredential, VCSRepository
)

from ansible_inspec.server.storage.base import StorageBackend
from ansible_inspec.server.db.prisma_client import get_db
from ansible_inspec.server.models import (
    JobTemplate as JobTemplateModel,
    Job as JobModel,
    WorkflowTemplate as WorkflowTemplateModel,
    User as UserModel,
    VCSCredential as VCSCredentialModel,
)

logger = logging.getLogger(__name__)


class PrismaStorageBackend(StorageBackend):
    """Storage backend using Prisma ORM for PostgreSQL."""

    def __init__(self):
        """Initialize Prisma storage backend."""
        logger.info("Initialized Prisma storage backend")

    # ==================== Job Template Operations ====================

    async def save_job_template(self, template: JobTemplateModel) -> None:
        """
        Save or update a job template.
        
        Args:
            template: JobTemplate instance to save
        """
        async with get_db() as db:
            data = {
                "name": template.name,
                "description": template.description,
                "profile": template.profile,
                "extraVars": json.loads(json.dumps(template.extra_vars)) if template.extra_vars else {},
            }
            
            existing = await db.jobtemplate.find_unique(where={"id": template.id})
            
            if existing:
                await db.jobtemplate.update(
                    where={"id": template.id},
                    data=data
                )
                logger.debug(f"Updated job template: {template.name}")
            else:
                await db.jobtemplate.create(
                    data={
                        "id": template.id,
                        **data
                    }
                )
                logger.debug(f"Created job template: {template.name}")

    async def get_job_template(self, template_id: str) -> Optional[JobTemplateModel]:
        """
        Get a job template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            JobTemplate if found, None otherwise
        """
        async with get_db() as db:
            template = await db.jobtemplate.find_unique(
                where={"id": template_id}
            )
            
            if template:
                return JobTemplateModel(
                    id=template.id,
                    name=template.name,
                    description=template.description,
                    profile=template.profile,
                    extra_vars=template.extraVars if template.extraVars else {},
                    created_at=template.createdAt,
                    updated_at=template.updatedAt,
                )
            return None

    async def list_job_templates(self) -> List[JobTemplateModel]:
        """
        List all job templates.
        
        Returns:
            List of JobTemplate instances
        """
        async with get_db() as db:
            templates = await db.jobtemplate.find_many(
                order={"createdAt": "desc"}
            )
            
            return [
                JobTemplateModel(
                    id=t.id,
                    name=t.name,
                    description=t.description,
                    profile=t.profile,
                    extra_vars=t.extraVars if t.extraVars else {},
                    created_at=t.createdAt,
                    updated_at=t.updatedAt,
                )
                for t in templates
            ]

    async def delete_job_template(self, template_id: str) -> bool:
        """
        Delete a job template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            True if deleted, False if not found
        """
        async with get_db() as db:
            try:
                await db.jobtemplate.delete(where={"id": template_id})
                logger.debug(f"Deleted job template: {template_id}")
                return True
            except Exception as e:
                logger.warning(f"Failed to delete job template {template_id}: {e}")
                return False

    # ==================== Job Operations ====================

    async def save_job(self, job: JobModel) -> None:
        """
        Save or update a job.
        
        Args:
            job: Job instance to save
        """
        async with get_db() as db:
            data = {
                "templateId": job.template_id,
                "templateName": job.template_name,
                "status": job.status,
                "target": job.target,
                "extraVars": json.loads(json.dumps(job.extra_vars)) if job.extra_vars else {},
                "stdout": job.stdout,
                "stderr": job.stderr,
                "exitCode": job.exit_code,
                "startedAt": job.started_at,
                "finishedAt": job.finished_at,
            }
            
            existing = await db.job.find_unique(where={"id": job.id})
            
            if existing:
                await db.job.update(
                    where={"id": job.id},
                    data=data
                )
                logger.debug(f"Updated job: {job.id}")
            else:
                await db.job.create(
                    data={
                        "id": job.id,
                        **data
                    }
                )
                logger.debug(f"Created job: {job.id}")

    async def get_job(self, job_id: str) -> Optional[JobModel]:
        """
        Get a job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job if found, None otherwise
        """
        async with get_db() as db:
            job = await db.job.find_unique(where={"id": job_id})
            
            if job:
                return JobModel(
                    id=job.id,
                    template_id=job.templateId,
                    template_name=job.templateName,
                    status=job.status,
                    target=job.target,
                    extra_vars=job.extraVars if job.extraVars else {},
                    stdout=job.stdout,
                    stderr=job.stderr,
                    exit_code=job.exitCode,
                    started_at=job.startedAt,
                    finished_at=job.finishedAt,
                    created_at=job.createdAt,
                )
            return None

    async def list_jobs(self) -> List[JobModel]:
        """
        List all jobs.
        
        Returns:
            List of Job instances
        """
        async with get_db() as db:
            jobs = await db.job.find_many(
                order={"createdAt": "desc"}
            )
            
            return [
                JobModel(
                    id=j.id,
                    template_id=j.templateId,
                    template_name=j.templateName,
                    status=j.status,
                    target=j.target,
                    extra_vars=j.extraVars if j.extraVars else {},
                    stdout=j.stdout,
                    stderr=j.stderr,
                    exit_code=j.exitCode,
                    started_at=j.startedAt,
                    finished_at=j.finishedAt,
                    created_at=j.createdAt,
                )
                for j in jobs
            ]

    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if deleted, False if not found
        """
        async with get_db() as db:
            try:
                await db.job.delete(where={"id": job_id})
                logger.debug(f"Deleted job: {job_id}")
                return True
            except Exception as e:
                logger.warning(f"Failed to delete job {job_id}: {e}")
                return False

    # ==================== Workflow Template Operations ====================

    async def save_workflow_template(self, workflow: WorkflowTemplateModel) -> None:
        """
        Save or update a workflow template.
        
        Args:
            workflow: WorkflowTemplate instance to save
        """
        async with get_db() as db:
            # Save workflow template
            workflow_data = {
                "name": workflow.name,
                "description": workflow.description,
            }
            
            existing = await db.workflowtemplate.find_unique(where={"id": workflow.id})
            
            if existing:
                await db.workflowtemplate.update(
                    where={"id": workflow.id},
                    data=workflow_data
                )
            else:
                await db.workflowtemplate.create(
                    data={
                        "id": workflow.id,
                        **workflow_data
                    }
                )
            
            # Save workflow nodes
            # First, delete existing nodes
            await db.workflownode.delete_many(where={"workflowId": workflow.id})
            
            # Then create new nodes
            for node in workflow.nodes:
                await db.workflownode.create(
                    data={
                        "id": node.id,
                        "workflowId": workflow.id,
                        "templateId": node.template_id,
                        "name": node.name,
                        "position": node.position,
                        "dependencies": json.loads(json.dumps(node.dependencies)) if node.dependencies else [],
                    }
                )
            
            logger.debug(f"Saved workflow template: {workflow.name}")

    async def get_workflow_template(self, workflow_id: str) -> Optional[WorkflowTemplateModel]:
        """
        Get a workflow template by ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            WorkflowTemplate if found, None otherwise
        """
        async with get_db() as db:
            workflow = await db.workflowtemplate.find_unique(
                where={"id": workflow_id},
                include={"nodes": True}
            )
            
            if workflow:
                from ansible_inspec.server.models import WorkflowNode
                
                nodes = [
                    WorkflowNode(
                        id=n.id,
                        template_id=n.templateId,
                        name=n.name,
                        position=n.position,
                        dependencies=n.dependencies if n.dependencies else [],
                    )
                    for n in workflow.nodes
                ]
                
                return WorkflowTemplateModel(
                    id=workflow.id,
                    name=workflow.name,
                    description=workflow.description,
                    nodes=nodes,
                    created_at=workflow.createdAt,
                    updated_at=workflow.updatedAt,
                )
            return None

    async def list_workflow_templates(self) -> List[WorkflowTemplateModel]:
        """
        List all workflow templates.
        
        Returns:
            List of WorkflowTemplate instances
        """
        async with get_db() as db:
            workflows = await db.workflowtemplate.find_many(
                include={"nodes": True},
                order={"createdAt": "desc"}
            )
            
            from ansible_inspec.server.models import WorkflowNode
            
            result = []
            for w in workflows:
                nodes = [
                    WorkflowNode(
                        id=n.id,
                        template_id=n.templateId,
                        name=n.name,
                        position=n.position,
                        dependencies=n.dependencies if n.dependencies else [],
                    )
                    for n in w.nodes
                ]
                
                result.append(
                    WorkflowTemplateModel(
                        id=w.id,
                        name=w.name,
                        description=w.description,
                        nodes=nodes,
                        created_at=w.createdAt,
                        updated_at=w.updatedAt,
                    )
                )
            
            return result

    async def delete_workflow_template(self, workflow_id: str) -> bool:
        """
        Delete a workflow template by ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if deleted, False if not found
        """
        async with get_db() as db:
            try:
                # Cascade delete will handle nodes automatically
                await db.workflowtemplate.delete(where={"id": workflow_id})
                logger.debug(f"Deleted workflow template: {workflow_id}")
                return True
            except Exception as e:
                logger.warning(f"Failed to delete workflow template {workflow_id}: {e}")
                return False

    # ==================== VCS Credential Operations ====================

    async def save_vcs_credential(self, credential: VCSCredentialModel) -> None:
        """
        Save or update a VCS credential.
        
        Args:
            credential: VCSCredential instance to save (should be encrypted)
        """
        async with get_db() as db:
            data = {
                "name": credential.name,
                "vcsType": credential.vcs_type,
                "username": credential.username,
                "password": credential.password,
                "sshPrivateKey": credential.ssh_private_key,
                "token": credential.token,
                "repositoryUrl": credential.repository_url,
            }
            
            existing = await db.vcscredential.find_unique(where={"id": credential.id})
            
            if existing:
                await db.vcscredential.update(
                    where={"id": credential.id},
                    data=data
                )
                logger.debug(f"Updated VCS credential: {credential.name}")
            else:
                await db.vcscredential.create(
                    data={
                        "id": credential.id,
                        **data
                    }
                )
                logger.debug(f"Created VCS credential: {credential.name}")

    async def get_vcs_credential(self, credential_id: str) -> Optional[VCSCredentialModel]:
        """
        Get a VCS credential by ID.
        
        Args:
            credential_id: Credential ID
            
        Returns:
            VCSCredential if found (encrypted), None otherwise
        """
        async with get_db() as db:
            cred = await db.vcscredential.find_unique(where={"id": credential_id})
            
            if cred:
                return VCSCredentialModel(
                    id=cred.id,
                    name=cred.name,
                    vcs_type=cred.vcsType,
                    username=cred.username,
                    password=cred.password,
                    ssh_private_key=cred.sshPrivateKey,
                    token=cred.token,
                    repository_url=cred.repositoryUrl,
                    encrypted=True,  # Data from DB is encrypted
                )
            return None

    async def list_vcs_credentials(self) -> List[VCSCredentialModel]:
        """
        List all VCS credentials.
        
        Returns:
            List of VCSCredential instances (encrypted)
        """
        async with get_db() as db:
            credentials = await db.vcscredential.find_many(
                order={"createdAt": "desc"}
            )
            
            return [
                VCSCredentialModel(
                    id=c.id,
                    name=c.name,
                    vcs_type=c.vcsType,
                    username=c.username,
                    password=c.password,
                    ssh_private_key=c.sshPrivateKey,
                    token=c.token,
                    repository_url=c.repositoryUrl,
                    encrypted=True,
                )
                for c in credentials
            ]

    async def delete_vcs_credential(self, credential_id: str) -> bool:
        """
        Delete a VCS credential by ID.
        
        Args:
            credential_id: Credential ID
            
        Returns:
            True if deleted, False if not found
        """
        async with get_db() as db:
            try:
                await db.vcscredential.delete(where={"id": credential_id})
                logger.debug(f"Deleted VCS credential: {credential_id}")
                return True
            except Exception as e:
                logger.warning(f"Failed to delete VCS credential {credential_id}: {e}")
                return False

    # ==================== User Operations ====================

    async def save_user(self, user: UserModel) -> None:
        """
        Save or update a user.
        
        Args:
            user: User instance to save
        """
        async with get_db() as db:
            data = {
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "roles": json.loads(json.dumps(user.roles)) if user.roles else [],
                "tenantId": user.tenant_id,
                "active": user.active,
                "lastLogin": user.last_login,
            }
            
            existing = await db.user.find_unique(where={"id": user.id})
            
            if existing:
                await db.user.update(
                    where={"id": user.id},
                    data=data
                )
                logger.debug(f"Updated user: {user.username}")
            else:
                await db.user.create(
                    data={
                        "id": user.id,
                        **data
                    }
                )
                logger.debug(f"Created user: {user.username}")

    async def get_user(self, user_id: str) -> Optional[UserModel]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        async with get_db() as db:
            user = await db.user.find_unique(where={"id": user_id})
            
            if user:
                return UserModel(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    name=user.name,
                    roles=user.roles if user.roles else [],
                    tenant_id=user.tenantId,
                    active=user.active,
                    created_at=user.createdAt,
                    last_login=user.lastLogin,
                )
            return None

    async def get_user_by_username(self, username: str) -> Optional[UserModel]:
        """
        Get a user by username.
        
        Args:
            username: Username
            
        Returns:
            User if found, None otherwise
        """
        async with get_db() as db:
            user = await db.user.find_unique(where={"username": username})
            
            if user:
                return UserModel(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    name=user.name,
                    roles=user.roles if user.roles else [],
                    tenant_id=user.tenantId,
                    active=user.active,
                    created_at=user.createdAt,
                    last_login=user.lastLogin,
                )
            return None

    async def list_users(self) -> List[UserModel]:
        """
        List all users.
        
        Returns:
            List of User instances
        """
        async with get_db() as db:
            users = await db.user.find_many(
                order={"createdAt": "desc"}
            )
            
            return [
                UserModel(
                    id=u.id,
                    username=u.username,
                    email=u.email,
                    name=u.name,
                    roles=u.roles if u.roles else [],
                    tenant_id=u.tenantId,
                    active=u.active,
                    created_at=u.createdAt,
                    last_login=u.lastLogin,
                )
                for u in users
            ]
