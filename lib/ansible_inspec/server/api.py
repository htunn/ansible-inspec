"""
REST API server for ansible-inspec with Prisma ORM.

Provides enterprise-grade REST API with authentication, VCS integration,
and database-backed storage.
"""

import os
import logging
import json
import time
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
from ansible_inspec.server.vcs.scheduler import VCSPollingScheduler
from prisma.models import (
    JobTemplate as JobTemplateModel,
    Job as JobModel,
    User as UserModel,
    VCSCredential as VCSCredentialModel,
)
from prisma import Json as PrismaJson
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
vcs_scheduler: Optional[VCSPollingScheduler] = None
azure_ad: Optional[AzureADAuth] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global storage, encryption, vcs_manager, vcs_scheduler, azure_ad
    
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
    
    # Initialize VCS manager (only if database is available)
    if settings.vcs.enabled and encryption:
        # Check if database is connected before initializing VCS
        from ansible_inspec.server.db.prisma_client import _prisma_client
        
        if _prisma_client is not None:
            vcs_manager = VCSManager(storage=storage, encryption=encryption)
            logger.info("VCS manager initialized")
            
            # Initialize and start VCS scheduler
            vcs_scheduler = VCSPollingScheduler()
            vcs_scheduler.start()
            logger.info("VCS polling scheduler started")
            
            # Load repositories from database and create polling jobs
            try:
                async with get_db() as db:
                    repositories = await db.vcsrepository.find_many()
                
                for repo in repositories:
                    # Create polling job for each enabled repository
                    async def poll_func(repository_url=repo.url, credential_id=repo.credentialId):
                        """Async wrapper for repository sync"""
                        try:
                            await vcs_manager.sync_repository(repo.name)
                        except Exception as e:
                            logger.error(f"VCS sync failed for {repo.name}: {e}")
                    
                    vcs_scheduler.add_vcs_poll_job(
                        job_id=f"vcs-poll-{repo.name}",
                        repository_url=repo.url,
                        credential_id=repo.credentialId or "",
                        poll_interval_minutes=(repo.pollInterval // 60) or settings.vcs.poll_interval_minutes,
                        func=poll_func
                    )
                
                logger.info(f"Loaded {len(repositories)} VCS repositories for polling")
            except Exception as e:
                logger.error(f"Failed to load VCS repositories: {e}")
        else:
            logger.info("VCS manager disabled - database not available")
    
    # Initialize Azure AD
    if settings.auth.enabled:
        azure_ad = AzureADAuth(settings)  # Pass full settings object
        logger.info("Azure AD authentication enabled")
    else:
        logger.info("Authentication disabled - running in development mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ansible-inspec API server...")
    
    # Shutdown VCS scheduler
    if vcs_scheduler:
        vcs_scheduler.shutdown(wait=True)
        logger.info("VCS scheduler shut down")
    
    await shutdown_database()


# Create FastAPI app
app = FastAPI(
    title="Ansible-InSpec API",
    description="Enterprise compliance testing with Ansible and InSpec integration",
    version="0.2.7",
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
    vcs_repo_id: Optional[str] = None
    vcs_path: Optional[str] = None
    vcs_sync: bool = False


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
    from ansible_inspec.server.db.prisma_client import _prisma_client
    
    # Check if database is connected
    database_status = "connected" if _prisma_client is not None else "disconnected"
    
    return {
        "status": "healthy",
        "version": "0.2.7",
        "storage_backend": settings.storage_backend,
        "database": database_status,
        "auth_enabled": settings.auth.enabled,
        "vcs_enabled": settings.vcs.enabled,
    }


@app.get("/api/v1")
async def api_info():
    """API information."""
    return {
        "name": "Ansible-InSpec API",
        "version": "0.2.7",
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
    
    record_auth_request(provider="azure_ad", status="initiated")
    return RedirectResponse(url=auth_url)


class PasswordLoginRequest(BaseModel):
    """Password login request"""
    username: str
    password: str


@app.post("/api/v1/auth/password-login")
async def password_login(login_request: PasswordLoginRequest):
    """
    Login with username and password.
    Returns JWT token for authentication.
    """
    try:
        # Find user in database
        async with get_db() as db:
            user = await db.user.find_unique(where={"username": login_request.username})
            
            if not user or not user.active:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid username or password"
                )
            
            # For demo/dev purposes, we'll use a simple password check
            # In production, use proper password hashing (bcrypt, argon2, etc.)
            # Check if user has password field (needs to be added to schema)
            # For now, we'll accept any password for existing users as a fallback
            
            # Update last login
            await db.user.update(
                where={"id": user.id},
                data={"lastLogin": datetime.now()}
            )
        
        # Create JWT session token with roles from database
        session_user_info = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "roles": json.loads(user.roles) if isinstance(user.roles, str) else user.roles,
            "tenant_id": user.tenantId
        }
        
        # Create token using azure_ad service or a basic JWT service
        if azure_ad:
            session_token = azure_ad.create_jwt_token(session_user_info)
        else:
            raise HTTPException(status_code=501, detail="Token generation not available")
        
        record_auth_request(provider="password", status="success")
        
        # Create response with cookie
        response_data = {
            "access_token": session_token,
            "token_type": "bearer",
            "user": {
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "roles": json.loads(user.roles) if isinstance(user.roles, str) else user.roles,
            }
        }
        
        # Return JSONResponse to set cookie
        from fastapi.responses import JSONResponse
        response = JSONResponse(content=response_data)
        
        # Set HTTP-only cookie with token
        response.set_cookie(
            key=settings.auth.cookie_name,
            value=session_token,
            max_age=settings.auth.access_token_expire_minutes * 60,  # Convert to seconds
            httponly=settings.auth.cookie_httponly,
            secure=settings.auth.cookie_secure,
            samesite=settings.auth.cookie_samesite
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password login error: {e}")
        record_auth_request(provider="password", status="failed")
        raise HTTPException(status_code=500, detail="Login failed")


@app.get("/api/v1/auth/callback")
async def auth_callback(request: Request, code: str, state: Optional[str] = None):
    """OAuth2 callback endpoint."""
    if not settings.auth.enabled or not azure_ad:
        raise HTTPException(status_code=501, detail="Authentication not enabled")
    
    try:
        # Build redirect URI (must match the one used in authorization request)
        redirect_uri = settings.auth.oauth_redirect_uri or str(request.base_url) + "api/v1/auth/callback"
        
        # Exchange code for token
        token_data = await azure_ad.exchange_code_for_token(code, redirect_uri)
        
        # Validate ID token and extract claims (use id_token, not access_token)
        user_info = await azure_ad.validate_token(token_data["id_token"])
        
        # Create or update user in database
        async with get_db() as db:
            user = await db.user.find_unique(where={"username": user_info["username"]})
            
            if not user:
                # Create new user
                # Get roles from Azure AD or default to admin
                roles = user_info.get("roles", [])
                if not roles:
                    roles = ["admin"]  # Default new users to admin role
                
                user = await db.user.create(
                    data={
                        "username": user_info["username"],
                        "email": user_info["email"],
                        "name": user_info.get("name"),
                        "roles": json.dumps(roles),  # Convert list to JSON string for Prisma Json type
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
        
        # Create JWT session token with roles from database, not Azure AD
        session_user_info = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "roles": json.loads(user.roles) if isinstance(user.roles, str) else user.roles,
            "tenant_id": user.tenantId
        }
        session_token = azure_ad.create_jwt_token(session_user_info)
        
        record_auth_request(provider="azure_ad", status="success")
        
        # Redirect to Streamlit UI with token as query parameter
        streamlit_url = settings.auth.streamlit_ui_url
        response = RedirectResponse(url=f"{streamlit_url}/?token={session_token}")
        
        # Also set cookie as backup
        response.set_cookie(
            key=settings.auth.cookie_name,
            value=session_token,
            max_age=settings.auth.access_token_expire_minutes * 60,  # Convert to seconds
            httponly=settings.auth.cookie_httponly,
            secure=settings.auth.cookie_secure,
            samesite=settings.auth.cookie_samesite
        )
        
        return response
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        record_auth_request(provider="azure_ad", status="failed")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_active_user)):
    """Get current user information."""
    return {
        "id": current_user.get("user_id"),
        "username": current_user.get("username"),
        "email": current_user.get("email"),
        "name": current_user.get("name"),
        "roles": current_user.get("roles", []),
        "tenant_id": current_user.get("tenant_id"),
    }


@app.post("/api/v1/auth/logout")
async def logout():
    """Logout endpoint - clears authentication cookie."""
    from fastapi.responses import JSONResponse
    
    record_auth_request(provider="logout", status="success")
    
    response = JSONResponse(content={"message": "Logged out successfully"})
    
    # Clear the authentication cookie
    response.delete_cookie(
        key=settings.auth.cookie_name,
        httponly=settings.auth.cookie_httponly,
        secure=settings.auth.cookie_secure,
        samesite=settings.auth.cookie_samesite
    )
    
    return response


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
                "created_at": t.createdAt.isoformat() if t.createdAt else None,
                "updated_at": t.updatedAt.isoformat() if t.updatedAt else None,
                "vcsRepoId": getattr(t, 'vcsRepoId', None),
                "vcsPath": getattr(t, 'vcsPath', None),
                "vcsSync": getattr(t, 'vcsSync', False),
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
    import json
    import time
    
    start_time = time.time()
    template = JobTemplateModel(
        id=str(uuid.uuid4()),
        name=template_data.name,
        description=template_data.description or "",
        profile=template_data.profile,
        extraVars=json.dumps(template_data.extra_vars),
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        vcsRepoId=template_data.vcs_repo_id,
        vcsPath=template_data.vcs_path,
        vcsSync=template_data.vcs_sync,
    )
    
    await storage.save_job_template(template)
    duration = time.time() - start_time
    record_storage_operation(backend=settings.storage_backend, operation="create", status="success", duration=duration)
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "profile": template.profile,
        "created_at": template.createdAt.isoformat(),
        "vcsRepoId": template.vcsRepoId,
        "vcsPath": template.vcsPath,
        "vcsSync": template.vcsSync,
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
        "extra_vars": json.loads(template.extraVars) if template.extraVars else {},
        "created_at": template.createdAt.isoformat() if template.createdAt else None,
        "updated_at": template.updatedAt.isoformat() if template.updatedAt else None,
        "vcsRepoId": getattr(template, 'vcsRepoId', None),
        "vcsPath": getattr(template, 'vcsPath', None),
        "vcsSync": getattr(template, 'vcsSync', False),
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
        template.extraVars = json.dumps(update_data.extra_vars)
    
    template.updatedAt = datetime.now()
    
    start_time = time.time()
    await storage.save_job_template(template)
    duration = time.time() - start_time
    record_storage_operation(backend=settings.storage_backend, operation="update", status="success", duration=duration)
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "profile": template.profile,
        "updated_at": template.updatedAt.isoformat(),
    }


@app.delete("/api/v1/job-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_template(
    template_id: str,
    current_user: UserModel = Depends(require_role("admin"))
):
    """Delete a job template."""
    start_time = time.time()
    if not await storage.delete_job_template(template_id):
        raise HTTPException(status_code=404, detail="Job template not found")
    
    duration = time.time() - start_time
    record_storage_operation(backend=settings.storage_backend, operation="delete", status="success", duration=duration)
    return None


@app.post("/api/v1/job-templates/{template_id}/launch", status_code=status.HTTP_201_CREATED)
async def launch_job_from_template(
    template_id: str,
    launch_data: dict = {},
    current_user: UserModel = Depends(require_role("operator"))
):
    """Launch a new job from a template."""
    import uuid
    
    # Get template
    template = await storage.get_job_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Job template not found")
    
    # Merge extra_vars from template and launch
    extra_vars = json.loads(template.extraVars) if template.extraVars else {}
    if "extra_vars" in launch_data:
        extra_vars.update(launch_data["extra_vars"])
    
    # Create job - extraVars as string for Prisma model
    job = JobModel(
        id=str(uuid.uuid4()),
        templateId=template.id,
        templateName=template.name,
        status="pending",
        extraVars=json.dumps(extra_vars),
        createdAt=datetime.now(),
    )
    
    start_time = time.time()
    await storage.save_job(job)
    duration = time.time() - start_time
    record_storage_operation(backend=settings.storage_backend, operation="create", status="success", duration=duration)
    
    # TODO: Launch job in background using executor
    
    return {
        "id": job.id,
        "template_id": job.templateId,
        "status": job.status,
        "created_at": job.createdAt.isoformat(),
    }


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
                "template_id": j.templateId,
                "template_name": j.templateName,
                "status": j.status,
                "target": j.target,
                "stdout": j.stdout,
                "stderr": j.stderr,
                "exit_code": j.exitCode,
                "created_at": j.createdAt.isoformat() if j.createdAt else None,
                "started_at": j.startedAt.isoformat() if j.startedAt else None,
                "finished_at": j.finishedAt.isoformat() if j.finishedAt else None,
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


@app.delete("/api/v1/vcs/repositories/{repo_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vcs_repository(
    repo_name: str,
    current_user: UserModel = Depends(require_role("admin"))
):
    """Delete a VCS repository configuration."""
    async with get_db() as db:
        repo = await db.vcsrepository.find_unique(where={"name": repo_name})
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository '{repo_name}' not found")
        
        # Delete the repository
        await db.vcsrepository.delete(where={"name": repo_name})
        
        logger.info(f"Deleted VCS repository: {repo_name}")
    
    return None


@app.get("/api/v1/vcs/repositories/{repo_name}/history")
async def get_repository_sync_history(
    repo_name: str,
    limit: int = 50,
    current_user: UserModel = Depends(require_role("viewer"))
):
    """
    Get sync history for a repository.
    
    Args:
        repo_name: Repository name
        limit: Maximum number of history records to return (default: 50)
    """
    async with get_db() as db:
        # First, find the repository
        repo = await db.vcsrepository.find_unique(where={"name": repo_name})
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository '{repo_name}' not found")
        
        # Fetch sync history
        history = await db.vcssynchistory.find_many(
            where={"repositoryId": repo.id},
            order={"syncStartedAt": "desc"},
            take=limit
        )
        
        return {
            "repository": repo_name,
            "count": len(history),
            "results": [
                {
                    "id": h.id,
                    "syncStartedAt": h.syncStartedAt.isoformat(),
                    "syncCompletedAt": h.syncCompletedAt.isoformat() if h.syncCompletedAt else None,
                    "status": h.status,
                    "commitHash": h.commitHash,
                    "profilesDiscovered": h.profilesDiscovered,
                    "templatesCreated": h.templatesCreated,
                    "errors": h.errors,
                    "triggeredBy": h.triggeredBy,
                    "triggerType": h.triggerType,
                    "duration_seconds": (
                        (h.syncCompletedAt - h.syncStartedAt).total_seconds()
                        if h.syncCompletedAt else None
                    )
                }
                for h in history
            ]
        }


@app.get("/api/v1/vcs/repositories/{repo_name}/files")
async def list_repository_files(
    repo_name: str,
    current_user: UserModel = Depends(require_role("viewer"))
):
    """
    List all files in a repository.
    
    Args:
        repo_name: Repository name
    """
    import os
    from pathlib import Path
    
    async with get_db() as db:
        # Find the repository
        repo = await db.vcsrepository.find_unique(where={"name": repo_name})
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository '{repo_name}' not found")
        
        if not repo.lastSyncAt:
            raise HTTPException(status_code=400, detail=f"Repository '{repo_name}' has not been synced yet")
        
        # Build path to repository
        repo_path = Path("/tmp/ansible-inspec-repos") / repo_name
        
        if not repo_path.exists():
            raise HTTPException(status_code=404, detail=f"Repository '{repo_name}' not found on disk")
        
        # List all files recursively
        files = []
        for root, dirs, filenames in os.walk(repo_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            
            for filename in filenames:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(repo_path)
                files.append(str(rel_path))
        
        return {
            "repository": repo_name,
            "count": len(files),
            "files": sorted(files)
        }


@app.get("/api/v1/vcs/repositories/{repo_name}/files/{file_path:path}")
async def get_repository_file_content(
    repo_name: str,
    file_path: str,
    current_user: UserModel = Depends(require_role("viewer"))
):
    """
    Get content of a specific file from a repository.
    
    Args:
        repo_name: Repository name
        file_path: Relative path to file within repository
    """
    from pathlib import Path
    
    async with get_db() as db:
        # Find the repository
        repo = await db.vcsrepository.find_unique(where={"name": repo_name})
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository '{repo_name}' not found")
        
        if not repo.lastSyncAt:
            raise HTTPException(status_code=400, detail=f"Repository '{repo_name}' has not been synced yet")
        
        # Build path to file
        repo_path = Path("/tmp/ansible-inspec-repos") / repo_name
        full_file_path = repo_path / file_path
        
        # Security check: ensure file is within repository
        try:
            full_file_path.resolve().relative_to(repo_path.resolve())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        if not full_file_path.exists():
            raise HTTPException(status_code=404, detail=f"File '{file_path}' not found")
        
        if not full_file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path '{file_path}' is not a file")
        
        # Read file content
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Binary file
            raise HTTPException(status_code=400, detail=f"File '{file_path}' is not a text file")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
        
        return {
            "repository": repo_name,
            "file_path": file_path,
            "content": content,
            "size": len(content)
        }


# ==================== VCS Webhook Endpoints ====================

@app.post("/api/v1/webhooks/github/{repo_name}")
async def github_webhook(
    repo_name: str,
    request: Request,
    x_hub_signature_256: Optional[str] = None
):
    """
    GitHub webhook handler for repository push events.
    
    Args:
        repo_name: Repository name to sync
        request: FastAPI request object
        x_hub_signature_256: GitHub webhook signature header
    """
    import hmac
    import hashlib
    
    if not vcs_manager:
        raise HTTPException(status_code=501, detail="VCS not enabled")
    
    if not settings.vcs.webhook_enabled:
        raise HTTPException(status_code=501, detail="Webhooks not enabled")
    
    # Get webhook payload
    body = await request.body()
    
    # Verify webhook signature if secret is configured
    if settings.vcs.webhook_secret:
        if not x_hub_signature_256:
            raise HTTPException(status_code=401, detail="Missing signature header")
        
        # Calculate expected signature
        expected_signature = "sha256=" + hmac.new(
            settings.vcs.webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (constant-time comparison)
        if not hmac.compare_digest(x_hub_signature_256, expected_signature):
            logger.warning(f"Invalid webhook signature for {repo_name}")
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse JSON payload
    try:
        payload = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Check if it's a push event
    if request.headers.get("X-GitHub-Event") != "push":
        return {"message": "Event ignored (not a push event)", "status": "ignored"}
    
    # Trigger sync for this repository
    logger.info(f"GitHub webhook triggered sync for repository: {repo_name}")
    
    try:
        result = await vcs_manager.trigger_manual_sync(repo_name)
        return {
            "message": "Repository sync triggered",
            "status": "success",
            "repository": repo_name,
            "commit": payload.get("after", "unknown")
        }
    except Exception as e:
        logger.error(f"Webhook sync failed for {repo_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@app.post("/api/v1/webhooks/gitlab/{repo_name}")
async def gitlab_webhook(
    repo_name: str,
    request: Request,
    x_gitlab_token: Optional[str] = None
):
    """
    GitLab webhook handler for repository push events.
    
    Args:
        repo_name: Repository name to sync
        request: FastAPI request object
        x_gitlab_token: GitLab webhook token header
    """
    if not vcs_manager:
        raise HTTPException(status_code=501, detail="VCS not enabled")
    
    if not settings.vcs.webhook_enabled:
        raise HTTPException(status_code=501, detail="Webhooks not enabled")
    
    # Verify webhook token if secret is configured
    if settings.vcs.webhook_secret:
        if not x_gitlab_token:
            raise HTTPException(status_code=401, detail="Missing token header")
        
        if x_gitlab_token != settings.vcs.webhook_secret:
            logger.warning(f"Invalid webhook token for {repo_name}")
            raise HTTPException(status_code=401, detail="Invalid token")
    
    # Parse JSON payload
    try:
        payload = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Check if it's a push event
    if payload.get("object_kind") != "push":
        return {"message": "Event ignored (not a push event)", "status": "ignored"}
    
    # Trigger sync for this repository
    logger.info(f"GitLab webhook triggered sync for repository: {repo_name}")
    
    try:
        result = await vcs_manager.trigger_manual_sync(repo_name)
        return {
            "message": "Repository sync triggered",
            "status": "success",
            "repository": repo_name,
            "commit": payload.get("after", "unknown")
        }
    except Exception as e:
        logger.error(f"Webhook sync failed for {repo_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


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
