# Publishing Checklist for v0.4.0

## ✅ Completed Items

### Docker Infrastructure
- [x] **docker-compose.yml** production-ready
  - Removed Redis service (not used)
  - Updated to PostgreSQL 16-alpine
  - Environment variable substitution
  - Named volumes for data persistence
  - Health checks for both services
  - Profiles volume mount for local InSpec profiles
  
- [x] **Dockerfile** optimized
  - Python 3.13-slim base image
  - Multi-stage build for smaller image
  - Node.js 20 for Prisma CLI
  - Prisma generate in build stage
  - Proper health check endpoint
  - Labels for metadata
  - Non-root user execution
  
- [x] **.env Configuration** enforced
  - Removed hardcoded database credentials
  - Removed hardcoded JWT secrets
  - Environment-based configuration only
  - Separate .env.docker template created
  - Clear instructions for secret generation

### Code Quality
- [x] **No hardcoded environment variables** in codebase
  - DatabaseSettings: No default for `url`
  - AuthSettings: No default for `jwt_secret`
  - All sensitive configs require .env
  
- [x] **API Server** fully operational
  - FastAPI with Prisma ORM
  - 20+ REST endpoints
  - Authentication ready (Azure AD OAuth2)
  - RBAC (admin/operator/viewer)
  - VCS sync capabilities
  - Audit logging

### Documentation
- [x] **DOCKER-DEPLOYMENT.md** created
  - Quick start guide
  - Configuration reference
  - Usage examples
  - Production deployment checklist
  - Troubleshooting guide
  
- [x] **TESTING.md** created
  - Docker setup tests
  - Job template tests
  - API endpoint tests
  - Profile types testing
  - Integration tests
  - Performance tests
  
- [x] **QUICKSTART.md** created
  - 5-minute quick start
  - Docker option
  - pip install option
  - First compliance check
  - Next steps
  
- [x] **test_job_templates.sh** script created
  - Automated test suite
  - Chef Supermarket profile tests
  - Local InSpec profile tests
  - CRUD operations
  - Job execution tests

## 🔄 In Progress

### Docker Build
- [ ] **Docker image build** (currently building)
  - Expected time: 3-5 minutes
  - Multi-stage build with Prisma support
  - Node.js + Python + InSpec installation

### Testing
- [ ] **Docker Compose testing** (pending build completion)
  - `docker-compose up -d`
  - Database initialization
  - Health checks
  - API connectivity

## ⏳ Pending Items

### Testing
- [ ] **Job template testing with Chef Supermarket profiles**
  - Test dev-sec/linux-baseline
  - Test dev-sec/ssh-baseline
  - Test dev-sec/cis-docker-benchmark
  - Verify profile download from Supermarket
  - Verify job execution
  - Verify results storage

- [ ] **Job template testing with local InSpec profiles**
  - Create sample local profile
  - Mount to /app/profiles in container
  - Create job template with local path
  - Execute job
  - Verify results

- [ ] **End-to-end Docker workflow test**
  - Start services
  - Initialize database
  - Create templates
  - Execute jobs
  - Verify results
  - Check persistence after restart

### Documentation Updates
- [ ] **README.md** updates
  - Update version to 0.4.0
  - Add Docker quick start section
  - Update feature list
  - Add testing information
  - Update installation instructions

- [ ] **CHANGELOG.md** update
  - Document v0.4.0 changes
  - Docker improvements
  - Configuration changes
  - Breaking changes (if any)

### Code Quality
- [ ] **Unit tests** review
  - Update tests for Prisma
  - Add Docker-specific tests
  - Ensure coverage

- [ ] **Integration tests** (optional)
  - GitHub Actions workflow
  - Automated Docker testing
  - Multi-platform builds

### Release Preparation
- [ ] **Version bumping**
  - Update pyproject.toml
  - Update __version__ in code
  - Update Docker labels

- [ ] **Git tagging**
  - Create v0.4.0 tag
  - Push to GitHub
  - Trigger release workflow

- [ ] **PyPI publishing**
  - Build distribution
  - Upload to PyPI
  - Verify installation

- [ ] **Docker Hub publishing**
  - Tag image
  - Push to Docker Hub
  - Update README on Docker Hub

## 🎯 Post-Publishing Tasks

### Documentation
- [ ] Create release notes
- [ ] Update migration guide (v0.3.x to v0.4.0)
- [ ] Update examples in repository
- [ ] Create video tutorial (optional)

### Community
- [ ] Announce on GitHub Discussions
- [ ] Update project website (if any)
- [ ] Share on social media
- [ ] Respond to initial feedback

### Monitoring
- [ ] Monitor GitHub Issues
- [ ] Monitor Docker Hub pulls
- [ ] Monitor PyPI downloads
- [ ] Collect user feedback

## 📋 Test Plan

### Phase 1: Docker Infrastructure (30 min)
```bash
# 1. Build image
docker-compose build

# 2. Start services
docker-compose up -d

# 3. Check health
curl http://localhost:8080/health

# 4. Initialize database
docker-compose exec api prisma db push

# 5. Verify database
docker-compose exec postgres psql -U ansibleinspec -c "\dt"
```

### Phase 2: Job Templates - Supermarket (20 min)
```bash
# 1. Create template
./tests/test_job_templates.sh

# Or manually:
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "linux-baseline",
    "profile": "dev-sec/linux-baseline",
    "supermarket": true,
    "inventory": ["inventory.yml"]
  }'

# 2. Create inventory
cat > examples/inventory.yml <<EOF
all:
  hosts:
    localhost:
      ansible_connection: local
EOF

# 3. Execute job
curl -X POST http://localhost:8080/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"template_name": "linux-baseline"}'

# 4. Check status
curl http://localhost:8080/api/v1/jobs
```

### Phase 3: Job Templates - Local Profiles (20 min)
```bash
# 1. Create local profile
mkdir -p examples/profiles/sample-profile
cat > examples/profiles/sample-profile/inspec.yml <<EOF
name: sample-profile
title: Sample InSpec Profile
version: 1.0.0
EOF

cat > examples/profiles/sample-profile/controls/example.rb <<EOF
control 'tmp-1.0' do
  title '/tmp should exist'
  describe file('/tmp') do
    it { should exist }
  end
end
EOF

# 2. Create template
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "local-profile",
    "profile": "/app/profiles/sample-profile",
    "supermarket": false,
    "inventory": ["inventory.yml"]
  }'

# 3. Execute job
curl -X POST http://localhost:8080/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"template_name": "local-profile"}'
```

### Phase 4: Persistence & Restart (10 min)
```bash
# 1. Restart services
docker-compose restart

# 2. Verify templates persisted
curl http://localhost:8080/api/v1/job-templates

# 3. Verify jobs persisted
curl http://localhost:8080/api/v1/jobs
```

## ✨ Success Criteria

All of the following must pass:

- [ ] Docker image builds successfully
- [ ] All services start and become healthy
- [ ] Database initializes without errors
- [ ] API responds to health checks
- [ ] Chef Supermarket templates can be created
- [ ] Chef Supermarket jobs execute successfully
- [ ] Local profile templates can be created
- [ ] Local profile jobs execute successfully
- [ ] Data persists after restart
- [ ] No hardcoded credentials in logs
- [ ] Documentation is complete and accurate
- [ ] Test script runs without errors

## 📝 Notes

### Breaking Changes
- Storage backend default changed from `hybrid` to `database`
- OAuth redirect URI changed from port 8081 to 8080
- Redis removed (if you were using it, migrate data first)
- Environment variables now required (no defaults for sensitive data)

### Migration Path from v0.3.x
1. Backup your data directory
2. Export job templates from old version
3. Update .env with required variables
4. Start new Docker Compose setup
5. Import job templates
6. Verify functionality

### Known Issues
- Streamlit UI disabled (needs Prisma auth update)
- VCS sync requires manual credential setup
- Windows InSpec profiles not fully tested

## 🚀 Ready to Publish?

Check all items in the "Pending Items" section before publishing:

```bash
# Run comprehensive check
./scripts/pre-publish-check.sh

# If all green, proceed with:
# 1. Update version numbers
# 2. Create git tag
# 3. Push to GitHub
# 4. Trigger release workflow
# 5. Publish to PyPI
# 6. Publish to Docker Hub
```

---

**Last Updated**: $(date +%Y-%m-%d)
**Target Release**: v0.4.0
**Estimated Time to Complete**: 2-3 hours
