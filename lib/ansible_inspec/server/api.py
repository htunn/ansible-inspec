"""
REST API server for ansible-inspec with Prisma ORM.

Provides enterprise-grade REST API with authentication, VCS integration,
and database-backed storage.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ansible_inspec.server.config import Settings
from ansible_inspec.server.db.prisma_client import initialize_database, shutdown_database, get_db
from ansible_inspec.server.storage import create_storage
from ansible_inspec.server.storage.base import StorageBackend
from ansible_inspec.server.auth.dependencies import get_current_user, get_current_active_user, require_role
from ansible_inspec.server.auth.azure_ad import AzureADAuth
from ansible_inspec.server.encryption import EncryptionService
from ansible_inspec.server.vcs.manager import VCSManager
from ansible_inspec.server.models import (
    JobTemplate as JobTemplateModel,
    Job as JobModel,
    User as UserModel,
    VCSCredential as VCSCredentialModel,
)
from ansible_inspec.server.monitoring import (
    record_storage_operation,
    record_auth_request,
    update_validation_days_remaining,
)

logger = logging.getLogger(__name__)

# Global instances
settings = Settings()
storage: Optional[StorageBackend] = None
encryption: Optional[EncryptionService] = None
vcs_manager: Optional[VCSManager] = None
azure_ad: Optional[AzureADAuth] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global storage, encryption, vcs_manager, azure_ad
    
    logger.info("Starting ansible-inspec API server...")
    
    # Initialize database
    await initialize_database(settings)
    
    # Initialize storage backend
    storage = create_storage(
        storage_backend=settings.storage_backend,
        data_dir=settings.data_dir
    )
    logger.info(f"Storage backend: {settings.storage_backend}")
    
    # Initialize encryption
    encryption_key = settings.encryption_key or os.getenv("ENCRYPTION_KEY")
    if encryption_key:
        encryption = EncryptionService(key=encryption_key)
        logger.info("Encryption service initialized")
    else:
        logger.warning("No encryption key configured - VCS credentials will not be encrypted")
    
    # Initialize VCS manager
    if settings.vcs.enabled and encryption:
        vcs_manager = VCSManager(storage=storage, encryption=encryption)
        logger.info("VCS manager initialized")
    
    # Initialize Azure AD
    if settings.auth.enabled:
        azure_ad = AzureADAuth(settings)  # Pass full settings object
        logger.info("Azure AD authentication enabled")
    else:
        logger.info("Authentication disabled - running in development mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ansible-inspec API server...")
    await shutdown_database()


# Create FastAPI app
app = FastAPI(
    title="Ansible-InSpec API",
    description="Enterprise compliance testing with Ansible and InSpec integration",
    version="0.4.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic Models ====================

class JobTemplateCreate(BaseModel):
    """Job template creation schema."""
    name: str
    description: Optional[str] = ""
    profile: str
    extra_vars: Dict[str, Any] = {}


class JobTemplateUpdate(BaseModel):
    """Job template update schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    profile: Optional[str] = None
    extra_vars: Optional[Dict[str, Any]] = None


class JobCreate(BaseModel):
    """Job creation schema."""
    template_id: str
    target: Optional[str] = None
    extra_vars: Dict[str, Any] = {}


class VCSCredentialCreate(BaseModel):
    """VCS credential creation schema."""
    name: str
    vcs_type: str  # github, gitlab, bitbucket, git
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_private_key: Optional[str] = None
    token: Optional[str] = None
    repository_url: Optional[str] = None


class VCSRepositoryCreate(BaseModel):
    """VCS repository creation schema."""
    name: str
    url: str
    branch: str = "main"
    credential_id: Optional[str] = None
    poll_interval: int = 300  # seconds
    profile_path: str = "inspec"
    auto_import: bool = True


class UserUpdate(BaseModel):
    """User update schema."""
    roles: Optional[List[str]] = None
    active: Optional[bool] = None


# ==================== Root Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint - redirect to docs."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.4.0",
        "storage_backend": settings.storage_backend,
        "auth_enabled": settings.auth.enabled,
        "vcs_enabled": settings.vcs.enabled,
    }


@app.get("/api/v1")
async def api_info():
    """API information."""
    return {
        "name": "Ansible-InSpec API",
        "version": "0.4.0",
        "endpoints": {
            "job_templates": "/api/v1/job-templates",
            "jobs": "/api/v1/jobs",
            "workflows": "/api/v1/workflows",
            "users": "/api/v1/users",
            "vcs_credentials": "/api/v1/vcs/credentials",
            "vcs_repositories": "/api/v1/vcs/repositories",
            "auth": "/api/v1/auth",
        }
    }


# ==================== Authentication Endpoints ====================

@app.get("/api/v1/auth/login")
async def login(request: Request):
    """Redirect to Azure AD login."""
    if not settings.auth.enabled or not azure_ad:
        raise HTTPException(status_code=501, detail="Authentication not enabled")
    
    # Build redirect URI
    redirect_uri = settings.auth.oauth_redirect_uri or str(request.base_url) + "api/v1/auth/callback"
    auth_url = azure_ad.get_authorization_url(redirect_uri=redirect_uri)
    
    record_auth_request(method="login", status="initiated")
    return RedirectResponse(url=auth_url)


@app.get("/api/v1/auth/callback")
async def auth_callback(code: str, state: Optional[str] = None):
    """OAuth2 callback endpoint."""
    if not settings.auth.enabled or not azure_ad:
        raise HTTPException(status_code=501, detail="Authentication not enabled")
    
    try:
        # Exchange code for token
        token_data = await azure_ad.exchange_code_for_token(code)
        
        # Validate token and extract claims
        user_info = await azure_ad.validate_token(token_data["access_token"])
        
        # Create or update user in database
        async with get_db() as db:
            user = await db.user.find_unique(where={"username": user_info["username"]})
            
            if not user:
                # Create new user
                user = await db.user.create(
                    data={
                        "username": user_info["username"],
                        "email": user_info["email"],
                        "name": user_info.get("name"),
                        "roles": user_info.get("roles", ["viewer"]),
                        "tenantId": user_info.get("tenant_id"),
                        "active": True,
                        "lastLogin": datetime.now(),
                    }
                )
            else:
                # Update last login
                user = await db.user.update(
                    where={"id": user.id},
                    data={"lastLogin": datetime.now()}
                )
        
        # Create JWT session token
        session_token = azure_ad.create_jwt_token(user_info)
        
        record_auth_request(method="callback", status="success")
        
        return {
            "access_token": session_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "roles": user.roles,
            }
        }
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        record_auth_request(method="callback", status="failed")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: UserModel = Depends(get_current_active_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "name": current_user.name,
        "roles": current_user.roles,
        "active": current_user.active,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
    }


@app.post("/api/v1/auth/logout")
async def logout():
    """Logout endpoint."""
    record_auth_request(method="logout", status="success")
    return {"message": "Logged out successfully"}


# ==================== Job Template Endpoints ====================

@app.get("/api/v1/job-templates")
async def list_job_templates(
    current_user: Optional[UserModel] = Depends(get_current_user)
):
    """List all job templates."""
    templates = await storage.list_job_templates()
    return {
        "count": len(templates),
        "results": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "profile": t.profile,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in templates
        ]
    }


@app.post("/api/v1/job-templates", status_code=status.HTTP_201_CREATED)
async def create_job_template(
    template_data: JobTemplateCreate,
    current_user: UserModel = Depends(require_role("operator"))
):
    """Create a new job template."""
    import uuid
    
    template = JobTemplateModel(
        id=str(uuid.uuid4()),
        name=template_data.name,
        description=template_data.description or "",
        profile=template_data.profile,
        extra_vars=template_data.extra_vars,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    await storage.save_job_template(template)
    record_storage_operation(backend=settings.storage_backend, operation="create", status="success")
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "profile": template.profile,
        "created_at": template.created_at.isoformat(),
    }


@app.get("/api/v1/job-templates/{template_id}")
async def get_job_template(
    template_id: str,
    current_user: Optional[UserModel] = Depends(get_current_user)
):
    """Get a specific job template."""
    template = await storage.get_job_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Job template not found")
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "profile": template.profile,
        "extra_vars": template.extra_vars,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }


@app.put("/api/v1/job-templates/{template_id}")
async def update_job_template(
    template_id: str,
    update_data: JobTemplateUpdate,
    current_user: UserModel = Depends(require_role("operator"))
):
    """Update a job template."""
    template = await storage.get_job_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Job template not found")
    
    # Update fields
    if update_data.name is not None:
        template.name = update_data.name
    if update_data.description is not None:
        template.description = update_data.description
    if update_data.profile is not None:
        template.profile = update_data.profile
    if update_data.extra_vars is not None:
        template.extra_vars = update_data.extra_vars
    
    template.updated_at = datetime.now()
    
    await storage.save_job_template(template)
    record_storage_operation(backend=settings.storage_backend, operation="update", status="success")
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "profile": template.profile,
        "updated_at": template.updated_at.isoformat(),
    }


@app.delete("/api/v1/job-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_template(
    template_id: str,
    current_user: UserModel = Depends(require_role("admin"))
):
    """Delete a job template."""
    if not await storage.delete_job_template(template_id):
        raise HTTPException(status_code=404, detail="Job template not found")
    
    record_storage_operation(backend=settings.storage_backend, operation="delete", status="success")
    return None


# ==================== Job Endpoints ====================

@app.get("/api/v1/jobs")
async def list_jobs(
    current_user: Optional[UserModel] = Depends(get_current_user)
):
    """List all jobs."""
    jobs = await storage.list_jobs()
    return {
        "count": len(jobs),
        "results": [
            {
                "id": j.id,
                "template_id": j.template_id,
                "template_name": j.template_name,
                "status": j.status,
                "target": j.target,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            }
            for j in jobs
        ]
    }


@app.post("/api/v1/jobs", status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: UserModel = Depends(require_role("operator"))
):
    """Create and launch a new job."""
    import uuid
    
    # Get template
    template = await storage.get_job_template(job_data.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Job template not found")
    
    # Create job
    job = JobModel(
        id=str(uuid.uuid4()),
        template_id=template.id,
        template_name=template.name,
        status="pending",
        target=job_data.target,
        extra_vars=job_data.extra_vars,
        created_at=datetime.now(),
    )
    
    await storage.save_job(job)
    record_storage_operation(backend=settings.storage_backend, operation="create", status="success")
    
    # TODO: Launch job in background using executor
    
    return {
        "id": job.id,
        "template_id": job.template_id,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
    }


@app.get("/api/v1/jobs/{job_id}")
async def get_job(
    job_id: str,
    current_user: Optional[UserModel] = Depends(get_current_user)
):
    """Get a specific job."""
    job = await storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": job.id,
        "template_id": job.template_id,
        "template_name": job.template_name,
        "status": job.status,
        "target": job.target,
        "extra_vars": job.extra_vars,
        "stdout": job.stdout,
        "stderr": job.stderr,
        "exit_code": job.exit_code,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


# ==================== VCS Credential Endpoints ====================

@app.post("/api/v1/vcs/credentials", status_code=status.HTTP_201_CREATED)
async def create_vcs_credential(
    cred_data: VCSCredentialCreate,
    current_user: UserModel = Depends(require_role("admin"))
):
    """Create a VCS credential."""
    import uuid
    
    if not encryption:
        raise HTTPException(status_code=501, detail="Encryption not configured")
    
    credential = VCSCredentialModel(
        id=str(uuid.uuid4()),
        name=cred_data.name,
        vcs_type=cred_data.vcs_type,
        username=cred_data.username,
        password=cred_data.password,
        ssh_private_key=cred_data.ssh_private_key,
        token=cred_data.token,
        repository_url=cred_data.repository_url,
        encrypted=False,
    )
    
    # Encrypt credentials
    credential.encrypt_credentials(encryption)
    
    await storage.save_vcs_credential(credential)
    
    return {
        "id": credential.id,
        "name": credential.name,
        "vcs_type": credential.vcs_type,
        "username": credential.username,
    }


@app.get("/api/v1/vcs/credentials")
async def list_vcs_credentials(
    current_user: UserModel = Depends(require_role("operator"))
):
    """List VCS credentials (without decrypted secrets)."""
    credentials = await storage.list_vcs_credentials()
    
    return {
        "count": len(credentials),
        "results": [
            {
                "id": c.id,
                "name": c.name,
                "vcs_type": c.vcs_type,
                "username": c.username,
            }
            for c in credentials
        ]
    }


@app.delete("/api/v1/vcs/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vcs_credential(
    credential_id: str,
    current_user: UserModel = Depends(require_role("admin"))
):
    """Delete a VCS credential."""
    if not await storage.delete_vcs_credential(credential_id):
        raise HTTPException(status_code=404, detail="VCS credential not found")
    
    return None


# ==================== VCS Repository Endpoints ====================

@app.post("/api/v1/vcs/repositories", status_code=status.HTTP_201_CREATED)
async def create_vcs_repository(
    repo_data: VCSRepositoryCreate,
    current_user: UserModel = Depends(require_role("admin"))
):
    """Create a VCS repository configuration."""
    if not vcs_manager:
        raise HTTPException(status_code=501, detail="VCS not enabled")
    
    async with get_db() as db:
        # Check if repository already exists
        existing = await db.vcsrepository.find_unique(where={"name": repo_data.name})
        if existing:
            raise HTTPException(status_code=400, detail="Repository already exists")
        
        # Create repository
        repo = await db.vcsrepository.create(
            data={
                "name": repo_data.name,
                "url": repo_data.url,
                "branch": repo_data.branch,
                "credentialId": repo_data.credential_id,
                "pollInterval": repo_data.poll_interval,
                "profilePath": repo_data.profile_path,
                "autoImport": repo_data.auto_import,
                "syncStatus": "idle",
            }
        )
        
        return {
            "id": repo.id,
            "name": repo.name,
            "url": repo.url,
            "branch": repo.branch,
            "auto_import": repo.autoImport,
        }


@app.get("/api/v1/vcs/repositories")
async def list_vcs_repositories(
    current_user: UserModel = Depends(require_role("operator"))
):
    """List VCS repositories."""
    if not vcs_manager:
        raise HTTPException(status_code=501, detail="VCS not enabled")
    
    repos = await vcs_manager.list_sync_jobs()
    return {"count": len(repos), "results": repos}


@app.post("/api/v1/vcs/repositories/{repo_name}/sync")
async def trigger_repository_sync(
    repo_name: str,
    current_user: UserModel = Depends(require_role("operator"))
):
    """Manually trigger repository synchronization."""
    if not vcs_manager:
        raise HTTPException(status_code=501, detail="VCS not enabled")
    
    result = await vcs_manager.trigger_manual_sync(repo_name)
    return result


# ==================== User Management Endpoints ====================

@app.get("/api/v1/users")
async def list_users(
    current_user: UserModel = Depends(require_role("admin"))
):
    """List all users (admin only)."""
    users = await storage.list_users()
    
    return {
        "count": len(users),
        "results": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "name": u.name,
                "roles": u.roles,
                "active": u.active,
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ]
    }


@app.put("/api/v1/users/{user_id}")
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: UserModel = Depends(require_role("admin"))
):
    """Update user roles and status (admin only)."""
    user = await storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if update_data.roles is not None:
        user.roles = update_data.roles
    if update_data.active is not None:
        user.active = update_data.active
    
    await storage.save_user(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "roles": user.roles,
        "active": user.active,
    }


# ==================== Storage Validation Endpoint ====================

@app.get("/api/v1/storage/validation-status")
async def get_validation_status(
    current_user: UserModel = Depends(require_role("admin"))
):
    """Get hybrid storage validation status."""
    if settings.storage_backend != "hybrid":
        raise HTTPException(status_code=400, detail="Not using hybrid storage")
    
    from ansible_inspec.server.storage.hybrid import HybridStorage
    
    if isinstance(storage, HybridStorage):
        status_data = storage.get_validation_status()
        return status_data
    else:
        raise HTTPException(status_code=500, detail="Storage backend is not HybridStorage")


# ==================== Metrics Endpoint ====================

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
