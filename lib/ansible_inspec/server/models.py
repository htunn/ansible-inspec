"""
Data models for InSpec Execution Server

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
import uuid
import logging

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELED = "canceled"


class JobType(str, Enum):
    """Type of job execution"""
    RUN = "run"
    CHECK = "check"
    SCAN = "scan"


@dataclass
class JobTemplate:
    """
    Job Template for executing InSpec profiles and Ansible playbooks
    Provides reusable templates for compliance testing jobs
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    job_type: JobType = JobType.RUN
    
    # InSpec-specific fields
    profile_path: str = ""  # InSpec profile path or URL
    reporter: str = "cli json"  # InSpec reporter format
    supermarket: bool = False  # Use Chef Supermarket
    
    # AAP-compatible fields
    playbook: Optional[str] = None  # Playbook path (alternative to profile_path)
    project: Optional[str] = None  # Project identifier
    inventory: Optional[str] = None  # Inventory source
    credentials: List[str] = field(default_factory=list)  # Credential IDs
    
    # Execution options
    target: Optional[str] = None  # Target hosts pattern
    limit: Optional[str] = None  # Limit execution to hosts
    tags: List[str] = field(default_factory=list)  # Job tags
    skip_tags: List[str] = field(default_factory=list)  # Tags to skip
    extra_vars: Dict[str, Any] = field(default_factory=dict)  # Extra variables
    
    # Performance settings
    forks: int = 5  # Number of parallel processes
    timeout: int = 0  # Job timeout in seconds (0 = no timeout)
    verbosity: int = 0  # Verbosity level (0-4)
    
    # Advanced options
    diff_mode: bool = False  # Show diffs
    job_slice_count: int = 1  # Job slicing for parallel execution
    allow_simultaneous: bool = False  # Allow concurrent executions
    use_fact_cache: bool = False  # Use fact caching
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None  # User who created
    organization: Optional[str] = None  # Organization ID
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['modified_at'] = self.modified_at.isoformat()
        data['job_type'] = self.job_type.value
        # Ensure lists are serialized properly (handle None values)
        data['credentials'] = list(self.credentials) if self.credentials else []
        data['tags'] = list(self.tags) if self.tags else None
        data['skip_tags'] = list(self.skip_tags) if self.skip_tags else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobTemplate':
        """Create JobTemplate from dictionary"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'modified_at' in data and isinstance(data['modified_at'], str):
            data['modified_at'] = datetime.fromisoformat(data['modified_at'])
        if 'job_type' in data and isinstance(data['job_type'], str):
            data['job_type'] = JobType(data['job_type'])
        return cls(**data)


@dataclass
class Job:
    """
    Job execution record
    Tracks the execution of a job template
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_template_id: str = ""
    job_template_name: str = ""
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    stdout: str = ""
    stderr: str = ""
    result_summary: Dict[str, Any] = field(default_factory=dict)
    extra_vars: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['finished_at'] = self.finished_at.isoformat() if self.finished_at else None
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create Job from dictionary"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'started_at' in data and data['started_at'] and isinstance(data['started_at'], str):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if 'finished_at' in data and data['finished_at'] and isinstance(data['finished_at'], str):
            data['finished_at'] = datetime.fromisoformat(data['finished_at'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = JobStatus(data['status'])
        return cls(**data)


@dataclass
class WorkflowNode:
    """Node in a workflow template"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    identifier: str = ""
    job_template_id: Optional[str] = None
    success_nodes: List[str] = field(default_factory=list)
    failure_nodes: List[str] = field(default_factory=list)
    always_nodes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class WorkflowTemplate:
    """
    Workflow Template for executing multiple jobs in sequence
    Enables orchestration of complex compliance testing workflows
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    nodes: List[WorkflowNode] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['modified_at'] = self.modified_at.isoformat()
        data['nodes'] = [node.to_dict() if hasattr(node, 'to_dict') else node 
                        for node in self.nodes]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowTemplate':
        """Create WorkflowTemplate from dictionary"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'modified_at' in data and isinstance(data['modified_at'], str):
            data['modified_at'] = datetime.fromisoformat(data['modified_at'])
        if 'nodes' in data:
            data['nodes'] = [WorkflowNode(**node) if isinstance(node, dict) else node 
                           for node in data['nodes']]
        return cls(**data)


@dataclass
class VCSCredential:
    """
    VCS credential with encryption support
    Stores Git/GitHub/GitLab credentials for repository access
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    vcs_type: str = "git"  # git, github, gitlab, bitbucket
    username: Optional[str] = None
    password: Optional[str] = None  # Encrypted
    ssh_private_key: Optional[str] = None  # Encrypted
    token: Optional[str] = None  # Encrypted (PAT, API key)
    repository_url: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    encrypted: bool = False  # Flag indicating encryption status
    
    def encrypt_credentials(self, encryption_service):
        """Encrypt sensitive fields using EncryptionService"""
        if not self.encrypted:
            if self.password:
                self.password = encryption_service.encrypt(self.password)
            if self.ssh_private_key:
                self.ssh_private_key = encryption_service.encrypt(self.ssh_private_key)
            if self.token:
                self.token = encryption_service.encrypt(self.token)
            self.encrypted = True
    
    def decrypt_credentials(self, encryption_service):
        """Decrypt sensitive fields for use"""
        if self.encrypted:
            try:
                if self.password:
                    self.password = encryption_service.decrypt(self.password)
                if self.ssh_private_key:
                    self.ssh_private_key = encryption_service.decrypt(self.ssh_private_key)
                if self.token:
                    self.token = encryption_service.decrypt(self.token)
                # Keep encrypted=True to prevent double encryption
            except Exception as e:
                logger.error(f"Failed to decrypt credentials: {e}")
                raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VCSCredential':
        """Create VCSCredential from dictionary"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class User:
    """User model for authentication and authorization"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: Optional[str] = None
    name: Optional[str] = None
    roles: List[str] = field(default_factory=list)  # admin, operator, viewer
    tenant_id: Optional[str] = None  # Azure AD tenant
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_login'] = self.last_login.isoformat() if self.last_login else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from dictionary"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'last_login' in data and data['last_login'] and isinstance(data['last_login'], str):
            data['last_login'] = datetime.fromisoformat(data['last_login'])
        return cls(**data)
