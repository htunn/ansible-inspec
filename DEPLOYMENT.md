# Deployment Guide: Authentication & VCS Integration

This guide covers deploying the Authentication and VCS Integration features for ansible-inspec server.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Authentication Setup](#authentication-setup)
- [VCS Integration Setup](#vcs-integration-setup)
- [Streamlit UI Configuration](#streamlit-ui-configuration)
- [Database Migration](#database-migration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Prerequisites

### Required

- PostgreSQL 13+ database
- Azure AD tenant and app registration (for authentication)
- Python 3.9+
- Git CLI installed on server

### Optional

- Reverse proxy with TLS/SSL (nginx, Traefik)
- Secrets management (Azure Key Vault, AWS Secrets Manager, HashiCorp Vault)

## Authentication Setup

### Step 1: Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
2. Click "New registration"
   - Name: `ansible-inspec-server`
   - Supported account types: Single tenant or multi-tenant
   - Redirect URI: `Web` → `http://localhost:8080/api/v1/auth/callback` (update for production)
3. Note the **Application (client) ID** and **Directory (tenant) ID**

### Step 2: Configure API Permissions

1. Go to **API permissions** → Add a permission → Microsoft Graph
2. Select **Delegated permissions** and add:
   - `openid`
   - `profile`
   - `email`
   - `User.Read`
3. Click **Grant admin consent**

### Step 3: Create Client Secret

1. Go to **Certificates & secrets** → New client secret
2. Description: `ansible-inspec-server-secret`
3. Expires: 24 months (recommended)
4. **Copy the secret value immediately** (won't be shown again)

### Step 4: Configure Server Environment

Update your `.env` file:

```bash
# Enable authentication
AUTH__ENABLED=true

# Azure AD Configuration
AUTH__AZURE_TENANT_ID=your-tenant-id-here
AUTH__AZURE_CLIENT_ID=your-client-id-here
AUTH__AZURE_CLIENT_SECRET=your-client-secret-here

# Generate JWT secret
AUTH__JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
AUTH__JWT_ALGORITHM=HS256
AUTH__ACCESS_TOKEN_EXPIRE_MINUTES=30
AUTH__REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth2 Redirect URIs (update for production)
AUTH__OAUTH_REDIRECT_URI=http://localhost:8080/api/v1/auth/callback
AUTH__STREAMLIT_UI_URL=http://localhost:8081

# Database required for authentication
STORAGE_BACKEND=database
DATABASE__URL=postgresql://user:password@localhost:5432/ansibleinspec
```

### Step 5: Run Database Migration

```bash
# Apply Prisma schema changes
cd /path/to/ansible-inspec
python -m prisma db push

# Verify migration
python -m prisma db pull
```

### Step 6: Test Authentication

1. Start the API server:
   ```bash
   uvicorn ansible_inspec.server.api:app --reload --port 8080
   ```

2. Access login endpoint:
   ```bash
   curl http://localhost:8080/api/v1/auth/login
   ```
   Should redirect to Azure AD login page

3. Complete OAuth flow and verify JWT token is returned

## VCS Integration Setup

### Step 1: Generate Encryption Key

VCS credentials are encrypted at rest. Generate a secure encryption key:

```bash
# Generate key
python scripts/generate_encryption_key.py

# Output will include:
# ENCRYPTION_KEY=...base64-key...
```

**CRITICAL:** Backup this key securely! Lost keys = permanent data loss.

### Step 2: Configure VCS Settings

Update your `.env` file:

```bash
# Enable VCS
VCS__ENABLED=true
VCS__POLL_INTERVAL_MINUTES=15
VCS__CONFIG_DIR=./data/vcs_repos

# Webhooks (optional)
VCS__WEBHOOK_ENABLED=true
VCS__WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Encryption key (REQUIRED)
ENCRYPTION_KEY=your-generated-key-from-step-1
```

### Step 3: Store Encryption Key Securely

#### Option 1: Password Manager
- Store in 1Password, LastPass, or similar
- Tag with: `ansible-inspec-encryption-key`
- Include: date created, server hostname

#### Option 2: Secrets Manager
```bash
# Azure Key Vault
az keyvault secret set \
  --vault-name myVault \
  --name ansible-inspec-encryption-key \
  --value "your-key-here"

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name ansible-inspec/encryption-key \
  --secret-string "your-key-here"

# HashiCorp Vault
vault kv put secret/ansible-inspec encryption_key="your-key-here"
```

#### Option 3: Encrypted File
```bash
# Create encrypted file
echo "ENCRYPTION_KEY=your-key-here" > .encryption_key
chmod 600 .encryption_key

# Load in environment
source .encryption_key
```

### Step 4: Create VCS Credentials

Using the API (requires admin role):

```bash
# GitHub Personal Access Token
curl -X POST http://localhost:8080/api/v1/vcs-credentials \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "github-token",
    "vcs_type": "github",
    "username": "your-github-username",
    "token": "ghp_your_personal_access_token"
  }'

# SSH Key
curl -X POST http://localhost:8080/api/v1/vcs-credentials \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "git-ssh-key",
    "vcs_type": "git",
    "username": "git",
    "ssh_private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\n...\n-----END OPENSSH PRIVATE KEY-----"
  }'
```

### Step 5: Create VCS Repository

```bash
curl -X POST http://localhost:8080/api/v1/vcs/repositories \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "compliance-profiles",
    "url": "https://github.com/your-org/inspec-profiles.git",
    "branch": "main",
    "credential_id": "credential-id-from-step-4",
    "poll_interval_minutes": 15,
    "auto_import": true
  }'
```

### Step 6: Configure Webhooks (Optional)

#### GitHub

1. Go to repository → Settings → Webhooks → Add webhook
2. Payload URL: `https://your-server.com/api/v1/webhooks/github/compliance-profiles`
3. Content type: `application/json`
4. Secret: Value of `VCS__WEBHOOK_SECRET` from .env
5. Events: Just the push event
6. Active: ✓

#### GitLab

1. Go to repository → Settings → Webhooks
2. URL: `https://your-server.com/api/v1/webhooks/gitlab/compliance-profiles`
3. Secret token: Value of `VCS__WEBHOOK_SECRET` from .env
4. Trigger: Push events
5. Enable SSL verification: ✓

## Streamlit UI Configuration

### Step 1: Update Streamlit Settings

The Streamlit UI now supports authentication. No additional configuration needed if you set `AUTH__STREAMLIT_UI_URL` in .env.

### Step 2: Start Streamlit

```bash
streamlit run lib/ansible_inspec/server/streamlit_app.py --server.port 8081
```

### Step 3: Access UI

1. Navigate to: `http://localhost:8081`
2. Click "Login with Azure AD"
3. Complete Azure AD authentication
4. Redirected back to Streamlit with active session

**Note:** Tokens stored in session state only (lost on browser refresh).

## Database Migration

### Apply New Schema

The VCS sync history table was added. Apply migration:

```bash
# Development: Push schema changes
python -m prisma db push

# Production: Generate migration
python -m prisma migrate dev --name add_vcs_sync_history

# Or use init script
python scripts/init_prisma.py
```

### Verify Migration

```bash
# Check tables
python -m prisma db pull

# Verify VCSSyncHistory table exists
psql -d ansibleinspec -c "\d vcs_sync_history"
```

## Testing

### Test Authentication Flow

```bash
# 1. Get login URL
curl http://localhost:8080/api/v1/auth/login -L

# 2. Complete browser login and copy JWT from response

# 3. Test authenticated endpoint
curl http://localhost:8080/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Expected response:
# {
#   "id": "...",
#   "username": "user@domain.com",
#   "email": "user@domain.com",
#   "roles": ["viewer"]
# }
```

### Test VCS Sync

```bash
# Manual sync trigger
curl -X POST http://localhost:8080/api/v1/vcs/repositories/compliance-profiles/sync \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Check sync history
curl http://localhost:8080/api/v1/vcs/repositories/compliance-profiles/history \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Test Webhook (GitHub)

```bash
# Simulate GitHub webhook
curl -X POST http://localhost:8080/api/v1/webhooks/github/compliance-profiles \
  -H "X-GitHub-Event: push" \
  -H "X-Hub-Signature-256: sha256=..." \
  -H "Content-Type: application/json" \
  -d '{
    "ref": "refs/heads/main",
    "after": "abc123...",
    "repository": {"url": "https://github.com/your-org/repo"}
  }'
```

## Troubleshooting

### Authentication Issues

#### "Missing authorization URL method"
- **Cause:** Old code version without `get_authorization_url()`
- **Fix:** Pull latest code, restart server

#### "Invalid token signature"
- **Cause:** JWKS cache stale or Azure AD key rotation
- **Fix:** Cache auto-refreshes every 24h, wait or restart server

#### "401 Unauthorized" after login
- **Cause:** Token expired (30 min default)
- **Fix:** Re-login, or increase `AUTH__ACCESS_TOKEN_EXPIRE_MINUTES`

### VCS Issues

#### "Scheduler not running"
- **Cause:** Server started before database ready
- **Fix:** Check logs, restart server, verify database connection

#### "Encryption key required"
- **Cause:** `ENCRYPTION_KEY` not set
- **Fix:** Generate key, add to .env, restart

#### "Git clone failed"
- **Cause:** Invalid credentials or network issue
- **Fix:** Verify credential via `git clone` manually, check logs

#### "Webhook signature validation failed"
- **Cause:** Mismatch between server secret and GitHub/GitLab config
- **Fix:** Regenerate secret, update both .env and webhook config

### Streamlit Issues

#### "Session lost on refresh"
- **Expected behavior:** Tokens stored in session state (in-memory)
- **Fix:** Re-login after refresh, or implement localStorage (future)

#### "Cannot connect to API"
- **Cause:** API server not running or wrong URL
- **Fix:** Check `API_BASE_URL` environment variable

## Security Considerations

### Production Deployment

#### 1. Enable HTTPS
```nginx
server {
    listen 443 ssl http2;
    server_name your-server.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Update .env:
```bash
AUTH__OAUTH_REDIRECT_URI=https://your-server.com/api/v1/auth/callback
AUTH__STREAMLIT_UI_URL=https://your-server.com:8081
```

#### 2. Rotate Secrets Regularly

```bash
# JWT Secret - every 90 days
AUTH__JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Webhook Secret - every 90 days
VCS__WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Encryption Key - use rotation function
python -c "from ansible_inspec.server.encryption import rotate_encryption_key; rotate_encryption_key()"
```

#### 3. Audit Logging

All authentication and VCS events are logged. Monitor for:
- Repeated failed logins (potential attack)
- VCS credential access
- Manual sync triggers
- Failed webhook validations

#### 4. Network Security

- Restrict database access to localhost or private network
- Use firewall rules to limit API access
- Enable rate limiting on auth endpoints
- Use VPN or bastion host for admin access

#### 5. RBAC Enforcement

Default roles:
- **admin**: Full access (credentials, user management)
- **operator**: Trigger syncs, create templates
- **viewer**: Read-only access

Assign roles via Azure AD token claims or manual user update.

## Rollback Procedure

If deployment fails:

```bash
# 1. Stop services
docker-compose down  # or kill processes

# 2. Restore database backup
pg_restore -d ansibleinspec backup.dump

# 3. Revert code
git revert <commit-hash>
# or
git checkout <previous-tag>

# 4. Restore .env from backup
cp .env.backup .env

# 5. Restart with previous version
docker-compose up -d
```

## Next Steps

- Configure monitoring and alerting
- Set up automated backups
- Implement multi-environment deployment (dev, staging, prod)
- Add custom Azure AD roles for fine-grained RBAC
- Integrate with SIEM for security event monitoring

For questions or issues, consult:
- [Authentication Guide](ansible-inspec-docs/guides/authentication.md)
- [VCS Integration Guide](ansible-inspec-docs/guides/vcs-integration.md)
- [API Documentation](http://localhost:8080/docs)
