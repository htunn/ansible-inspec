# API Documentation

Complete API reference for ansible-inspec library and CLI.

**Latest Update (v0.2.6):** Version bump with documentation improvements.

**v0.2.5:** Fixed critical missing import statements that caused NameError in v0.2.4. All translator files now properly import `re` module for variable name sanitization.

**v0.2.4:** Added missing error handling and result tracking to assertion tasks. All assert tasks now include `ignore_errors: True` and `register` fields, enabling full compliance scans without early abortion and proper result collection for reporting.

**v0.2.2:** Added dynamic custom resource mapper that automatically translates custom InSpec resources to native Ansible modules. Also fixed InSpec parser value extraction to properly handle operators in assertions.

**v0.2.1:** Fixed critical translator field mismatch that prevented native translation.

**v0.1.6:** Fixed critical converter bug that caused 99% control loss when converting profiles with quoted control IDs.

## Table of Contents

- [Installation](#installation)
- [CLI Reference](#cli-reference)
- [REST API Server](#rest-api-server)
  - [Authentication](#authentication-endpoints)
  - [Job Templates](#job-template-endpoints)
  - [Jobs](#job-endpoints)
  - [VCS Credentials](#vcs-credential-endpoints)
  - [VCS Repositories](#vcs-repository-endpoints)
  - [Webhooks](#webhook-endpoints)
  - [User Management](#user-management-endpoints)
  - [Monitoring](#monitoring-endpoints)
- [Python API](#python-api)
- [Core Classes](#core-classes)
- [Reporters](#reporters)
- [Converters](#converters)
- [Bug Fixes and Testing](#bug-fixes-and-testing)
- [Examples](#examples)

---

## Installation

### PyPI Installation

```bash
# Install latest version
pip install ansible-inspec

# Install specific version
pip install ansible-inspec==0.1.0

# Install with development dependencies
pip install ansible-inspec[dev]
```

### Docker Installation

```bash
# Pull latest image
docker pull htunnthuthu/ansible-inspec:latest

# Pull specific version
docker pull htunnthuthu/ansible-inspec:0.1.0

# Run container
docker run --rm htunnthuthu/ansible-inspec:latest --help
```

See [Docker Usage Guide](DOCKER.md) for detailed Docker instructions.

---

## CLI Reference

### Global Options

```bash
ansible-inspec [command] [options]
```

**Global Flags:**
- `--version` - Show version and exit
- `--license` - Show license information
- `--help, -h` - Show help message

### Commands

#### `exec` - Execute InSpec Profile

Run InSpec profiles on target systems using Ansible inventory.

```bash
ansible-inspec exec PROFILE_PATH [options]
```

**Arguments:**
- `PROFILE_PATH` - Path to InSpec profile directory

**Options:**
- `-t, --target TARGET` - Target specification (inventory file, host, or special target)
  - File path: `/path/to/inventory.yml`
  - Single host: `user@hostname`
  - Local: `local://`
  - Docker: `docker://container_name`
  
- `--reporter REPORTER` - Output format for results
  - Single: `json`, `html`, `junit`, `cli`
  - Multiple: `json:path.json html:path.html`
  - Default: `cli`
  
- `--output PATH` - Output file path for reports
- `--controls CONTROLS` - Comma-separated list of control IDs to run
- `--tags TAGS` - Comma-separated list of tags to filter controls

**Examples:**

```bash
# Run profile on local system
ansible-inspec exec my-profile --target local://

# Run on remote host via SSH
ansible-inspec exec my-profile --target user@hostname

# Run with Ansible inventory
ansible-inspec exec my-profile --target inventory.yml

# Generate JSON report
ansible-inspec exec my-profile --target local:// --reporter json --output report.json

# Multiple reporters
ansible-inspec exec my-profile --target local:// \
  --reporter "json:report.json html:report.html"

# Run specific controls
ansible-inspec exec my-profile --target local:// --controls "ssh-1,ssh-2"

# Filter by tags
ansible-inspec exec my-profile --target local:// --tags "critical,security"
```

#### `convert` - Convert InSpec Profile to Ansible Collection

Transform Ruby-based InSpec profiles into pure Ansible collections.

```bash
ansible-inspec convert PROFILE_PATH [options]
```

**Arguments:**
- `PROFILE_PATH` - Path to InSpec profile directory or Supermarket profile name

**Options:**
- `-o, --output-dir DIR` - Output directory for converted collection
  - Default: `./collections`
  
- `-n, --namespace NAME` - Ansible Galaxy namespace
  - Default: `compliance`
  
- `-c, --collection-name NAME` - Collection name
  - Default: Derived from profile name
  
- `--no-build` - Skip building the collection tarball
- `--force` - Overwrite existing collection
- `--include-callback` - Bundle compliance reporter callback plugin (enabled by default)

**Examples:**

```bash
# Basic conversion
ansible-inspec convert my-profile

# Custom namespace and collection name
ansible-inspec convert my-profile \
  --namespace myorg \
  --collection-name security_baseline

# Specify output directory
ansible-inspec convert my-profile --output-dir /path/to/collections

# Convert and build tarball
ansible-inspec convert my-profile --output-dir ./dist

# Download and convert from Chef Supermarket
ansible-inspec convert dev-sec/linux-baseline
```

#### `supermarket` - Interact with Chef Supermarket

Search and download compliance profiles from Chef Supermarket.

```bash
ansible-inspec supermarket SUBCOMMAND [options]
```

**Subcommands:**

##### `search` - Search for profiles

```bash
ansible-inspec supermarket search [QUERY] [options]
```

**Options:**
- `-l, --limit N` - Limit results (default: 20)
- `-s, --sort FIELD` - Sort by: `name`, `downloads`, `updated` (default: `updated`)

**Examples:**

```bash
# Search all profiles
ansible-inspec supermarket search

# Search for CIS profiles
ansible-inspec supermarket search CIS

# Search and limit results
ansible-inspec supermarket search linux --limit 10

# Sort by downloads
ansible-inspec supermarket search --sort downloads
```

##### `info` - Get profile details

```bash
ansible-inspec supermarket info PROFILE_NAME
```

**Examples:**

```bash
# Get info about a profile
ansible-inspec supermarket info dev-sec/linux-baseline

# Get info about CIS benchmark
ansible-inspec supermarket info cis/cis-ubuntu-20-04-server-level1
```

##### `download` - Download profile

```bash
ansible-inspec supermarket download PROFILE_NAME [options]
```

**Options:**
- `-o, --output-dir DIR` - Download destination (default: `./profiles`)

**Examples:**

```bash
# Download profile
ansible-inspec supermarket download dev-sec/linux-baseline

# Download to specific directory
ansible-inspec supermarket download dev-sec/linux-baseline \
  --output-dir /tmp/profiles
```

---

## REST API Server

The ansible-inspec server provides a production-ready REST API for managing compliance testing workflows, VCS integration, and user authentication.

### Base URL

```
http://localhost:8080/api/v1
```

### Starting the Server

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Using Python directly
uvicorn ansible_inspec.server.api:app --host 0.0.0.0 --port 8080

# With environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/ansibleinspec"
export JWT_SECRET="your-secret-key"
export ENCRYPTION_KEY="your-encryption-key"
uvicorn ansible_inspec.server.api:app --reload
```

### Authentication

The API supports two authentication methods:
1. **Azure AD OAuth2** - Enterprise SSO (recommended for production)
2. **Password-based** - Local username/password authentication

All endpoints (except health check and auth endpoints) require authentication via JWT bearer tokens.

**Authorization Header:**
```
Authorization: Bearer <jwt_token>
```

### Role-Based Access Control (RBAC)

- **admin** - Full access to all endpoints including user management
- **operator** - Can manage job templates, jobs, and VCS repositories
- **viewer** - Read-only access to jobs and templates

---

### Authentication Endpoints

#### GET /health

Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "version": "0.2.6",
  "storage_backend": "database",
  "database": "connected",
  "auth_enabled": true,
  "vcs_enabled": true
}
```

#### GET /api/v1

API information endpoint.

**Response:**
```json
{
  "name": "Ansible-InSpec API",
  "version": "0.2.6",
  "endpoints": {
    "job_templates": "/api/v1/job-templates",
    "jobs": "/api/v1/jobs",
    "workflows": "/api/v1/workflows",
    "users": "/api/v1/users",
    "vcs_credentials": "/api/v1/vcs/credentials",
    "vcs_repositories": "/api/v1/vcs/repositories",
    "auth": "/api/v1/auth"
  }
}
```

#### GET /api/v1/auth/login

Redirect to Azure AD OAuth2 login page.

**Response:**
- 302 Redirect to Microsoft login page

#### POST /api/v1/auth/password-login

Login with username and password.

**Request Body:**
```json
{
  "username": "admin",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user-123",
    "username": "admin",
    "email": "admin@example.com",
    "roles": ["admin"]
  }
}
```

**Status Codes:**
- 200: Success
- 401: Invalid credentials

#### GET /api/v1/auth/callback

OAuth2 callback endpoint for Azure AD authentication.

**Query Parameters:**
- `code` - Authorization code from Azure AD
- `state` - State parameter for CSRF protection

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### GET /api/v1/auth/me

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "user-123",
  "username": "admin",
  "email": "admin@example.com",
  "name": "Administrator",
  "roles": ["admin"],
  "active": true,
  "last_login": "2026-02-11T10:30:00Z"
}
```

**Status Codes:**
- 200: Success
- 401: Unauthorized

#### POST /api/v1/auth/logout

Logout current user and invalidate token.

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

---

### Job Template Endpoints

#### GET /api/v1/job-templates

List all job templates.

**Query Parameters:**
- `limit` (int, optional): Maximum results (default: 100)
- `offset` (int, optional): Pagination offset (default: 0)

**Required Role:** viewer

**Response:**
```json
{
  "count": 2,
  "results": [
    {
      "id": "template-123",
      "name": "linux-baseline",
      "description": "DevSec Linux Baseline",
      "profile": "dev-sec/linux-baseline",
      "extra_vars": {},
      "vcs_repo_id": null,
      "created_at": "2026-02-11T10:00:00Z",
      "updated_at": "2026-02-11T10:00:00Z"
    }
  ]
}
```

#### POST /api/v1/job-templates

Create a new job template.

**Required Role:** operator

**Request Body:**
```json
{
  "name": "linux-baseline",
  "description": "DevSec Linux Baseline compliance check",
  "profile": "dev-sec/linux-baseline",
  "extra_vars": {
    "check_level": "critical"
  },
  "vcs_repo_id": "repo-456",
  "vcs_path": "profiles/linux-baseline",
  "vcs_sync": true
}
```

**Response:**
```json
{
  "id": "template-123",
  "name": "linux-baseline",
  "description": "DevSec Linux Baseline compliance check",
  "profile": "dev-sec/linux-baseline",
  "extra_vars": {"check_level": "critical"},
  "created_at": "2026-02-11T10:00:00Z"
}
```

**Status Codes:**
- 201: Created
- 400: Invalid input
- 401: Unauthorized
- 403: Forbidden

#### GET /api/v1/job-templates/{template_id}

Get a specific job template by ID.

**Required Role:** viewer

**Response:**
```json
{
  "id": "template-123",
  "name": "linux-baseline",
  "description": "DevSec Linux Baseline",
  "profile": "dev-sec/linux-baseline",
  "extra_vars": {},
  "vcs_repo_id": null,
  "vcs_path": null,
  "vcs_sync": false,
  "created_at": "2026-02-11T10:00:00Z",
  "updated_at": "2026-02-11T10:00:00Z"
}
```

**Status Codes:**
- 200: Success
- 404: Template not found

#### PUT /api/v1/job-templates/{template_id}

Update a job template.

**Required Role:** operator

**Request Body:**
```json
{
  "name": "updated-name",
  "description": "Updated description",
  "profile": "new-profile-path",
  "extra_vars": {"new_var": "value"}
}
```

**Response:**
```json
{
  "id": "template-123",
  "name": "updated-name",
  "description": "Updated description",
  "updated_at": "2026-02-11T11:00:00Z"
}
```

**Status Codes:**
- 200: Success
- 404: Template not found
- 400: Invalid input

#### DELETE /api/v1/job-templates/{template_id}

Delete a job template.

**Required Role:** admin

**Status Codes:**
- 204: No Content (success)
- 404: Template not found

#### POST /api/v1/job-templates/{template_id}/launch

Launch a job from a template.

**Required Role:** operator

**Request Body:**
```json
{
  "target": "production-servers",
  "extra_vars": {
    "override_var": "value"
  }
}
```

**Response:**
```json
{
  "id": "job-789",
  "template_id": "template-123",
  "status": "running",
  "created_at": "2026-02-11T11:00:00Z"
}
```

**Status Codes:**
- 201: Created
- 404: Template not found

---

### Job Endpoints

#### GET /api/v1/jobs

List all jobs with optional filtering.

**Query Parameters:**
- `limit` (int): Maximum results (default: 100)
- `offset` (int): Pagination offset (default: 0)
- `status` (string): Filter by status (pending, running, completed, failed)
- `template_id` (string): Filter by template ID

**Required Role:** viewer

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": "job-789",
      "template_id": "template-123",
      "status": "completed",
      "target": "production-servers",
      "started_at": "2026-02-11T11:00:00Z",
      "finished_at": "2026-02-11T11:05:00Z",
      "duration_seconds": 300,
      "controls_passed": 45,
      "controls_failed": 3,
      "controls_total": 48
    }
  ]
}
```

#### POST /api/v1/jobs

Create and execute a new job.

**Required Role:** operator

**Request Body:**
```json
{
  "template_id": "template-123",
  "target": "production-servers",
  "extra_vars": {
    "custom_var": "value"
  }
}
```

**Response:**
```json
{
  "id": "job-789",
  "template_id": "template-123",
  "status": "running",
  "created_at": "2026-02-11T11:00:00Z"
}
```

**Status Codes:**
- 201: Created
- 404: Template not found

#### GET /api/v1/jobs/{job_id}

Get detailed job information and results.

**Required Role:** viewer

**Response:**
```json
{
  "id": "job-789",
  "template_id": "template-123",
  "template_name": "linux-baseline",
  "status": "completed",
  "target": "production-servers",
  "started_at": "2026-02-11T11:00:00Z",
  "finished_at": "2026-02-11T11:05:00Z",
  "duration_seconds": 300,
  "result": {
    "controls_passed": 45,
    "controls_failed": 3,
    "controls_skipped": 0,
    "controls_total": 48,
    "compliance_percentage": 93.75,
    "controls": [
      {
        "id": "ssh-1",
        "title": "SSH Protocol Version",
        "status": "passed",
        "impact": 1.0,
        "results": []
      }
    ]
  }
}
```

**Status Codes:**
- 200: Success
- 404: Job not found

---

### VCS Credential Endpoints

#### POST /api/v1/vcs/credentials

Create a new VCS credential for repository authentication.

**Required Role:** admin

**Request Body:**
```json
{
  "name": "github-token",
  "vcs_type": "github",
  "token": "ghp_xxxxxxxxxxxx",
  "repository_url": "https://github.com/org/repo"
}
```

**Alternative with SSH:**
```json
{
  "name": "gitlab-ssh",
  "vcs_type": "gitlab",
  "ssh_private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "repository_url": "git@gitlab.com:org/repo.git"
}
```

**Alternative with username/password:**
```json
{
  "name": "bitbucket-creds",
  "vcs_type": "bitbucket",
  "username": "user@example.com",
  "password": "app-password",
  "repository_url": "https://bitbucket.org/org/repo"
}
```

**Response:**
```json
{
  "id": "cred-456",
  "name": "github-token",
  "vcs_type": "github",
  "username": null
}
```

**Note:** Credentials are encrypted at rest using Fernet symmetric encryption.

**Status Codes:**
- 201: Created
- 501: Encryption not configured

#### GET /api/v1/vcs/credentials

List all VCS credentials (without showing sensitive data).

**Required Role:** operator

**Response:**
```json
{
  "count": 2,
  "results": [
    {
      "id": "cred-456",
      "name": "github-token", "vcs_type": "github",
      "username": null
    },
    {
      "id": "cred-789",
      "name": "gitlab-ssh",
      "vcs_type": "gitlab",
      "username": "git"
    }
  ]
}
```

#### DELETE /api/v1/vcs/credentials/{credential_id}

Delete a VCS credential.

**Required Role:** admin

**Status Codes:**
- 204: No Content (success)
- 404: Credential not found

---

### VCS Repository Endpoints

#### POST /api/v1/vcs/repositories

Register a VCS repository for automatic profile synchronization.

**Required Role:** admin

**Request Body:**
```json
{
  "name": "compliance-profiles",
  "url": "https://github.com/org/compliance-profiles.git",
  "branch": "main",
  "credential_id": "cred-456",
  "poll_interval": 300,
  "profile_path": "inspec",
  "auto_import": true
}
```

**Response:**
```json
{
  "id": "repo-123",
  "name": "compliance-profiles",
  "url": "https://github.com/org/compliance-profiles.git",
  "branch": "main",
  "auto_import": true
}
```

**Status Codes:**
- 201: Created
- 400: Repository already exists
- 501: VCS not enabled

#### GET /api/v1/vcs/repositories

List all registered VCS repositories.

**Required Role:** operator

**Response:**
```json
{
  "count": 1,
  "results": [
    {
      "id": "repo-123",
      "name": "compliance-profiles",
      "url": "https://github.com/org/compliance-profiles.git",
      "branch": "main",
      "sync_status": "completed",
      "last_sync_at": "2026-02-11T10:00:00Z",
      "last_commit": "abc123def456",
      "auto_import": true
    }
  ]
}
```

#### POST /api/v1/vcs/repositories/{repo_name}/sync

Manually trigger repository synchronization.

**Required Role:** operator

**Response:**
```json
{
  "status": "success",
  "message": "Repository sync triggered",
  "sync_id": "sync-789"
}
```

**Status Codes:**
- 200: Success
- 404: Repository not found
- 501: VCS not enabled

#### DELETE /api/v1/vcs/repositories/{repo_name}

Delete a VCS repository configuration (does not delete synced profiles).

**Required Role:** admin

**Status Codes:**
- 204: No Content (success)
- 404: Repository not found

#### GET /api/v1/vcs/repositories/{repo_name}/history

Get synchronization history for a repository.

**Query Parameters:**
- `limit` (int): Maximum results (default: 50)

**Required Role:** viewer

**Response:**
```json
{
  "repository": "compliance-profiles",
  "count": 10,
  "results": [
    {
      "id": "sync-789",
      "syncStartedAt": "2026-02-11T10:00:00Z",
      "syncCompletedAt": "2026-02-11T10:02:00Z",
      "status": "completed",
      "commitHash": "abc123def456",
      "profilesDiscovered": 5,
      "templatesCreated": 5,
      "errors": null,
      "triggeredBy": "admin",
      "triggerType": "manual",
      "duration_seconds": 120
    }
  ]
}
```

#### GET /api/v1/vcs/repositories/{repo_name}/files

List all files in a synced repository.

**Required Role:** viewer

**Response:**
```json
{
  "repository": "compliance-profiles",
  "count": 25,
  "files": [
    "README.md",
    "inspec/linux-baseline/inspec.yml",
    "inspec/linux-baseline/controls/01_baseline.rb",
    "inspec/windows-baseline/inspec.yml"
  ]
}
```

**Status Codes:**
- 200: Success
- 400: Repository not synced yet
- 404: Repository not found

#### GET /api/v1/vcs/repositories/{repo_name}/files/{file_path}

Get content of a specific file from a synced repository.

**Required Role:** viewer

**Response:**
```json
{
  "repository": "compliance-profiles",
  "file_path": "inspec/linux-baseline/inspec.yml",
  "content": "name: linux-baseline\ntitle: DevSec Linux Baseline\nversion: 2.8.0\n...",
  "size": 512
}
```

**Status Codes:**
- 200: Success
- 400: Invalid file path or binary file
- 404: File not found

---

### Webhook Endpoints

#### POST /api/v1/webhooks/github/{repo_name}

GitHub webhook handler for push events.

**Headers:**
```
X-Hub-Signature-256: sha256=<signature>
X-GitHub-Event: push
```

**Request Body:** GitHub webhook payload

**Response:**
```json
{
  "message": "Repository sync triggered",
  "status": "success",
  "repository": "compliance-profiles",
  "commit": "abc123def456"
}
```

**Status Codes:**
- 200: Success
- 401: Invalid signature
- 501: Webhooks not enabled

**Configuration:**
1. Go to repository Settings → Webhooks
2. Add webhook URL: `http://your-server:8080/api/v1/webhooks/github/{repo_name}`
3. Content type: `application/json`
4. Secret: Set `WEBHOOK_SECRET` environment variable
5. Events: Select "Just the push event"

#### POST /api/v1/webhooks/gitlab/{repo_name}

GitLab webhook handler for push events.

**Headers:**
```
X-Gitlab-Token: <secret>
```

**Request Body:** GitLab webhook payload

**Response:**
```json
{
  "message": "Repository sync triggered",
  "status": "success",
  "repository": "compliance-profiles",
  "commit": "abc123def456"
}
```

**Status Codes:**
- 200: Success
- 401: Invalid token
- 501: Webhooks not enabled

**Configuration:**
1. Go to repository Settings → Webhooks
2. Add webhook URL: `http://your-server:8080/api/v1/webhooks/gitlab/{repo_name}`
3. Secret token: Set `WEBHOOK_SECRET` environment variable
4. Trigger: Select "Push events"

---

### User Management Endpoints

#### GET /api/v1/users

List all users (admin only).

**Required Role:** admin

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": "user-123",
      "username": "admin",
      "email": "admin@example.com",
      "name": "Administrator",
      "roles": ["admin"],
      "active": true,
      "last_login": "2026-02-11T10:00:00Z"
    }
  ]
}
```

#### PUT /api/v1/users/{user_id}

Update user roles and status (admin only).

**Required Role:** admin

**Request Body:**
```json
{
  "roles": ["operator", "viewer"],
  "active": true
}
```

**Response:**
```json
{
  "id": "user-123",
  "username": "operator1",
  "roles": ["operator", "viewer"],
  "active": true
}
```

**Status Codes:**
- 200: Success
- 404: User not found

---

### Monitoring Endpoints

#### GET /api/v1/storage/validation-status

Get hybrid storage validation status (admin only, hybrid mode only).

**Required Role:** admin

**Response:**
```json
{
  "mode": "validation",
  "validation_days_remaining": 25,
  "validation_period_days": 30,
  "auto_cutover_enabled": true,
  "operations_validated": 1250,
  "validation_failures": 0,
  "last_validation_check": "2026-02-11T10:00:00Z"
}
```

**Status Codes:**
- 200: Success
- 400: Not using hybrid storage

#### GET /metrics

Prometheus metrics endpoint (no authentication required).

**Response:** Prometheus text format

```
# HELP ansible_inspec_storage_operations_total Total number of storage operations
# TYPE ansible_inspec_storage_operations_total counter
ansible_inspec_storage_operations_total{backend="database",operation="save"} 145
ansible_inspec_storage_operations_total{backend="database",operation="get"} 892

# HELP ansible_inspec_storage_operation_duration_seconds Storage operation duration
# TYPE ansible_inspec_storage_operation_duration_seconds histogram
ansible_inspec_storage_operation_duration_seconds_bucket{backend="database",operation="save",le="0.1"} 142

# HELP ansible_inspec_auth_requests_total Total authentication requests
# TYPE ansible_inspec_auth_requests_total counter
ansible_inspec_auth_requests_total{provider="azure_ad",status="success"} 45
```

---

### API Examples

#### Complete Workflow Example

```bash
# 1. Login
curl -X POST http://localhost:8080/api/v1/auth/password-login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"secret"}' | jq -r '.access_token' > token.txt

TOKEN=$(cat token.txt)

# 2. Create VCS credential
curl -X POST http://localhost:8080/api/v1/vcs/credentials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "github-token",
    "vcs_type": "github",
    "token": "ghp_xxxxxxxxxxxx"
  }'

# 3. Register repository
curl -X POST http://localhost:8080/api/v1/vcs/repositories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "compliance-profiles",
    "url": "https://github.com/org/compliance-profiles.git",
    "branch": "main",
    "credential_id": "cred-456",
    "auto_import": true
  }'

# 4. Trigger manual sync
curl -X POST http://localhost:8080/api/v1/vcs/repositories/compliance-profiles/sync \
  -H "Authorization: Bearer $TOKEN"

# 5. List job templates (auto-created from sync)
curl -X GET http://localhost:8080/api/v1/job-templates \
  -H "Authorization: Bearer $TOKEN"

# 6. Launch job
curl -X POST http://localhost:8080/api/v1/job-templates/template-123/launch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "production-servers",
    "extra_vars": {}
  }'

# 7. Check job status
curl -X GET http://localhost:8080/api/v1/jobs/job-789 \
  -H "Authorization: Bearer $TOKEN"

# 8. View job results
curl -X GET http://localhost:8080/api/v1/jobs/job-789 \
  -H "Authorization: Bearer $TOKEN" | jq '.result'
```

#### Python Client Example

```python
import requests

class AnsibleInSpecClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.token = None
        self.login(username, password)
    
    def login(self, username, password):
        """Login and store token"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/password-login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
    
    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    def create_job_template(self, name, profile, description=""):
        """Create a job template"""
        response = requests.post(
            f"{self.base_url}/api/v1/job-templates",
            headers=self._headers(),
            json={
                "name": name,
                "profile": profile,
                "description": description
            }
        )
        response.raise_for_status()
        return response.json()
    
    def launch_job(self, template_id, target="localhost"):
        """Launch a job from template"""
        response = requests.post(
            f"{self.base_url}/api/v1/job-templates/{template_id}/launch",
            headers=self._headers(),
            json={"target": target}
        )
        response.raise_for_status()
        return response.json()
    
    def get_job(self, job_id):
        """Get job details"""
        response = requests.get(
            f"{self.base_url}/api/v1/jobs/{job_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

# Usage
client = AnsibleInSpecClient(
    "http://localhost:8080",
    username="admin",
    password="secret"
)

# Create template
template = client.create_job_template(
    name="linux-baseline",
    profile="dev-sec/linux-baseline",
    description="DevSec Linux Baseline"
)

# Launch job
job = client.launch_job(template["id"], target="production-servers")

# Check results
result = client.get_job(job["id"])
print(f"Status: {result['status']}")
print(f"Compliance: {result['result']['compliance_percentage']}%")
```

---

## Python API

### Basic Usage

```python
from ansible_inspec import Runner, ProfileConverter
from ansible_inspec.core import ExecutionConfig

# Execute InSpec profile
config = ExecutionConfig(
    profile_path="/path/to/profile",
    target="local://",
    reporter="json",
    output_path="report.json"
)

runner = Runner(config)
result = runner.run()

# Save reports
result.save("report.json", format="json")
result.save("report.html", format="html")

# Convert profile to Ansible collection
converter = ProfileConverter(
    profile_path="/path/to/profile",
    output_dir="./collections",
    namespace="myorg",
    collection_name="security"
)

collection_path = converter.convert()
print(f"Collection created at: {collection_path}")
```

---

## Core Classes

### ExecutionConfig

Configuration for InSpec profile execution.

```python
from ansible_inspec.core import ExecutionConfig

config = ExecutionConfig(
    profile_path: str,              # Path to InSpec profile
    target: str,                    # Target (inventory, host, or special)
    reporter: str = "cli",          # Output format
    output_path: Optional[str] = None,  # Output file path
    controls: Optional[List[str]] = None,  # Control IDs to run
    tags: Optional[List[str]] = None       # Tags to filter
)
```

**Attributes:**
- `profile_path` (str): Path to InSpec profile directory
- `target` (str): Target specification
- `reporter` (str): Output format (json, html, junit, cli)
- `output_path` (Optional[str]): Path for report output
- `controls` (Optional[List[str]]): List of control IDs
- `tags` (Optional[List[str]]): List of tags to filter

### ExecutionResult

Results from InSpec profile execution.

```python
from ansible_inspec.core import ExecutionResult

result = runner.run()  # Returns ExecutionResult

# Properties
result.success         # bool: Overall success
result.exit_code       # int: Exit code
result.output          # str: Raw output
result.error           # Optional[str]: Error message
result.controls_passed # int: Number of passed controls
result.controls_failed # int: Number of failed controls
result.controls_total  # int: Total controls

# Methods
result.to_json() -> str
result.to_html() -> str
result.to_junit() -> str
result.save(path: str, format: str = "json") -> None
```

**Example:**

```python
# Check results
if result.success:
    print(f"All {result.controls_total} controls passed!")
else:
    print(f"Failed: {result.controls_failed}/{result.controls_total}")
    
# Generate reports
json_data = result.to_json()
html_report = result.to_html()

# Save to files
result.save("compliance-report.json", format="json")
result.save("compliance-report.html", format="html")
result.save("compliance-report.xml", format="junit")
```

### Runner

Execute InSpec profiles.

```python
from ansible_inspec import Runner
from ansible_inspec.core import ExecutionConfig

# Create runner
config = ExecutionConfig(profile_path="./my-profile", target="local://")
runner = Runner(config)

# Execute
result = runner.run()

# Access results
print(f"Success: {result.success}")
print(f"Controls: {result.controls_passed}/{result.controls_total}")
```

**Methods:**
- `run() -> ExecutionResult` - Execute the profile and return results

### ProfileConverter

Convert InSpec profiles to Ansible collections.

```python
from ansible_inspec import ProfileConverter

converter = ProfileConverter(
    profile_path: str,
    output_dir: str = "./collections",
    namespace: str = "compliance",
    collection_name: Optional[str] = None,
    force: bool = False,
    build: bool = True
)

# Convert profile
collection_path = converter.convert()
print(f"Collection: {collection_path}")
```

**Parameters:**
- `profile_path` (str): Path to InSpec profile
- `output_dir` (str): Output directory for collection
- `namespace` (str): Ansible Galaxy namespace
- `collection_name` (Optional[str]): Collection name (auto-generated if None)
- `force` (bool): Overwrite existing collection
- `build` (bool): Build collection tarball

**Methods:**
- `convert() -> str` - Convert profile, returns collection path
- `build() -> str` - Build collection tarball, returns tarball path

**Example:**

```python
# Convert with custom settings
converter = ProfileConverter(
    profile_path="/path/to/cis-benchmark",
    output_dir="./ansible-collections",
    namespace="security",
    collection_name="cis_ubuntu_20_04",
    force=True,
    build=True
)

try:
    collection_path = converter.convert()
    print(f"✓ Collection created: {collection_path}")
    
    # Build tarball
    tarball = converter.build()
    print(f"✓ Tarball: {tarball}")
except Exception as e:
    print(f"✗ Conversion failed: {e}")
```

---

## Reporters

### InSpec JSON Reporter

Generate InSpec-compatible JSON reports.

```python
from ansible_inspec.reporters import InSpecJSONReport, InSpecControl, InSpecProfile

# Create report
report = InSpecJSONReport(version="5.22.0")

# Add profile
profile = InSpecProfile(
    name="my-profile",
    title="My Security Profile",
    version="1.0.0",
    summary="Security baseline",
    controls=[]
)
report.profiles.append(profile)

# Add control
control = InSpecControl(
    id="ctrl-1",
    title="SSH Configuration",
    desc="Ensure SSH is configured securely",
    impact=0.7,
    tags={},
    code="describe file('/etc/ssh/sshd_config') { it { should exist } }",
    source_location={"ref": "controls/ssh.rb", "line": 1},
    results=[{
        "status": "passed",
        "code_desc": "File /etc/ssh/sshd_config should exist",
        "run_time": 0.002
    }]
)
profile.controls.append(control)

# Generate JSON
json_output = report.to_json(indent=2)
print(json_output)

# Save to file
report.save("/path/to/report.json")
```

**Classes:**

#### InSpecJSONReport

Main report container.

**Attributes:**
- `version` (str): InSpec version
- `profiles` (List[InSpecProfile]): List of profiles
- `platform` (InSpecPlatform): Platform information
- `statistics` (InSpecStatistics): Execution statistics
- `errors` (List[str]): Execution errors

**Methods:**
- `to_dict() -> Dict` - Convert to dictionary
- `to_json(indent: int = 2) -> str` - Generate JSON string
- `save(path: str, indent: int = 2) -> None` - Save to file

#### InSpecControl

Represents a single control.

**Attributes:**
- `id` (str): Control ID
- `title` (str): Control title
- `desc` (str): Description
- `impact` (float): Impact score (0.0 - 1.0)
- `tags` (Dict): Tags
- `code` (str): Control code
- `source_location` (Dict): Source file location
- `results` (List[Dict]): Test results

#### InSpecProfile

Represents an InSpec profile.

**Attributes:**
- `name` (str): Profile name
- `title` (str): Profile title
- `version` (str): Version
- `summary` (str): Summary
- `controls` (List[InSpecControl]): Controls

#### InSpecPlatform

Platform information.

**Attributes:**
- `name` (str): Platform name
- `release` (str): Release version
- `target_id` (str): Target identifier

#### InSpecStatistics

Execution statistics.

**Attributes:**
- `duration` (float): Execution duration in seconds
- `controls` (Dict): Control counts

### HTML Reporter

Generate interactive HTML reports.

```python
from ansible_inspec.core import ExecutionResult

result = runner.run()

# Generate HTML
html_report = result.to_html()

# Save HTML report
result.save("compliance-report.html", format="html")
```

**HTML Features:**
- Interactive dashboard
- Control filtering
- Pass/fail statistics
- Color-coded results
- Execution error section
- Responsive design

### JUnit Reporter

Generate JUnit XML for CI/CD integration.

```python
# Generate JUnit XML
junit_xml = result.to_junit()

# Save for CI/CD
result.save("test-results.xml", format="junit")
```

**JUnit Features:**
- Test suite per profile
- Test case per control
- Failure details
- Execution timing
- CI/CD compatible

---

## Converters

### Profile Conversion

The converter translates InSpec profiles (Ruby DSL) into Ansible collections with native tasks.

**Key Features (v0.1.6):**
- **Fixed Critical Bug**: Control ID regex now properly handles quotes in control IDs
  - Previous versions failed on CIS benchmark controls like `"1.1.1 (L1) Ensure 'password history' is set"`
  - Now successfully converts all 358 controls instead of only 4 (99% improvement)
- **Sanitized Variable Names**: Automatically converts control IDs to valid Ansible variable names
  - Example: `"2.2.27 (L1) Ensure..."` → `"inspec_2_2_27_L1_Ensure"`
- **Custom Resources**: Detects and converts InSpec custom resources to Ansible modules
- **Native Modules**: Prefers Ansible native modules when available (file, service, package, etc.)

### Profile Structure Analysis

```python
from ansible_inspec.converter import ProfileConverter, InSpecControlParser

# Parse InSpec controls with proper quote handling
control_code = '''
control "1.1.1 (L1) Ensure 'Enforce password history' is set to '7 password(s)'" do
  impact 1.0
  title "Password History"
  desc "Enforce password history"
  
  describe registry_key('HKEY_LOCAL_MACHINE\\...') do
    its('PasswordHistorySize') { should cmp >= 7 }
  end
end
'''

parser = InSpecControlParser(control_code)
controls = parser.parse()

# Successfully extracts full control ID with quotes
assert controls[0]['id'] == "1.1.1 (L1) Ensure 'Enforce password history' is set to '7 password(s)'"

# Analyze full profile
converter = ProfileConverter(profile_path="./cis-benchmark")
profile_info = converter.analyze()

print(f"Profile: {profile_info['name']}")
print(f"Controls: {len(profile_info['controls'])}")  # Now gets all controls!
print(f"Custom Resources: {profile_info['custom_resources']}")
```

### Control ID Handling

The converter properly handles complex control IDs from compliance frameworks:

```python
from ansible_inspec.converter import sanitize_variable_name

# Real-world CIS benchmark control IDs
control_ids = [
    "1.1.1 (L1) Ensure 'Enforce password history' is set to '7 password(s)'",
    "2.2.27 (L1) Ensure 'Enable computer and user accounts' is set",
    "18.9.108.2.1 (L2) Ensure 'Configure registry policy processing' is set"
]

for control_id in control_ids:
    var_name = sanitize_variable_name(control_id)
    print(f"{control_id}\n  → {var_name}\n")

# Output:
# 1.1.1 (L1) Ensure 'Enforce password history' is set to '7 password(s)'
#   → inspec_1_1_1_L1_Ensure_Enforce_password_history_is_set_to_7_password_s
#
# 2.2.27 (L1) Ensure 'Enable computer and user accounts' is set
#   → inspec_2_2_27_L1_Ensure_Enable_computer_and_user_accounts_is_set
```

### Custom Resource Handling

The converter automatically detects and converts custom InSpec resources:

```python
# InSpec custom resource (libraries/application_config.rb)
class ApplicationConfig < Inspec.resource(1)
  name 'application_config'
  
  def value(key)
    config[key]
  end
end

# Converted to Ansible module (plugins/modules/application_config.py)
def main():
    module = AnsibleModule(argument_spec={'key': {'type': 'str'}})
    # ... implementation
```

### Conversion Workflow

```python
from ansible_inspec import ProfileConverter

# Step 1: Initialize converter
converter = ProfileConverter(
    profile_path="./profiles/cis-ubuntu",
    output_dir="./collections",
    namespace="security",
    collection_name="cis_ubuntu"
)

# Step 2: Convert profile
collection_path = converter.convert()
# Creates: ./collections/ansible_collections/security/cis_ubuntu/

# Step 3: Collection structure
# ansible_collections/security/cis_ubuntu/
# ├── galaxy.yml                    # Collection metadata
# ├── README.md                     # Documentation
# ├── ansible.cfg                   # Auto-reporting config
# ├── roles/                        # Converted controls
# │   ├── filesystem/
# │   ├── network/
# │   └── ...
# ├── playbooks/                    # Ready-to-use playbooks
# │   └── compliance_check.yml
# ├── plugins/
# │   ├── modules/                  # Custom resources
# │   └── callback/                 # Reporter plugin
# │       └── compliance_reporter.py
# └── docs/                         # Documentation

# Step 4: Build tarball
tarball = converter.build()
# Creates: security-cis_ubuntu-1.0.0.tar.gz

# Step 5: Install collection
# ansible-galaxy collection install security-cis_ubuntu-1.0.0.tar.gz
```

---

## Bug Fixes and Testing

### Bug #1: Control ID Regex Pattern Fix (v0.1.6)

**Severity:** CRITICAL (P0)  
**Status:** Fixed  
**Date:** 2026-01-11

#### Problem
The InSpec profile converter was only converting 4 out of 358 controls (99% loss) from CIS benchmark profiles. The root cause was a regex pattern that failed to match control IDs containing single quotes.

#### Root Cause
```python
# Problematic pattern (v0.1.5 and earlier)
CONTROL_PATTERN = re.compile(
    r"control\s+['\"]([^'\"]+)['\"]\s+do(.*?)^end",
    re.MULTILINE | re.DOTALL
)
```

The character class `[^'\"]+` means "match any character EXCEPT quotes", causing the pattern to stop at the first quote inside the control ID:

```ruby
control "1.1.1 (L1) Ensure 'password history' is set" do
#       ^------- Match stops here -------^  <-- Only captures up to first '
```

#### Solution
```python
# Fixed pattern (v0.1.6+)
CONTROL_PATTERN = re.compile(
    r"control\s+(['\"])(.+?)\1\s+do(.*?)^end",
    re.MULTILINE | re.DOTALL
)
```

Uses backreference `\1` to match the same quote type that opened the string:
- `(['\"])` - Capture opening quote (group 1)
- `(.+?)` - Capture control ID with any characters (group 2)
- `\1` - Match the SAME quote that opened the string
- Control ID moved from group(1) to group(2)
- Control body moved from group(2) to group(3)

#### Impact
- **Before:** 4 controls converted (1.1% success rate)
- **After:** 358 controls converted (100% success rate)
- **Improvement:** 354 additional controls (8,850% increase)

#### Testing
The fix includes comprehensive regression tests:

```python
# Test 1: Control ID with single quotes
def test_parse_control_with_quotes_in_id():
    control_code = '''
control "1.1.1 (L1) Ensure 'Enforce password history' is set to '7 password(s)'" do
  impact 1.0
  describe file('/etc/passwd') do
    it { should exist }
  end
end
    '''
    parser = InSpecControlParser(control_code)
    controls = parser.parse()
    
    assert len(controls) == 1
    assert controls[0]['id'] == "1.1.1 (L1) Ensure 'Enforce password history' is set to '7 password(s)'"

# Test 2: Mixed quote types
def test_parse_control_with_double_quotes_in_single_quoted_id():
    control_code = '''
control 'test-id-with-"double"-quotes' do
  impact 0.5
  describe file('/test') do
    it { should exist }
  end
end
    '''
    parser = InSpecControlParser(control_code)
    controls = parser.parse()
    
    assert controls[0]['id'] == 'test-id-with-"double"-quotes'

# Test 3: Multiple controls with quotes
def test_parse_multiple_controls_with_quotes():
    # Tests parsing of 3 controls with various quote patterns
    # Ensures all controls are captured correctly
```

#### Verification
To verify the fix works on your profiles:

```bash
# Clone repository
git clone https://github.com/Htunn/ansible-inspec
cd ansible-inspec

# Install with latest fix
pip install -e .

# Run tests
pytest tests/test_converter.py::TestInSpecControlParser -v

# Test on real CIS benchmark profile
ansible-inspec convert path/to/cis-profile -o /tmp/test-output

# Count converted controls
grep -c "^control " path/to/cis-profile/controls/*.rb
# Should match number of tasks in converted collection
```

#### References
- Bug Report: [Bug #1 Report](../CHANGELOG.md#016---2026-01-11)
- Fixed Files: `lib/ansible_inspec/converter.py` (lines 169-172, 196-198)
- Test Coverage: `tests/test_converter.py` (lines 178-285)

---

## Examples

### Example 1: Local Compliance Check

```python
from ansible_inspec import Runner
from ansible_inspec.core import ExecutionConfig

# Configure execution
config = ExecutionConfig(
    profile_path="./profiles/linux-baseline",
    target="local://",
    reporter="json",
    output_path="local-compliance.json"
)

# Run profile
runner = Runner(config)
result = runner.run()

# Check results
if result.success:
    print("✓ System is compliant!")
else:
    print(f"✗ {result.controls_failed} controls failed")
    print(result.error)

# Generate HTML report
result.save("compliance-report.html", format="html")
```

### Example 2: Multi-Host Compliance

```python
from ansible_inspec import Runner
from ansible_inspec.core import ExecutionConfig

# Use Ansible inventory
config = ExecutionConfig(
    profile_path="./profiles/cis-benchmark",
    target="inventory.yml",  # Ansible inventory file
    reporter="html",
    output_path=".compliance-reports/multi-host.html"
)

runner = Runner(config)
result = runner.run()

print(f"Tested: {result.hosts_total} hosts")
print(f"Passed: {result.controls_passed}/{result.controls_total}")
```

### Example 3: Convert and Deploy

```python
from ansible_inspec import ProfileConverter
import subprocess

# Convert InSpec profile
converter = ProfileConverter(
    profile_path="./profiles/pci-dss",
    namespace="compliance",
    collection_name="pci_dss"
)

collection_path = converter.convert()
tarball = converter.build()

# Install collection
subprocess.run([
    "ansible-galaxy", "collection", "install",
    tarball, "--force"
])

# Run collection playbook
subprocess.run([
    "ansible-playbook",
    f"{collection_path}/playbooks/compliance_check.yml",
    "-i", "inventory.yml"
])
```

### Example 4: CI/CD Integration

```python
from ansible_inspec import Runner
from ansible_inspec.core import ExecutionConfig
import sys

# Configure for CI/CD
config = ExecutionConfig(
    profile_path=os.getenv("PROFILE_PATH"),
    target=os.getenv("TARGET_INVENTORY"),
    reporter="junit",
    output_path="test-results/compliance.xml"
)

runner = Runner(config)
result = runner.run()

# Exit with appropriate code for CI/CD
sys.exit(0 if result.success else 1)
```

### Example 5: Custom Reporting

```python
from ansible_inspec import Runner
from ansible_inspec.core import ExecutionConfig
from ansible_inspec.reporters import InSpecJSONReport
import json

# Run profile
config = ExecutionConfig(
    profile_path="./my-profile",
    target="local://"
)

runner = Runner(config)
result = runner.run()

# Parse JSON report
report_data = json.loads(result.to_json())

# Custom analysis
for profile in report_data['profiles']:
    for control in profile['controls']:
        if control['results'][0]['status'] == 'failed':
            print(f"FAILED: {control['id']} - {control['title']}")
            print(f"  Impact: {control['impact']}")
            print(f"  Description: {control['desc']}")
```

### Example 6: Chef Supermarket Integration

```python
from ansible_inspec import SupermarketClient, ProfileConverter

# Search for profiles
client = SupermarketClient()
profiles = client.search("CIS", limit=10)

for profile in profiles:
    print(f"{profile['name']}: {profile['summary']}")

# Download and convert
profile_name = "dev-sec/linux-baseline"
profile_info = client.info(profile_name)
profile_path = client.download(profile_name, output_dir="./profiles")

# Convert to Ansible collection
converter = ProfileConverter(
    profile_path=profile_path,
    namespace="devsec",
    collection_name="linux_baseline"
)

collection_path = converter.convert()
print(f"Collection ready: {collection_path}")
```

---

## Configuration

### Environment Variables

- `ANSIBLE_INSPEC_REPORTER` - Default reporter format
- `ANSIBLE_INSPEC_OUTPUT_DIR` - Default output directory
- `ANSIBLE_CONFIG` - Ansible configuration file
- `ANSIBLE_INVENTORY` - Default inventory file

### Ansible Configuration

```ini
# ansible.cfg
[defaults]
callbacks_enabled = compliance_reporter
callback_result_dir = .compliance-reports

[callback_compliance_reporter]
output_dir = .compliance-reports
output_format = json
```

---

## Error Handling

```python
from ansible_inspec import Runner, ProfileConverter
from ansible_inspec.core import ExecutionConfig
from ansible_inspec.exceptions import ProfileNotFoundError, ConversionError

# Execution error handling
try:
    config = ExecutionConfig(
        profile_path="./nonexistent-profile",
        target="local://"
    )
    runner = Runner(config)
    result = runner.run()
except ProfileNotFoundError as e:
    print(f"Profile error: {e}")
except Exception as e:
    print(f"Execution error: {e}")

# Conversion error handling
try:
    converter = ProfileConverter(
        profile_path="./invalid-profile",
        namespace="test"
    )
    converter.convert()
except ConversionError as e:
    print(f"Conversion failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Support and Resources

- **Documentation**: https://github.com/Htunn/ansible-inspec#readme
- **PyPI**: https://pypi.org/project/ansible-inspec/
- **Docker Hub**: https://hub.docker.com/r/htunnthuthu/ansible-inspec
- **Issues**: https://github.com/Htunn/ansible-inspec/issues
- **Changelog**: https://github.com/Htunn/ansible-inspec/blob/main/CHANGELOG.md

---

## License

GPL-3.0-or-later. See [LICENSE](../LICENSE) for details.
