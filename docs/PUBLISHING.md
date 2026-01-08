# Publishing Guide

This guide explains how to publish ansible-inspec to PyPI and Docker Hub.

## Prerequisites

### PyPI Publishing
- GitHub repository with appropriate secrets configured
- PyPI account with 2FA enabled
- Trusted publisher configured on PyPI (recommended)

### Docker Hub Publishing
- Docker Hub account
- Repository created: `htunnthuthu/ansible-inspec`
- GitHub secrets configured

## GitHub Secrets Configuration

Configure these secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

### For PyPI (Trusted Publishing - Recommended)
No secrets needed! Just configure the trusted publisher on PyPI:

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new publisher with:
   - PyPI Project Name: `ansible-inspec`
   - Owner: `Htunn`
   - Repository: `ansible-inspec`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`

### For Docker Hub

Add these as **Repository secrets**:
- `DOCKER_PASSWORD`: Your Docker Hub access token

Add these as **Repository variables**:
- `DOCKER_USERNAME`: Your Docker Hub username (e.g., `htunnthuthu`)
- `IMAGE_NAME`: `ansible-inspec`

## Release Process

### 1. Update Version

Edit `pyproject.toml`:
```toml
[project]
version = "0.2.0"  # Increment version
```

Update `lib/ansible_inspec/__init__.py`:
```python
__version__ = "0.2.0"
```

### 2. Update CHANGELOG

Create/update `CHANGELOG.md`:
```markdown
# Changelog

## [0.2.0] - 2026-01-08

### Added
- New feature X
- Enhancement Y

### Fixed
- Bug fix Z

### Changed
- Updated dependency versions
```

### 3. Commit Changes

```bash
git add pyproject.toml lib/ansible_inspec/__init__.py CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
git push origin main
```

### 4. Create and Push Git Tag

```bash
# Create annotated tag
git tag -a v0.2.0 -m "Release version 0.2.0"

# Push tag to trigger workflows
git push origin v0.2.0
```

This will trigger both workflows:
- `.github/workflows/publish.yml` - Publishes to PyPI
- `.github/workflows/docker.yml` - Publishes to Docker Hub

### 5. Monitor Workflows

1. Go to GitHub Actions tab
2. Watch both workflows execute:
   - **Publish to PyPI**: Builds, publishes, verifies
   - **Build and Push Docker Image**: Builds multi-arch images, tests, scans

### 6. Verify Release

After workflows complete:

**PyPI:**
```bash
pip install ansible-inspec==0.2.0
ansible-inspec --version
```

**Docker Hub:**
```bash
docker pull htunnthuthu/ansible-inspec:0.2.0
docker run --rm htunnthuthu/ansible-inspec:0.2.0 --version
```

## Manual Publishing (Fallback)

### PyPI Manual Publishing

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Upload to PyPI (requires API token)
twine upload dist/*
```

### Docker Manual Publishing

```bash
# Build multi-arch image
docker buildx create --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag htunnthuthu/ansible-inspec:0.2.0 \
  --tag htunnthuthu/ansible-inspec:latest \
  --push \
  .
```

## Workflow Details

### PyPI Workflow (`publish.yml`)

Triggered by: Git tags matching `v*`

Jobs:
1. **build**: Creates Python distribution packages (wheel + sdist)
2. **publish**: Uploads to PyPI using trusted publishing
3. **verify**: Installs from PyPI and runs smoke tests

### Docker Workflow (`docker.yml`)

Triggered by:
- Git tags matching `v*`
- Manual workflow dispatch
- Pull requests (build only, no push)

Jobs:
1. **build**: Builds multi-arch images, pushes to Docker Hub
2. **integration-test**: Runs functional tests on published images
3. **security-scan**: Scans images with Trivy, uploads results to GitHub Security

## Troubleshooting

### PyPI Publishing Fails

**Trusted publisher not configured:**
- Configure at https://pypi.org/manage/account/publishing/

**Version already exists:**
- Increment version number
- Cannot replace existing versions on PyPI

**Build artifacts missing:**
- Check if `build` job completed successfully
- Verify `dist/` directory contains `.whl` and `.tar.gz` files

### Docker Publishing Fails

**Authentication failed:**
- Verify `DOCKER_PASSWORD` secret is correct
- Ensure Docker Hub token has write permissions

**Multi-arch build fails:**
- Check if both amd64 and arm64 builds succeed
- Review build logs for platform-specific errors

**Image tests fail:**
- Verify Dockerfile CMD/ENTRYPOINT is correct
- Check if InSpec installation succeeded

## Version Management

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Incompatible API changes
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible

Example workflow:
- `v0.1.0` → `v0.1.1` (bug fix)
- `v0.1.1` → `v0.2.0` (new feature)
- `v0.2.0` → `v1.0.0` (breaking change)

## Release Checklist

- [ ] Version updated in `pyproject.toml`
- [ ] Version updated in `lib/ansible_inspec/__init__.py`
- [ ] CHANGELOG.md updated
- [ ] All tests passing locally
- [ ] Documentation updated
- [ ] Git tag created with `v` prefix
- [ ] Tag pushed to GitHub
- [ ] Both workflows completed successfully
- [ ] PyPI package verified
- [ ] Docker images verified
- [ ] GitHub release created (optional)
- [ ] Announcement prepared (optional)

## GitHub Release (Optional)

After workflows complete:

1. Go to GitHub repository → Releases
2. Click "Draft a new release"
3. Choose tag: `v0.2.0`
4. Release title: `v0.2.0 - Brief description`
5. Description: Copy relevant CHANGELOG entries
6. Attach build artifacts if needed
7. Publish release

## Security Scanning

All published Docker images are automatically scanned:
- **Trivy**: Vulnerability scanning
- Results uploaded to GitHub Security tab
- Review: Settings → Security → Code scanning alerts

## Support

For publishing issues:
- GitHub Discussions: https://github.com/Htunn/ansible-inspec/discussions
- Issues: https://github.com/Htunn/ansible-inspec/issues
