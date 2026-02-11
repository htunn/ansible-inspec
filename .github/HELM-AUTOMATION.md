# Helm Chart Release Automation

This document explains the automated Helm chart release process using GitHub Actions.

## 🚀 Quick Start

### Releasing a New Chart Version

Three simple steps:

```bash
# 1. Update version in Chart.yaml
vim helm/ansible-inspec/Chart.yaml
# Change: version: 0.2.7
# Change: appVersion: "0.2.7"

# 2. Commit changes
git add helm/ansible-inspec/Chart.yaml
git commit -m "Bump Helm chart to v0.2.7"
git push origin main

# 3. Create and push tag
git tag -a v0.2.7 -m "Release v0.2.7"
git push origin v0.2.7

# ✨ GitHub Actions automatically:
#   - Packages the chart
#   - Updates gh-pages branch
#   - Creates GitHub Release
#   - Artifact Hub indexes the new version (5-10 min)
```

## 📋 Automated Workflows

### 1. Release Workflow

**File:** `.github/workflows/release-helm.yml`

**Trigger:** Git tags matching `v*` (e.g., `v0.2.6`, `v0.2.7`, `v1.0.0`)

**What it does:**

1. ✅ Checks out main branch
2. 📦 Updates Helm dependencies (PostgreSQL)
3. 🔨 Packages the chart (`ansible-inspec-X.Y.Z.tgz`)
4. 🔄 Switches to `gh-pages` branch
5. 📤 Copies packaged chart to `helm/` directory
6. 📊 Updates Helm repository index (`index.yaml`)
7. 🚀 Commits and pushes to `gh-pages`
8. 🎉 Creates GitHub Release with chart attachment
9. 📝 Generates workflow summary with installation instructions

**Outputs:**
- Chart package: `https://htunn.github.io/ansible-inspec/helm/ansible-inspec-X.Y.Z.tgz`
- Updated index: `https://htunn.github.io/ansible-inspec/helm/index.yaml`
- GitHub Release: `https://github.com/Htunn/ansible-inspec/releases/tag/vX.Y.Z`

**Monitoring:**
- Go to: https://github.com/Htunn/ansible-inspec/actions
- Click on the workflow run to see detailed logs
- Check the summary for installation commands

### 2. Lint Workflow

**File:** `.github/workflows/helm-lint.yml`

**Trigger:** 
- Push to `main` branch with changes to `helm/**`
- Pull requests with changes to `helm/**`

**What it does:**

1. ✅ Runs `helm lint ansible-inspec/`
2. ✅ Validates Chart.yaml required fields
3. ✅ Checks Artifact Hub annotations
4. ✅ Tests chart templating with `helm template`
5. ✅ Verifies chart packages successfully

**Checks:**
- Required fields: `version`, `appVersion`, `description`
- Artifact Hub annotations: `category`, `changes`, `images`, `links`
- Chart syntax and structure
- Template rendering
- Package creation

## 📝 Release Checklist

Before creating a new release:

### 1. Update Chart.yaml

```yaml
# helm/ansible-inspec/Chart.yaml

# Update version (semver)
version: 0.2.7  # INCREMENT THIS

# Update app version
appVersion: "0.2.7"  # MATCH APPLICATION VERSION

# Update changelog annotation
annotations:
  artifacthub.io/changes: |
    - kind: changed  # or: added, fixed, deprecated, removed, security
      description: What changed in this version
      links:
        - name: GitHub Issue
          url: https://github.com/Htunn/ansible-inspec/issues/123
    - kind: security
      description: Security improvements
```

**Change kinds:**
- `added` - New features
- `changed` - Changes in existing functionality
- `deprecated` - Soon-to-be removed features
- `removed` - Removed features
- `fixed` - Bug fixes
- `security` - Security improvements

### 2. Update Image Tags (if needed)

```yaml
# helm/ansible-inspec/values.yaml
image:
  tag: "0.2.7"  # Update if app version changed

# helm/ansible-inspec/Chart.yaml annotations
annotations:
  artifacthub.io/images: |
    - name: ansible-inspec
      image: docker.io/htunnthuthu/ansible-inspec:0.2.7  # Update tag
      platforms:
        - linux/amd64
        - linux/arm64
```

### 3. Test Locally (Optional but Recommended)

```bash
# Lint the chart
cd helm
helm lint ansible-inspec/

# Template test
helm template test ansible-inspec/ --debug

# Package test
helm package ansible-inspec/

# Install test (requires Kubernetes cluster)
helm install test-release ansible-inspec/ --dry-run --debug
```

### 4. Commit and Tag

```bash
# Commit changes
git add helm/ansible-inspec/
git commit -m "Release Helm chart v0.2.7

- Feature: Added X
- Fixed: Issue with Y
- Security: Improved Z
"

git push origin main

# Create annotated tag
git tag -a v0.2.7 -m "Release v0.2.7

Helm Chart Changes:
- Feature: Added X
- Fixed: Issue with Y
- Security: Improved Z

Application Version: 0.2.7
Chart Version: 0.2.7
"

# Push tag (triggers release workflow)
git push origin v0.2.7
```

### 5. Monitor Release

```bash
# Watch the workflow
# Visit: https://github.com/Htunn/ansible-inspec/actions

# Check gh-pages branch
git fetch origin gh-pages
git log origin/gh-pages -1

# Verify chart is available
helm repo add ansible-inspec https://htunn.github.io/ansible-inspec/helm
helm repo update
helm search repo ansible-inspec

# Expected output:
# NAME                          CHART VERSION   APP VERSION   DESCRIPTION
# ansible-inspec/ansible-inspec 0.2.7          0.2.7         Enterprise compliance...
```

### 6. Verify on Artifact Hub

Wait 5-10 minutes, then check:
- Visit: https://artifacthub.io/packages/search?repo=ansible-inspec
- New version should appear automatically
- Changelog should be visible
- Links should work

## 🔧 Workflow Configuration

### Environment Variables

The workflows use these automatic variables:
- `$GITHUB_ACTOR` - User who triggered the workflow
- `$GITHUB_REF` - Full ref (e.g., `refs/tags/v0.2.7`)
- `$GITHUB_REF_NAME` - Tag name (e.g., `v0.2.7`)
- `$GITHUB_TOKEN` - Auto-provided authentication token

### Permissions

Required permissions (already configured):
- `contents: write` - Push to gh-pages, create releases
- `pages: write` - Update GitHub Pages

### Secrets

No additional secrets required! The workflow uses:
- `${{ secrets.GITHUB_TOKEN }}` - Automatically provided by GitHub

## 🐛 Troubleshooting

### Workflow Fails on Tag Push

**Symptom:** Workflow fails when pushing tag

**Check:**
1. Chart.yaml version matches tag (e.g., tag `v0.2.7` → version `0.2.7`)
2. All dependencies are valid
3. Chart lint passes: `helm lint helm/ansible-inspec/`

**View logs:**
- https://github.com/Htunn/ansible-inspec/actions
- Click on failed workflow run
- Expand failed step to see error

### Chart Not Appearing on Artifact Hub

**Symptom:** New version not showing on Artifact Hub after 10+ minutes

**Solutions:**
1. Check gh-pages was updated:
   ```bash
   curl https://htunn.github.io/ansible-inspec/helm/index.yaml
   ```
2. Verify chart package exists:
   ```bash
   curl -I https://htunn.github.io/ansible-inspec/helm/ansible-inspec-0.2.7.tgz
   ```
3. Manually trigger Artifact Hub scan:
   - Go to: https://artifacthub.io
   - Control Panel → Repositories → ansible-inspec
   - Click "Rescan"

### GitHub Pages Not Updating

**Symptom:** Chart URL returns 404

**Solutions:**
1. Check GitHub Pages settings:
   - https://github.com/Htunn/ansible-inspec/settings/pages
   - Source should be: `gh-pages` branch, `/ (root)` folder
2. Check gh-pages branch exists:
   ```bash
   git ls-remote origin gh-pages
   ```
3. Check workflow permissions:
   - Repository Settings → Actions → General → Workflow permissions
   - Should be: "Read and write permissions"

### Chart Package Corrupted

**Symptom:** Chart downloads but won't install

**Solutions:**
1. Verify chart packaging locally:
   ```bash
   cd helm
   helm package ansible-inspec/
   helm install test ./ansible-inspec-0.2.7.tgz --dry-run
   ```
2. Check dependencies were updated:
   ```bash
   helm dependency list ansible-inspec/
   ```
3. Retrigger workflow:
   ```bash
   # Delete tag and recreate
   git tag -d v0.2.7
   git push origin :refs/tags/v0.2.7
   git tag -a v0.2.7 -m "Release v0.2.7"
   git push origin v0.2.7
   ```

## 📊 Monitoring and Analytics

### GitHub Actions Usage

View workflow runs:
- https://github.com/Htunn/ansible-inspec/actions/workflows/release-helm.yml
- https://github.com/Htunn/ansible-inspec/actions/workflows/helm-lint.yml

### Download Statistics

**Artifact Hub:**
- Control Panel → Repositories → ansible-inspec → Statistics

**GitHub Releases:**
- https://github.com/Htunn/ansible-inspec/releases
- Click on any release to see download counts

**GitHub Pages Traffic:**
- https://github.com/Htunn/ansible-inspec/graphs/traffic

## 🔄 Rollback Procedure

If you need to rollback a release:

### 1. Revert Tag (if needed)

```bash
# Delete remote tag
git push origin :refs/tags/v0.2.7

# Delete local tag
git tag -d v0.2.7
```

### 2. Remove from gh-pages

```bash
# Checkout gh-pages
git checkout gh-pages

# Remove problematic chart
rm helm/ansible-inspec-0.2.7.tgz

# Regenerate index without the version
helm repo index helm --url https://htunn.github.io/ansible-inspec/helm

# Commit and push
git add helm/
git commit -m "Remove broken chart v0.2.7"
git push origin gh-pages

# Back to main
git checkout main
```

### 3. Delete GitHub Release

- Go to: https://github.com/Htunn/ansible-inspec/releases
- Click on the release
- Click "Delete this release"

## 📚 Additional Resources

- **Helm Documentation**: https://helm.sh/docs/
- **Artifact Hub Docs**: https://artifacthub.io/docs/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Semver**: https://semver.org/

## 🎯 Best Practices

1. **Semantic Versioning**: Follow semver (MAJOR.MINOR.PATCH)
   - MAJOR: Breaking changes
   - MINOR: New features (backward compatible)
   - PATCH: Bug fixes

2. **Test Before Release**: Always test locally before tagging
   ```bash
   helm lint helm/ansible-inspec/
   helm install test helm/ansible-inspec/ --dry-run
   ```

3. **Descriptive Commits**: Use meaningful commit messages
   ```bash
   git commit -m "Release v0.2.7: Add new feature X"
   ```

4. **Complete Changelogs**: Update `artifacthub.io/changes` annotation
   - List all significant changes
   - Include links to issues/PRs
   - Use appropriate change kinds

5. **Coordinate with App Releases**: 
   - Chart `appVersion` should match application version
   - Release chart after application is released
   - Tag format: `v` + version (e.g., `v0.2.7`)

6. **Monitor Releases**:
   - Check workflow succeeds
   - Verify chart installs correctly
   - Confirm Artifact Hub indexing

## 🆘 Support

If you encounter issues:

1. **Check Workflow Logs**: https://github.com/Htunn/ansible-inspec/actions
2. **Review Documentation**: [PUBLISHING.md](../helm/PUBLISHING.md)
3. **File an Issue**: https://github.com/Htunn/ansible-inspec/issues
4. **Workflow Files**:
   - [release-helm.yml](../.github/workflows/release-helm.yml)
   - [helm-lint.yml](../.github/workflows/helm-lint.yml)
