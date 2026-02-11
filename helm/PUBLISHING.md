# Publishing Helm Chart to Artifact Hub

This guide explains how to publish the ansible-inspec Helm chart to [Artifact Hub](https://artifacthub.io).

## Prerequisites

- ✅ `artifacthub-repo.yml` created at repository root
- ✅ `Chart.yaml` updated with Artifact Hub annotations  
- ✅ Comprehensive `README.md` in chart directory
- ✅ Valid LICENSE file
- ✅ Helm chart repository set up (GitHub Pages or other HTTP server)

## Publishing Steps

### 1. Set Up GitHub Pages Helm Repository

Create a `gh-pages` branch to serve Helm charts:

```bash
# Create gh-pages branch
git checkout --orphan gh-pages
git rm -rf .

# Create index.html (optional)
cat > index.html <<EOF
<!DOCTYPE html>
<html>
<head><title>Ansible-InSpec Helm Charts</title></head>
<body>
<h1>Ansible-InSpec Helm Charts Repository</h1>
<p>Add this repository:</p>
<pre>helm repo add ansible-inspec https://htunn.github.io/ansible-inspec/helm</pre>
</body>
</html>
EOF

# Initialize repository
git add index.html
git commit -m "Initialize Helm repository"
git push origin gh-pages
git checkout main
```

### 2. Package and Publish Helm Chart

```bash
# Navigate to helm directory
cd helm

# Package the chart
helm package ansible-inspec/

# Generate repository index
helm repo index . --url https://htunn.github.io/ansible-inspec/helm

# Commit to gh-pages branch
git checkout gh-pages
git pull origin gh-pages

# Copy package and index
cp helm/ansible-inspec-*.tgz .
cp helm/index.yaml .
cp helm/artifacthub-repo.yml .

# Commit and push
git add .
git commit -m "Release ansible-inspec Helm chart v0.2.6"
git push origin gh-pages

git checkout main
```

### 3. Register Repository on Artifact Hub

1. **Go to Artifact Hub**: Visit [https://artifacthub.io](https://artifacthub.io)

2. **Sign In**: Use GitHub, Google, or OIDC to sign in

3. **Add Repository**:
   - Click your profile → "Control Panel"
   - Go to "Repositories" tab
   - Click "Add repository"
   - Fill in details:
     - **Kind**: Helm charts
     - **Name**: ansible-inspec
     - **Display name**: Ansible-InSpec
     - **URL**: `https://htunn.github.io/ansible-inspec/helm`
     - **Repository type**: Git based (GitHub Pages)

4. **Save**: Click "Add" to register the repository

### 4. Verify Publisher (Optional but Recommended)

To display the "Verified publisher" badge:

1. The `artifacthub-repo.yml` file is already in place at the repository root
2. After adding the repository in Artifact Hub, note the **Repository ID** from the control panel
3. Update `helm/artifacthub-repo.yml` with the `repositoryID`:

```yaml
repositoryID: <your-repo-id-from-artifacthub>
```

4. Commit and push changes:

```bash
git add helm/artifacthub-repo.yml
git commit -m "Add Artifact Hub repository ID for verification"
git push origin main

# Update gh-pages
git checkout gh-pages
cp helm/artifacthub-repo.yml .
git add artifacthub-repo.yml
git commit -m "Update artifacthub-repo.yml with repository ID"
git push origin gh-pages
git checkout main
```

5. Wait for next repository scan (happens automatically when index.yaml changes)
6. Verified publisher badge will appear after successful verification

### 5. Apply for Official Status (Optional)

To get the "Official" badge:

1. Ensure "Verified publisher" status is obtained first
2. Make sure chart README.md is comprehensive
3. File an issue using the [official status request template](https://github.com/artifacthub/hub/issues/new?assignees=&labels=official+status+request&template=official-status-request.md&title=%5BOFFICIAL%5D+ansible-inspec)

## Automation with GitHub Actions

### ✅ Automated Workflows Included

This repository includes two GitHub Actions workflows for Helm chart automation:

#### 1. **Release Workflow** (`.github/workflows/release-helm.yml`)

Automatically publishes Helm charts when you push a git tag:

**Triggers:** Git tags matching `v*` (e.g., `v0.2.6`, `v0.2.7`)

**Actions:**
- 📦 Updates Helm chart dependencies
- 🔨 Packages the chart
- 📤 Pushes to `gh-pages` branch
- 📊 Updates Helm repository index
- 🎉 Creates GitHub Release with chart attachment
- 📝 Generates workflow summary

**Usage:**
```bash
# 1. Update Chart.yaml version and appVersion
# 2. Update changelog in annotations
# 3. Commit changes
git add helm/ansible-inspec/Chart.yaml
git commit -m "Bump chart to v0.2.7"
git push origin main

# 4. Create and push tag
git tag -a v0.2.7 -m "Release v0.2.7"
git push origin v0.2.7

# 5. GitHub Actions automatically:
#    - Packages chart
#    - Updates gh-pages
#    - Creates release
#    - Artifact Hub auto-indexes new version
```

#### 2. **Lint Workflow** (`.github/workflows/helm-lint.yml`)

Validates Helm chart on every push and pull request:

**Triggers:** Changes to `helm/**` files

**Actions:**
- ✅ Runs `helm lint`
- 📋 Validates Chart.yaml required fields
- 🏷️ Checks Artifact Hub annotations
- 🧪 Tests chart templating
- 📦 Verifies chart packages successfully

**Files Checked:**
- `.github/workflows/release-helm.yml` - Release automation
- `.github/workflows/helm-lint.yml` - Chart validation

## Updating the Chart

When releasing a new version:

1. **Update version in `Chart.yaml`**:
   ```yaml
   version: 0.2.7  # Increment
   appVersion: "0.2.7"
   ```

2. **Update annotations with changes**:
   ```yaml
   annotations:
     artifacthub.io/changes: |
       - kind: changed
         description: Updated feature X
       - kind: fixed
         description: Fixed issue Y
   ```

3. **Package and publish**:
   ```bash
   cd helm
   helm package ansible-inspec/
   helm repo index . --url https://htunn.github.io/ansible-inspec/helm
   
   git checkout gh-pages
   cp helm/ansible-inspec-*.tgz .
   cp helm/index.yaml .
   git add .
   git commit -m "Release ansible-inspec v0.2.7"
   git push origin gh-pages
   git checkout main
   ```

4. Artifact Hub will automatically detect the update and index the new version

## Testing the Repository

```bash
# Add repository
helm repo add ansible-inspec https://htunn.github.io/ansible-inspec/helm

# Update repository
helm repo update

# Search for charts
helm search repo ansible-inspec

# Install chart
helm install my-release ansible-inspec/ansible-inspec
```

## Troubleshooting

### Chart not appearing on Artifact Hub

- **Check index.yaml**: Ensure it's accessible at `https://htunn.github.io/ansible-inspec/helm/index.yaml`
- **Check artifacthub-repo.yml**: Must be at `https://htunn.github.io/ansible-inspec/helm/artifacthub-repo.yml`
- **Wait for scan**: Artifact Hub scans repositories periodically (may take a few minutes)
- **Check repository settings**: Ensure repository URL is exactly correct in Artifact Hub

### Verified publisher not showing

- **Repository ID**: Make sure `repositoryID` in `artifacthub-repo.yml` matches Artifact Hub
- **Owner email**: Must match the email of Artifact Hub account
- **File location**: `artifacthub-repo.yml` must be at repository root level
- **Wait for rescan**: Trigger rescan by updating `index.yaml` (change generated timestamp)

### Chart security scanning issues

- Use `whitelisted: true` for base images (like PostgreSQL) in `artifacthub.io/images` annotation
- Provide image platforms for better compatibility information

## Resources

- [Artifact Hub Documentation](https://artifacthub.io/docs/)
- [Helm Charts Repositories Guide](https://artifacthub.io/docs/topics/repositories/helm-charts/)
- [Helm Annotations Reference](https://artifacthub.io/docs/topics/annotations/helm/)
- [artifacthub-repo.yml Specification](https://github.com/artifacthub/hub/blob/master/docs/metadata/artifacthub-repo.yml)

## Support

- **Issues**: [GitHub Issues](https://github.com/Htunn/ansible-inspec/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Htunn/ansible-inspec/discussions)
- **Email**: hello@example.com
