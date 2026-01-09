# Publishing ansible-inspec

Complete guide for publishing ansible-inspec to PyPI and Docker Hub.

## Table of Contents

- [Quick Start](#quick-start)
- [PyPI Publishing](#pypi-publishing)
- [Docker Publishing](#docker-publishing)
- [Version Management](#version-management)
- [Release Checklist](#release-checklist)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

**For PyPI:**
- GitHub repository configured with PyPI trusted publishing
- PyPI account with 2FA enabled
- Write access to ansible-inspec repository

**For Docker:**
- Docker Hub account
- Repository created: `htunnthuthu/ansible-inspec`
- GitHub repository secrets configured

### One-Command Release

```bash
# 1. Update version and changelog
vim pyproject.toml  # Update version
vim lib/ansible_inspec/__init__.py  # Update __version__
vim CHANGELOG.md  # Document changes

# 2. Commit and tag
git add .
git commit -m "chore: release version 0.2.0"
git push origin main

# 3. Create and push tag (triggers automatic publishing)
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

**That's it!** GitHub Actions will automatically:
1. Build Python package
2. Publish to PyPI
3. Build Docker images (amd64 + arm64)
4. Push to Docker Hub
5. Run security scans
6. Validate installations

---

## PyPI Publishing

### Automated Publishing (Recommended)

#### Setup PyPI Trusted Publishing

1. **Go to PyPI**: https://pypi.org/manage/account/publishing/

2. **Add New Publisher**:
   - **PyPI Project Name**: `ansible-inspec`
   - **Owner**: `Htunn`
   - **Repository name**: `ansible-inspec`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

3. **Save** - No API tokens needed!

#### Publish New Version

```bash
# Update version in pyproject.toml
[project]
version = "0.2.0"

# Update version in source
# lib/ansible_inspec/__init__.py
__version__ = "0.2.0"

# Commit changes
git add pyproject.toml lib/ansible_inspec/__init__.py CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
git push origin main

# Create and push tag
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

#### Publishing Workflow

The `.github/workflows/publish.yml` workflow:

1. **Build Job**: 
   - Builds wheel and source distribution
   - Validates package metadata
   - Uploads artifacts

2. **Publish Job**:
   - Uses trusted publishing (no tokens!)
   - Publishes to PyPI
   - Runs in `pypi` environment

3. **Verify Job**:
   - Waits for PyPI propagation (2 minutes)
   - Installs package from PyPI
   - Runs smoke tests

**Monitor**: https://github.com/Htunn/ansible-inspec/actions/workflows/publish.yml

### Manual PyPI Publishing

If automated publishing fails:

```bash
# Install tools
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*

# Upload to TestPyPI (test first!)
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ ansible-inspec

# Upload to PyPI
twine upload dist/*
```

**Requires**: PyPI API token in `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...

[testpypi]
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZw...
```

### Verify PyPI Release

```bash
# Install from PyPI
pip install ansible-inspec==0.2.0

# Test
ansible-inspec --version
ansible-inspec --help
ansible-inspec init profile test-profile

# Check package page
open https://pypi.org/project/ansible-inspec/
```

---

## Docker Publishing

### Automated Docker Publishing

#### Setup Docker Hub

1. **Create Repository**: https://hub.docker.com/repository/create
   - **Namespace**: `htunnthuthu`
   - **Name**: `ansible-inspec`
   - **Visibility**: Public
   - **Description**: Compliance testing with Ansible and InSpec

2. **Create Access Token**: https://hub.docker.com/settings/security
   - **Description**: `GitHub Actions - ansible-inspec`
   - **Permissions**: Read, Write, Delete
   - **Copy token** (shown once!)

3. **Configure GitHub Secrets**: https://github.com/Htunn/ansible-inspec/settings/secrets/actions
   - **Add secret**: `DOCKER_PASSWORD` = `<your-docker-token>`
   - **Add variable**: `DOCKER_USERNAME` = `htunnthuthu`
   - **Add variable**: `IMAGE_NAME` = `ansible-inspec`

#### Publish Docker Image

Same process as PyPI - **just push a tag**:

```bash
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

#### Docker Workflow

The `.github/workflows/docker.yml` workflow:

1. **Build Job**:
   - Builds multi-architecture images (amd64, arm64)
   - Extracts version from `pyproject.toml`
   - Tags with version and `latest`
   - Pushes to Docker Hub
   - Caches layers for faster builds

2. **Integration Test Job**:
   - Pulls published image
   - Tests basic functionality
   - Validates version output
   - Tests profile creation

3. **Security Scan Job**:
   - Scans image with Trivy
   - Uploads results to GitHub Security
   - Checks for vulnerabilities

**Monitor**: https://github.com/Htunn/ansible-inspec/actions/workflows/docker.yml

### Docker Image Tags

Published images get multiple tags:

```bash
# Version tags
htunnthuthu/ansible-inspec:0.2.0    # Full version
htunnthuthu/ansible-inspec:0.2      # Minor version
htunnthuthu/ansible-inspec:0        # Major version
htunnthuthu/ansible-inspec:latest   # Latest stable

# Branch tags (if pushed from main)
htunnthuthu/ansible-inspec:main

# PR tags (testing only, not pushed)
htunnthuthu/ansible-inspec:pr-123
```

### Manual Docker Publishing

If automated publishing fails:

```bash
# Login to Docker Hub
docker login
# Username: htunnthuthu
# Password: <paste token>

# Build for local architecture
docker build -t htunnthuthu/ansible-inspec:0.2.0 .

# Test locally
docker run --rm htunnthuthu/ansible-inspec:0.2.0 --version

# Push single architecture
docker push htunnthuthu/ansible-inspec:0.2.0

# Tag as latest
docker tag htunnthuthu/ansible-inspec:0.2.0 htunnthuthu/ansible-inspec:latest
docker push htunnthuthu/ansible-inspec:latest
```

#### Multi-Architecture Build (Recommended)

```bash
# Create buildx builder
docker buildx create --name multiarch --use

# Build and push multi-arch
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag htunnthuthu/ansible-inspec:0.2.0 \
  --tag htunnthuthu/ansible-inspec:latest \
  --push \
  .
```

### Verify Docker Release

```bash
# Pull image
docker pull htunnthuthu/ansible-inspec:0.2.0

# Test basic functionality
docker run --rm htunnthuthu/ansible-inspec:0.2.0 --version
docker run --rm htunnthuthu/ansible-inspec:0.2.0 --help

# Test profile creation
docker run --rm -v $(pwd):/workspace \
  htunnthuthu/ansible-inspec:0.2.0 \
  init profile test-profile

# Check Docker Hub page
open https://hub.docker.com/r/htunnthuthu/ansible-inspec
```

---

## Version Management

### Semantic Versioning

ansible-inspec follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (0.x.x): Breaking changes
- **MINOR** (x.1.x): New features, backwards compatible
- **PATCH** (x.x.1): Bug fixes, backwards compatible

### Files to Update

When bumping version, update **3 files**:

#### 1. `pyproject.toml`

```toml
[project]
version = "0.2.0"  # <-- Update here
```

#### 2. `lib/ansible_inspec/__init__.py`

```python
__version__ = "0.2.0"  # <-- Update here
```

#### 3. `CHANGELOG.md`

```markdown
# Changelog

## [0.2.0] - 2026-01-10

### Added
- New reporter modes documentation
- InSpec-free compliance testing
- Multi-format report export

### Fixed
- E2E test improvements
- Error handling in HTML reports

### Changed
- Updated dependencies
```

### Version Consistency Check

```bash
# Check all versions match
grep -r "0.2.0" pyproject.toml lib/ansible_inspec/__init__.py CHANGELOG.md

# Should show:
# pyproject.toml:version = "0.2.0"
# lib/ansible_inspec/__init__.py:__version__ = "0.2.0"
# CHANGELOG.md:## [0.2.0] - 2026-01-10
```

---

## Release Checklist

Use this checklist for every release:

### Pre-Release

- [ ] All tests passing: `make test`
- [ ] E2E tests passing: `bash tests/e2e_test.sh`
- [ ] Code quality checks: `make lint`
- [ ] Documentation updated
- [ ] CHANGELOG.md updated with changes
- [ ] Version bumped in 3 files (pyproject.toml, __init__.py, CHANGELOG.md)
- [ ] Versions consistent across files

### Release

- [ ] Create feature branch: `git checkout -b release/v0.2.0`
- [ ] Commit version bump: `git commit -m "chore: bump version to 0.2.0"`
- [ ] Push branch: `git push origin release/v0.2.0`
- [ ] Create PR to main
- [ ] Review and merge PR
- [ ] Pull main: `git checkout main && git pull`
- [ ] Create tag: `git tag -a v0.2.0 -m "Release version 0.2.0"`
- [ ] Push tag: `git push origin v0.2.0`

### Post-Release

- [ ] Monitor PyPI workflow: https://github.com/Htunn/ansible-inspec/actions/workflows/publish.yml
- [ ] Monitor Docker workflow: https://github.com/Htunn/ansible-inspec/actions/workflows/docker.yml
- [ ] Verify PyPI: `pip install ansible-inspec==0.2.0`
- [ ] Verify Docker: `docker pull htunnthuthu/ansible-inspec:0.2.0`
- [ ] Check PyPI page: https://pypi.org/project/ansible-inspec/
- [ ] Check Docker Hub: https://hub.docker.com/r/htunnthuthu/ansible-inspec
- [ ] Create GitHub Release: https://github.com/Htunn/ansible-inspec/releases/new
  - Tag: `v0.2.0`
  - Title: `Release v0.2.0`
  - Description: Copy from CHANGELOG.md
  - Attach: `dist/*.tar.gz` and `dist/*.whl`

---

## Troubleshooting

### PyPI Issues

#### Trusted Publisher Not Working

**Error**: `Publishing to PyPI failed`

**Solution**:
1. Verify trusted publisher configured at https://pypi.org/manage/account/publishing/
2. Check settings match:
   - PyPI Project Name: `ansible-inspec`
   - Owner: `Htunn`
   - Repository: `ansible-inspec`
   - Workflow: `publish.yml`
   - Environment: `pypi`

#### Version Already Exists

**Error**: `File already exists`

**Solution**:
- PyPI doesn't allow overwriting versions
- Bump version number and retry
- Delete and recreate tag:
  ```bash
  git tag -d v0.2.0
  git push origin :refs/tags/v0.2.0
  # Update version, commit, create new tag
  ```

#### Build Fails

**Error**: `No module named 'setuptools'`

**Solution**:
```toml
# Ensure pyproject.toml has build system
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"
```

### Docker Issues

#### Authentication Failed

**Error**: `denied: requested access to the resource is denied`

**Solution**:
1. Regenerate Docker Hub access token
2. Update GitHub secret `DOCKER_PASSWORD`
3. Ensure token has **Read, Write** permissions

#### Multi-Arch Build Fails

**Error**: `Multiple platforms feature is currently not supported for docker driver`

**Solution**:
- Automated workflow uses `buildx` - no action needed
- For manual builds:
  ```bash
  docker buildx create --name multiarch --use
  docker buildx inspect --bootstrap
  ```

#### Image Too Large

**Warning**: Docker image > 1GB

**Solution**:
- Review Dockerfile
- Use `.dockerignore`
- Multi-stage builds
- Minimize layers

```dockerfile
# .dockerignore
.git
.venv
__pycache__
*.pyc
tests/
docs/
.github/
```

#### Security Scan Failures

**Error**: Trivy found critical vulnerabilities

**Solution**:
1. Review scan results in GitHub Security tab
2. Update base image: `FROM python:3.12-slim`
3. Update dependencies in `pyproject.toml`
4. Rebuild and rescan

### GitHub Actions Issues

#### Workflow Not Triggering

**Problem**: Tag pushed but workflows didn't run

**Solution**:
1. Check tag format: must be `v*` (e.g., `v0.2.0`)
2. Verify workflows enabled: Repo → Actions → Enable workflows
3. Check workflow file syntax:
   ```bash
   actionlint .github/workflows/*.yml
   ```

#### Secrets Not Available

**Error**: `secrets.DOCKER_PASSWORD not found`

**Solution**:
1. Go to Repo → Settings → Secrets and variables → Actions
2. Add repository secret: `DOCKER_PASSWORD`
3. Add repository variable: `DOCKER_USERNAME`

#### Timeout Issues

**Error**: Workflow timeout after 6 hours

**Solution**:
- Check for hanging commands
- Review build cache usage
- Optimize test suite
- Add timeout to jobs:
  ```yaml
  jobs:
    build:
      timeout-minutes: 30
  ```

### General Issues

#### Version Mismatch

**Problem**: PyPI shows different version than Docker

**Solution**:
```bash
# Check version in all locations
python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
python -c "import sys; sys.path.insert(0, 'lib'); from ansible_inspec import __version__; print(__version__)"
git describe --tags --abbrev=0
```

#### Dependencies Out of Date

**Problem**: Build warnings about deprecated packages

**Solution**:
```bash
# Update dependencies
pip install --upgrade pip setuptools wheel
pip-compile --upgrade pyproject.toml  # if using pip-tools

# Test with new versions
pip install -e .[dev]
make test
```

---

## Workflow Files

### PyPI Workflow

`.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - "v*"

permissions:
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
```

### Docker Workflow

`.github/workflows/docker.yml`:

```yaml
name: Build and Push Docker Image

on:
  push:
    tags:
      - "v*"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ vars.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - uses: docker/build-push-action@v5
        with:
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ${{ vars.DOCKER_USERNAME }}/ansible-inspec:${{ github.ref_name }}
            ${{ vars.DOCKER_USERNAME }}/ansible-inspec:latest
```

---

## Support

- **Issues**: https://github.com/Htunn/ansible-inspec/issues
- **Discussions**: https://github.com/Htunn/ansible-inspec/discussions
- **PyPI**: https://pypi.org/project/ansible-inspec/
- **Docker Hub**: https://hub.docker.com/r/htunnthuthu/ansible-inspec

---

## License

GPL-3.0-or-later
