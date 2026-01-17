"""
SQLAlchemy database models for ansible-inspec server.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import JSON
from datetime import datetime
import uuid
from enum import Enum as PyEnum


Base = declarative_base()


class JobStatus(str, PyEnum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELED = "canceled"


class JobType(str, PyEnum):
    """Type of job execution"""
    RUN = "run"
    CHECK = "check"
    SCAN = "scan"


class UserDB(Base):
    """User table for authentication"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    roles = Column(JSONB)  # List of roles: ['admin', 'operator', 'viewer']
    tenant_id = Column(String(255), index=True)  # Azure AD tenant
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_login = Column(DateTime)
    active = Column(Boolean, default=True, nullable=False)


class JobTemplateDB(Base):
    """Job template table"""
    __tablename__ = "job_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    job_type = Column(SQLEnum(JobType), nullable=False, default=JobType.RUN)
    
    # InSpec-specific
    profile_path = Column(Text)
    reporter = Column(String(100))
    supermarket = Column(Boolean, default=False)
    
    # AAP-compatible
    playbook = Column(Text)
    project = Column(String(255))
    inventory = Column(Text)
    credentials = Column(JSONB)  # List of credential IDs
    
    # Execution options
    target = Column(Text)
    limit = Column(Text)
    tags = Column(JSONB)  # List of tags
    skip_tags = Column(JSONB)  # List of skip tags
    extra_vars = Column(JSONB)  # Dictionary of extra variables
    
    # Performance
    forks = Column(Integer, default=5)
    timeout = Column(Integer, default=0)
    verbosity = Column(Integer, default=0)
    
    # Advanced
    diff_mode = Column(Boolean, default=False)
    job_slice_count = Column(Integer, default=1)
    allow_simultaneous = Column(Boolean, default=False)
    use_fact_cache = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    modified_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), ForeignKey('users.username'))
    organization = Column(String(255), index=True)


class JobDB(Base):
    """Job execution record table"""
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_template_id = Column(UUID(as_uuid=True), ForeignKey('job_templates.id'), nullable=False, index=True)
    job_template_name = Column(String(255), nullable=False)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)
    
    started_at = Column(DateTime, index=True)
    finished_at = Column(DateTime)
    
    # Store large outputs in separate table or object storage in production
    stdout = Column(Text)
    stderr = Column(Text)
    
    result_summary = Column(JSONB)  # Compliance results summary
    extra_vars = Column(JSONB)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class WorkflowNodeDB(Base):
    """Workflow node table"""
    __tablename__ = "workflow_nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_template_id = Column(UUID(as_uuid=True), ForeignKey('workflow_templates.id'), nullable=False)
    identifier = Column(String(255), nullable=False)
    job_template_id = Column(UUID(as_uuid=True), ForeignKey('job_templates.id'))
    
    success_nodes = Column(JSONB)  # List of node IDs
    failure_nodes = Column(JSONB)  # List of node IDs
    always_nodes = Column(JSONB)  # List of node IDs


class WorkflowTemplateDB(Base):
    """Workflow template table"""
    __tablename__ = "workflow_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    modified_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class VCSCredentialDB(Base):
    """VCS credential table with encrypted fields"""
    __tablename__ = "vcs_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    vcs_type = Column(String(50), nullable=False)  # git, github, gitlab, bitbucket
    
    username = Column(String(255))
    password = Column(Text)  # Encrypted
    ssh_private_key = Column(Text)  # Encrypted
    token = Column(Text)  # Encrypted
    
    repository_url = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    encrypted = Column(Boolean, default=True, nullable=False)


class VCSRepositoryDB(Base):
    """VCS repository sync configuration"""
    __tablename__ = "vcs_repositories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    url = Column(Text, nullable=False)
    branch = Column(String(255), default="main")
    credential_id = Column(UUID(as_uuid=True), ForeignKey('vcs_credentials.id'))
    
    sync_enabled = Column(Boolean, default=True, nullable=False)
    poll_interval_minutes = Column(Integer, default=15)
    auto_import = Column(Boolean, default=True)  # Auto-create job templates
    
    last_sync_at = Column(DateTime)
    last_commit_hash = Column(String(255))
    sync_status = Column(String(50))  # success, failed, pending
    sync_error = Column(Text)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    modified_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
