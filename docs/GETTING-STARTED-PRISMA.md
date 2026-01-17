# Getting Started with Ansible-InSpec (Prisma Edition)

This guide will help you set up and run ansible-inspec with Prisma Python ORM in under 15 minutes.

## Prerequisites

- Python 3.8+
- PostgreSQL 13+ (or Docker)
- Git

## Step 1: Clone Repository

```bash
git clone https://github.com/Htunn/ansible-inspec.git
cd ansible-inspec
```

## Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Step 3: Start PostgreSQL

### Option A: Docker (Recommended for development)

```bash
docker run -d \
  --name ansible-inspec-postgres \
  -e POSTGRES_USER=ansible \
  -e POSTGRES_PASSWORD=ansible \
  -e POSTGRES_DB=ansible_inspec \
  -p 5432:5432 \
  postgres:15-alpine
```

### Option B: Local PostgreSQL

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt-get install postgresql-15
sudo systemctl start postgresql

# Create database
psql -U postgres -c "CREATE USER ansible WITH PASSWORD 'ansible';"
psql -U postgres -c "CREATE DATABASE ansible_inspec OWNER ansible;"
```

## Step 4: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Generate encryption key
python scripts/generate_encryption_key.py

# Edit .env and update:
# - DATABASE__URL (if not using defaults)
# - ENCRYPTION_KEY (from previous step)
# - AUTH__* settings (for Azure AD, see Authentication Guide)
```

Minimal `.env` for local development:

```dotenv
DEBUG=true
STORAGE_BACKEND=database
DATABASE__URL=postgresql://ansible:ansible@localhost:5432/ansible_inspec
ENCRYPTION_KEY=<your-generated-key>
AUTH__ENABLED=false  # Disable for local testing
```

## Step 5: Initialize Database

```bash
# Run Prisma initialization script
python scripts/init_prisma.py
```

This script:
1. Generates Prisma Client Python from `schema.prisma`
2. Creates all database tables
3. Creates default admin user

Or manually:

```bash
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://ansible:ansible@localhost:5432/ansible_inspec"

# Generate Prisma client
prisma generate

# Create tables
prisma db push

# View database in Prisma Studio
prisma studio  # Opens at http://localhost:5555
```

## Step 6: Start Services

### Terminal 1: API Server

```bash
source .venv/bin/activate
uvicorn ansible_inspec.server.api:app --reload --port 8080
```

API will be available at: http://localhost:8080
OpenAPI docs at: http://localhost:8080/docs

### Terminal 2: Streamlit UI (Optional)

```bash
source .venv/bin/activate
streamlit run lib/ansible_inspec/server/ui.py --server.port 8081
```

UI will be available at: http://localhost:8081

## Step 7: Verify Installation

### Check API Health

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status": "healthy", "version": "0.4.0"}
```

### List Job Templates

```bash
curl http://localhost:8080/api/v1/job-templates
```

### Create a Test Job Template

```bash
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-profile",
    "description": "Test InSpec Profile",
    "profile": "https://github.com/dev-sec/linux-baseline.git",
    "extra_vars": {}
  }'
```

## Step 8: Run Your First InSpec Check

### Via API

```bash
curl -X POST http://localhost:8080/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "<template-id-from-previous-step>",
    "target": "localhost"
  }'
```

### Via CLI

```bash
ansible-inspec run \
  --profile https://github.com/dev-sec/linux-baseline.git \
  --target localhost
```

## Next Steps

### Enable Authentication

See [Authentication Guide](../ansible-inspec-docs/guides/authentication.md) for Azure AD setup.

### Configure VCS Integration

See [VCS Integration Guide](../ansible-inspec-docs/guides/vcs-integration.md) for Git repository sync.

### Set Up Monitoring

See [Monitoring Guide](../ansible-inspec-docs/guides/monitoring.md) for Prometheus/Grafana setup.

### Production Deployment

See [Deployment Guide](../ansible-inspec-docs/guides/deployment.md) for Kubernetes/Docker deployment.

## Troubleshooting

### "Prisma CLI not found"

```bash
pip install prisma
```

### "Can't connect to database"

Verify PostgreSQL is running:
```bash
psql postgresql://ansible:ansible@localhost:5432/ansible_inspec -c "SELECT 1"
```

### "Table does not exist"

Run database initialization:
```bash
python scripts/init_prisma.py
```

### "Import Error: No module named 'prisma'"

Generate Prisma client:
```bash
prisma generate
```

### "Permission denied"

Make scripts executable:
```bash
chmod +x scripts/*.py
```

## Development Workflow

### Making Schema Changes

1. Edit `schema.prisma`
2. Generate client: `prisma generate`
3. Push to database: `prisma db push`
4. Test changes

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black lib/ tests/
flake8 lib/ tests/
```

### Type Checking

```bash
mypy lib/ansible_inspec/
```

## Common Commands

```bash
# Start PostgreSQL (Docker)
docker start ansible-inspec-postgres

# Stop PostgreSQL (Docker)
docker stop ansible-inspec-postgres

# View database schema
prisma studio

# Generate Prisma client
prisma generate

# Create migration
prisma migrate dev --name description

# Apply migrations
prisma migrate deploy

# Reset database (⚠️ DESTRUCTIVE)
prisma migrate reset

# View API documentation
open http://localhost:8080/docs

# View Prometheus metrics
curl http://localhost:8080/metrics
```

## Quick Reference

| Service | URL | Purpose |
|---------|-----|---------|
| API Server | http://localhost:8080 | REST API endpoints |
| API Docs | http://localhost:8080/docs | OpenAPI/Swagger UI |
| Streamlit UI | http://localhost:8081 | Web dashboard |
| Prisma Studio | http://localhost:5555 | Database browser |
| Prometheus Metrics | http://localhost:8080/metrics | Monitoring metrics |

## Resources

- [Prisma Migration Guide](PRISMA-MIGRATION.md)
- [API Documentation](API.md)
- [Architecture Overview](../ansible-inspec-docs/guides/architecture.md)
- [Contributing Guide](CONTRIBUTING.md)
