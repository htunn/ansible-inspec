# Quick Start Guide

Get ansible-inspec running in under 5 minutes!

## 🚀 Option 1: Docker (Recommended for Production)

### Prerequisites
- Docker 20.10+ and Docker Compose 2.0+
- 2GB RAM available
- Ports 8080 and 5432 available

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/htunn/ansible-inspec.git
cd ansible-inspec

# 2. Copy environment template
cp .env.docker .env

# 3. Generate secrets (requires Python)
# Encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 4. Edit .env file
# - Set POSTGRES_PASSWORD (required)
# - Set ENCRYPTION_KEY (from step 3)
# - Set AUTH__JWT_SECRET (from step 3)

# 5. Start services
docker-compose up -d

# 6. Wait for services to be healthy (30 seconds)
sleep 30

# 7. Initialize database
docker-compose exec api prisma db push

# 8. Check health
curl http://localhost:8080/health
```

**Expected output:**
```json
{
  "status": "healthy",
  "version": "0.4.0",
  "storage_backend": "database",
  "auth_enabled": false,
  "vcs_enabled": false
}
```

### Access Points

- **API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **Metrics**: http://localhost:8080/metrics

## 📦 Option 2: pip Install (Development/Local)

### Prerequisites
- Python 3.8+
- PostgreSQL 12+ running locally
- InSpec installed (for profile conversion)

### Steps

```bash
# 1. Install from PyPI
pip install ansible-inspec

# 2. Create .env file
cat > .env <<EOF
DATABASE__URL=postgresql://user:password@localhost:5432/ansible_inspec
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
AUTH__JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
AUTH__ENABLED=false
STORAGE_BACKEND=database
EOF

# 3. Initialize database (first time only)
# Run migrations in your PostgreSQL database

# 4. Start API server
ansible-inspec start-server --port 8080

# 5. Check health (in another terminal)
curl http://localhost:8080/health
```

## 🔧 Your First Compliance Check

### Create a Job Template

```bash
# Using Chef Supermarket profile
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "linux-baseline",
    "description": "DevSec Linux Baseline",
    "profile": "dev-sec/linux-baseline",
    "supermarket": true,
    "inventory": ["inventory.yml"],
    "enabled": true
  }'
```

### Create Inventory File

```bash
cat > examples/inventory.yml <<EOF
all:
  hosts:
    localhost:
      ansible_connection: local
EOF
```

### Execute Job

```bash
curl -X POST http://localhost:8080/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "linux-baseline"
  }'
```

### Check Job Status

```bash
# Get job ID from previous response, then:
curl http://localhost:8080/api/v1/jobs/<job-id>
```

## 📚 Next Steps

### Explore More Profiles

```bash
# CIS Docker Benchmark
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "docker-benchmark",
    "profile": "dev-sec/cis-docker-benchmark",
    "supermarket": true,
    "inventory": ["inventory.yml"]
  }'

# SSH Baseline
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ssh-baseline",
    "profile": "dev-sec/ssh-baseline",
    "supermarket": true,
    "inventory": ["inventory.yml"]
  }'
```

### Create Custom Profile

```bash
# 1. Create profile structure
mkdir -p examples/profiles/custom-checks

# 2. Create inspec.yml
cat > examples/profiles/custom-checks/inspec.yml <<EOF
name: custom-checks
title: Custom Security Checks
version: 1.0.0
supports:
  - os-family: linux
EOF

# 3. Create control
cat > examples/profiles/custom-checks/controls/filesystem.rb <<EOF
control 'filesystem-1.0' do
  impact 0.7
  title 'Critical directories should exist'
  
  describe file('/tmp') do
    it { should exist }
    it { should be_directory }
  end
end
EOF

# 4. Create job template for custom profile
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom-checks",
    "profile": "/app/profiles/custom-checks",
    "supermarket": false,
    "inventory": ["inventory.yml"]
  }'
```

### Enable Authentication

```bash
# Edit .env file:
AUTH__ENABLED=true
AUTH__AZURE_TENANT_ID=your-tenant-id
AUTH__AZURE_CLIENT_ID=your-client-id
AUTH__AZURE_CLIENT_SECRET=your-client-secret

# Restart services
docker-compose restart api
```

### Enable VCS Sync

```bash
# Edit .env file:
VCS__ENABLED=true
VCS__REPOSITORIES=[{"name":"profiles","url":"https://github.com/org/profiles.git","branch":"main"}]

# Add VCS credential via API
curl -X POST http://localhost:8080/api/v1/vcs-credentials \
  -H "Content-Type: application/json" \
  -d '{
    "name": "github-token",
    "credential_type": "token",
    "username": "your-username",
    "token": "ghp_your_token_here"
  }'

# Restart to trigger sync
docker-compose restart api
```

## 🔍 Troubleshooting

### API won't start

```bash
# Check logs
docker-compose logs -f api

# Common issues:
# - Missing environment variables
# - Database not ready
# - Port conflicts
```

### Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U ansibleinspec -c "SELECT 1"
```

### Job execution fails

```bash
# Check job logs in database
docker-compose exec postgres psql -U ansibleinspec -c \
  "SELECT id, status, error FROM \"Job\" ORDER BY created_at DESC LIMIT 5;"

# Check InSpec installation
docker-compose exec api inspec --version
```

## 📖 Documentation

- **Full Documentation**: [docs/](docs/)
- **Docker Deployment**: [docs/DOCKER-DEPLOYMENT.md](docs/DOCKER-DEPLOYMENT.md)
- **Testing Guide**: [TESTING.md](TESTING.md)
- **API Reference**: http://localhost:8080/docs
- **Profile Conversion**: [docs/PROFILE-CONVERSION.md](docs/PROFILE-CONVERSION.md)

## 🆘 Getting Help

- **Issues**: https://github.com/htunn/ansible-inspec/issues
- **Discussions**: https://github.com/htunn/ansible-inspec/discussions
- **Examples**: [examples/](examples/)

## 🎯 What's Next?

1. ✅ Set up Docker environment
2. ✅ Create your first job template
3. ✅ Run a compliance check
4. 📖 Read the [full documentation](docs/)
5. 🔐 Enable [authentication](docs/DOCKER-DEPLOYMENT.md#security-checklist)
6. 🔄 Set up [VCS sync](docs/SERVER.md#vcs-integration)
7. 📊 Build [workflows](docs/SERVER.md#workflow-templates)
8. 🚀 Deploy to production!
