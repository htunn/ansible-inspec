# Publishing Setup Complete

## Overview

Your ansible-inspec project is now configured for automated publishing to both PyPI and Docker Hub using GitHub Actions CI/CD.

## What Was Created

### Docker Support

1. **Dockerfile**
   - Multi-stage build for optimized image size
   - Python 3.12 slim base
   - InSpec installation included
   - Non-root user (`ansibleinspec`)
   - Multi-architecture support (AMD64, ARM64)
   - Healthcheck included

2. **.dockerignore**
   - Excludes unnecessary files from Docker builds
   - Reduces image size

3. **docs/DOCKER.md**
   - Comprehensive Docker usage guide
   - Common usage patterns
   - Docker Compose example
   - Troubleshooting tips

### GitHub Actions Workflows

1. **.github/workflows/publish.yml** - PyPI Publishing
   - Triggered by git tags (`v*`)
   - Jobs:
     * `build`: Creates Python distribution packages
     * `publish`: Uploads to PyPI using trusted publishing (no tokens needed!)
     * `verify`: Installs from PyPI and runs tests
   - Fully automated, secure

2. **.github/workflows/docker.yml** - Docker Hub Publishing
   - Triggered by git tags (`v*`), workflow_dispatch, or PRs
   - Jobs:
     * `build`: Multi-arch Docker images (amd64, arm64)
     * `integration-test`: Tests published Docker images
     * `security-scan`: Trivy vulnerability scanning
   - Results uploaded to GitHub Security tab

### Project Configuration

1. **pyproject.toml** - Updated
   - Project URLs updated to use your GitHub (Htunn/ansible-inspec)
   - Docker Hub link added
   - All metadata configured for PyPI

2. **README.md** - Enhanced
   - Added PyPI and Docker badges
   - Installation instructions for PyPI and Docker
   - Docker usage examples
   - Links to new documentation

3. **Makefile**
   - Convenient commands for development
   - `make help` - Show all commands
   - `make build` - Build distribution
   - `make docker-build` - Build Docker image
   - `make docker-test` - Test Docker image

4. **docs/PUBLISHING.md**
   - Complete guide for publishing releases
   - GitHub secrets configuration
   - Step-by-step release process
   - Troubleshooting tips

5. **MANIFEST.in**
   - Controls which files are included in PyPI package

## Required GitHub Secrets

### For Docker Hub

Go to your GitHub repository → Settings → Secrets and variables → Actions

**Secrets** (encrypted):
- `DOCKER_PASSWORD`: Your Docker Hub access token
  * Create at: https://hub.docker.com/settings/security
  * Click "New Access Token"
  * Give it Read, Write, Delete permissions

**Variables** (plain text):
- `DOCKER_USERNAME`: `htunnthuthu`
- `IMAGE_NAME`: `ansible-inspec`

### For PyPI (Trusted Publishing - Recommended)

**No secrets needed!** Just configure the trusted publisher on PyPI:

1. Go to: https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in:
   - **PyPI Project Name**: `ansible-inspec`
   - **Owner**: `Htunn`
   - **Repository name**: `ansible-inspec`
   - **Workflow filename**: `publish.yml`
   - **Environment name**: `pypi`

That's it! No API tokens to manage.

## How to Publish a Release

### Step 1: Update Version

Edit `pyproject.toml`:
```toml
[project]
version = "0.1.0"  # Change to 0.2.0, etc.
```

Edit `lib/ansible_inspec/__init__.py`:
```python
__version__ = "0.1.0"  # Keep in sync
```

### Step 2: Update CHANGELOG

Edit `CHANGELOG.md` and add your changes.

### Step 3: Commit and Tag

```bash
git add pyproject.toml lib/ansible_inspec/__init__.py CHANGELOG.md
git commit -m "chore: bump version to 0.1.0"
git push origin main

# Create tag
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

### Step 4: Watch the Magic! ✨

1. GitHub Actions automatically triggers both workflows
2. Builds packages and Docker images
3. Publishes to PyPI and Docker Hub
4. Runs security scans
5. All within ~5-10 minutes!

### Step 5: Verify

**PyPI:**
```bash
pip install ansible-inspec==0.1.0
ansible-inspec --version
```

**Docker Hub:**
```bash
docker pull htunnthuthu/ansible-inspec:0.1.0
docker run --rm htunnthuthu/ansible-inspec:0.1.0 --version
```

## First-Time Setup Checklist

Before your first release:

- [ ] Create Docker Hub repository: `htunnthuthu/ansible-inspec`
- [ ] Add `DOCKER_PASSWORD` secret to GitHub
- [ ] Add `DOCKER_USERNAME` variable to GitHub
- [ ] Add `IMAGE_NAME` variable to GitHub
- [ ] Configure PyPI trusted publisher (after first manual upload or account setup)
- [ ] Create PyPI account if you don't have one
- [ ] Create repository environment named `pypi` in GitHub settings

## Docker Hub Repository Setup

1. Go to: https://hub.docker.com/
2. Click "Create Repository"
3. Name: `ansible-inspec`
4. Namespace: `htunnthuthu`
5. Visibility: Public
6. Click "Create"

## PyPI Account Setup

If you need to create the project initially:

1. Create account at: https://pypi.org/
2. Enable 2FA (required for new projects)
3. **Option A - Manual first upload:**
   ```bash
   python -m build
   pip install twine
   twine upload dist/*
   ```
4. **Option B - Use TestPyPI first:**
   ```bash
   twine upload --repository testpypi dist/*
   ```

After the first upload, configure trusted publishing (see above).

## Testing Before Release

### Test Docker Build Locally

```bash
# Build
make docker-build

# Test
make docker-test

# Or manually:
docker run --rm ansible-inspec:local --version
docker run --rm -v $(pwd):/workspace ansible-inspec:local init profile test
```

### Test Package Build Locally

```bash
# Build
make build

# Inspect
ls -lh dist/

# Install locally
pip install dist/ansible_inspec-0.1.0-py3-none-any.whl

# Test
ansible-inspec --version
```

### Test Workflows Without Publishing

Pull requests trigger the workflows without publishing:

```bash
git checkout -b test-workflows
git push origin test-workflows
# Create PR on GitHub
```

This will:
- Build packages (no publish)
- Build Docker images (no push to Docker Hub)
- Run all tests

## Directory Structure

```
ansible-inspec/
├── .github/
│   └── workflows/
│       ├── publish.yml      # PyPI publishing
│       └── docker.yml       # Docker Hub publishing
├── docs/
│   ├── DOCKER.md           # Docker usage guide
│   └── PUBLISHING.md       # Publishing guide
├── Dockerfile              # Multi-stage Docker build
├── .dockerignore          # Docker build exclusions
├── Makefile               # Development commands
├── MANIFEST.in            # PyPI package inclusions
└── pyproject.toml         # Updated with URLs
```

## Support

- **Documentation**: See `docs/PUBLISHING.md` for detailed guides
- **Docker Guide**: See `docs/DOCKER.md` for Docker usage
- **GitHub Workflows**: Check `.github/workflows/` for automation details

## Next Steps

1. Set up GitHub secrets (Docker Hub token)
2. Set up GitHub variables (Docker username, image name)
3. Create Docker Hub repository
4. Configure PyPI trusted publisher
5. Test everything with your first release!

Happy publishing! 🚀
