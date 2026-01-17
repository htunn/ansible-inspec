# Testing Guide

## Overview

This guide covers testing ansible-inspec with Docker, job templates, and various InSpec profiles.

## Quick Test

```bash
# 1. Start Docker services
docker-compose up -d

# 2. Wait for services to be healthy (30 seconds)
sleep 30

# 3. Initialize database
docker-compose exec api prisma db push

# 4. Run job template tests
./tests/test_job_templates.sh
```

## Detailed Testing

### 1. Docker Setup Test

#### Build and Start

```bash
# Build from scratch
docker-compose build --no-cache

# Start services
docker-compose up -d

# Check status
docker-compose ps

# Expected output:
# NAME                  STATUS              PORTS
# ansible-inspec-api    running (healthy)   0.0.0.0:8080->8080/tcp
# ansible-inspec-postgres  running (healthy)   5432/tcp
```

#### Health Checks

```bash
# API health
curl http://localhost:8080/health

# Expected:
# {
#   "status": "healthy",
#   "version": "0.4.0",
#   "storage_backend": "database",
#   "auth_enabled": false,
#   "vcs_enabled": false
# }

# PostgreSQL health
docker-compose exec postgres pg_isready -U ansibleinspec

# Expected: /var/run/postgresql:5432 - accepting connections
```

#### Database Initialization

```bash
# Push Prisma schema
docker-compose exec api prisma db push

# Expected:
# ✅ Database schema updated successfully

# Verify tables
docker-compose exec postgres psql -U ansibleinspec -c "\dt"

# Expected tables:
# User, JobTemplate, Job, WorkflowTemplate, WorkflowNode,
# VCSCredential, VCSRepository, AuditLog, Workflow
```

### 2. Job Template Tests

#### Automated Test Suite

Run the comprehensive test script:

```bash
./tests/test_job_templates.sh
```

This tests:
- ✅ API health check
- ✅ Create Chef Supermarket template
- ✅ Create local InSpec profile template
- ✅ List all templates
- ✅ Get specific template
- ✅ Update template
- ✅ Execute job from Supermarket profile
- ✅ Execute job from local profile
- ✅ List all jobs
- ✅ Cleanup templates

#### Manual Testing

##### Test Chef Supermarket Profile

```bash
# Create template
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cis-docker-benchmark",
    "description": "CIS Docker Benchmark",
    "profile": "dev-sec/cis-docker-benchmark",
    "supermarket": true,
    "inventory": ["inventory.yml"],
    "enabled": true
  }'

# Execute job
curl -X POST http://localhost:8080/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "cis-docker-benchmark"
  }'
```

##### Test Local InSpec Profile

First, create a local profile:

```bash
# Create profile directory
mkdir -p ./examples/profiles/custom-checks

# Create inspec.yml
cat > ./examples/profiles/custom-checks/inspec.yml <<EOF
name: custom-checks
title: Custom Security Checks
version: 1.0.0
maintainer: Your Name
copyright: Your Organization
license: Apache-2.0
summary: Custom InSpec profile
supports:
  - os-family: linux
EOF

# Create control
cat > ./examples/profiles/custom-checks/controls/filesystem.rb <<EOF
control 'filesystem-1.0' do
  impact 0.7
  title 'Critical directories should exist'
  desc 'Ensures critical system directories exist'
  
  describe file('/tmp') do
    it { should exist }
    it { should be_directory }
  end
  
  describe file('/var') do
    it { should exist }
    it { should be_directory }
  end
end
EOF

# Create template for this profile
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom-security-checks",
    "description": "Custom security checks",
    "profile": "/app/profiles/custom-checks",
    "supermarket": false,
    "inventory": ["inventory.yml"],
    "enabled": true
  }'

# Execute job
curl -X POST http://localhost:8080/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "custom-security-checks"
  }'
```

### 3. API Endpoint Tests

#### Job Templates

```bash
# List all templates
curl http://localhost:8080/api/v1/job-templates

# Get specific template
curl http://localhost:8080/api/v1/job-templates/cis-docker-benchmark

# Update template
curl -X PUT http://localhost:8080/api/v1/job-templates/cis-docker-benchmark \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated CIS Docker Benchmark",
    "enabled": false
  }'

# Delete template
curl -X DELETE http://localhost:8080/api/v1/job-templates/cis-docker-benchmark
```

#### Jobs

```bash
# List all jobs
curl http://localhost:8080/api/v1/jobs

# Get specific job
JOB_ID="<job-id-from-list>"
curl http://localhost:8080/api/v1/jobs/${JOB_ID}

# Cancel job
curl -X POST http://localhost:8080/api/v1/jobs/${JOB_ID}/cancel
```

#### System

```bash
# Metrics
curl http://localhost:8080/metrics

# API documentation
curl http://localhost:8080/docs

# OpenAPI schema
curl http://localhost:8080/openapi.json
```

### 4. Profile Types Testing

#### Chef Supermarket Profiles

Popular profiles to test:

```bash
# DevSec Linux Baseline
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{"name":"linux-baseline","profile":"dev-sec/linux-baseline","supermarket":true,"inventory":["inventory.yml"]}'

# DevSec SSH Baseline
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{"name":"ssh-baseline","profile":"dev-sec/ssh-baseline","supermarket":true,"inventory":["inventory.yml"]}'

# DevSec Nginx Baseline
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{"name":"nginx-baseline","profile":"dev-sec/nginx-baseline","supermarket":true,"inventory":["inventory.yml"]}'
```

#### Local Profile Path Formats

Test different path formats:

```bash
# Absolute path
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{"name":"local-absolute","profile":"/app/profiles/custom-checks","supermarket":false,"inventory":["inventory.yml"]}'

# Relative path (from /app)
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{"name":"local-relative","profile":"profiles/custom-checks","supermarket":false,"inventory":["inventory.yml"]}'
```

### 5. Integration Tests

#### With Inventory

Create test inventory:

```bash
cat > ./examples/inventory.yml <<EOF
all:
  hosts:
    localhost:
      ansible_connection: local
    
  children:
    webservers:
      hosts:
        web1.example.com:
          ansible_host: 192.168.1.10
        web2.example.com:
          ansible_host: 192.168.1.11
    
    databases:
      hosts:
        db1.example.com:
          ansible_host: 192.168.1.20
EOF

# Test with specific hosts
curl -X POST http://localhost:8080/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "linux-baseline",
    "extra_vars": {
      "limit": "webservers"
    }
  }'
```

#### With Extra Variables

```bash
curl -X POST http://localhost:8080/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "linux-baseline",
    "extra_vars": {
      "compliance_level": "strict",
      "environment": "production"
    }
  }'
```

### 6. Error Handling Tests

#### Invalid Template

```bash
# Missing required field
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{"name":"invalid"}'

# Expected: 422 Unprocessable Entity with validation errors
```

#### Invalid Profile

```bash
# Non-existent Supermarket profile
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{"name":"bad-profile","profile":"nonexistent/profile","supermarket":true,"inventory":["inventory.yml"]}'

# Non-existent local profile
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{"name":"bad-local","profile":"/nonexistent/path","supermarket":false,"inventory":["inventory.yml"]}'
```

#### Invalid Job

```bash
# Non-existent template
curl -X POST http://localhost:8080/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"template_name":"does-not-exist"}'

# Expected: 404 Not Found
```

### 7. Performance Tests

#### Load Test with Apache Bench

```bash
# Install apache bench
# macOS: brew install httpie
# Linux: apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8080/health

# Test list templates
ab -n 100 -c 5 http://localhost:8080/api/v1/job-templates
```

#### Concurrent Jobs

```bash
# Create multiple jobs concurrently
for i in {1..5}; do
  curl -X POST http://localhost:8080/api/v1/jobs \
    -H "Content-Type: application/json" \
    -d '{"template_name":"linux-baseline"}' &
done
wait

# Check job queue
curl http://localhost:8080/api/v1/jobs | jq '.[] | {id, status, created_at}'
```

### 8. Database Tests

#### Direct Database Queries

```bash
# List all templates
docker-compose exec postgres psql -U ansibleinspec -c "SELECT id, name, profile, supermarket FROM \"JobTemplate\";"

# List all jobs
docker-compose exec postgres psql -U ansibleinspec -c "SELECT id, template_id, status, created_at FROM \"Job\" ORDER BY created_at DESC LIMIT 10;"

# Count by status
docker-compose exec postgres psql -U ansibleinspec -c "SELECT status, COUNT(*) FROM \"Job\" GROUP BY status;"
```

#### Data Integrity

```bash
# Check foreign key relationships
docker-compose exec postgres psql -U ansibleinspec -c "
  SELECT j.id, j.status, jt.name as template_name
  FROM \"Job\" j
  JOIN \"JobTemplate\" jt ON j.template_id = jt.id
  LIMIT 10;
"
```

## Troubleshooting

### Container Issues

```bash
# View logs
docker-compose logs -f api

# Restart API
docker-compose restart api

# Rebuild API
docker-compose up -d --build api
```

### Database Issues

```bash
# Reset database
docker-compose down
docker volume rm ansible-inspec_postgres_data
docker-compose up -d
docker-compose exec api prisma db push
```

### InSpec Issues

```bash
# Check InSpec installation in container
docker-compose exec api inspec --version

# Test profile syntax locally
docker-compose exec api inspec check /app/profiles/custom-checks

# Execute profile directly
docker-compose exec api inspec exec /app/profiles/custom-checks
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start services
        run: |
          cp .env.docker .env
          echo "POSTGRES_PASSWORD=test123" >> .env
          echo "ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> .env
          echo "AUTH__JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env
          docker-compose up -d
      
      - name: Wait for services
        run: sleep 30
      
      - name: Initialize database
        run: docker-compose exec -T api prisma db push
      
      - name: Run tests
        run: ./tests/test_job_templates.sh
      
      - name: Show logs on failure
        if: failure()
        run: docker-compose logs
```

## Test Coverage Goals

- ✅ Docker Compose setup and configuration
- ✅ API health and availability
- ✅ Chef Supermarket profile templates
- ✅ Local InSpec profile templates
- ✅ Job template CRUD operations
- ✅ Job execution and status tracking
- ✅ Database persistence
- ✅ Error handling and validation
- ⏳ Authentication (when enabled)
- ⏳ VCS integration (when enabled)
- ⏳ Workflow templates
- ⏳ Multi-profile jobs

## Next Steps

After successful testing:

1. **Enable Authentication**
   - Set `AUTH__ENABLED=true`
   - Configure Azure AD credentials
   - Test RBAC (admin/operator/viewer)

2. **Production Deployment**
   - Set strong passwords
   - Enable HTTPS
   - Configure monitoring
   - Set up backups

3. **Advanced Features**
   - VCS integration (GitHub/GitLab)
   - Workflow templates
   - Scheduled jobs
   - Reporting dashboards
