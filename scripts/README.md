# Release Scripts

Automation scripts for managing ansible-inspec releases.

## release.sh

Automated release script that handles version bumping, changelog updates, and git tagging.

### Usage

```bash
# Interactive mode (prompts for version and changelog)
./scripts/release.sh

# With version argument (still prompts for changelog)
./scripts/release.sh 0.1.2
```

### What it does

1. **Validates environment**
   - Checks git repository
   - Warns about uncommitted changes
   - Shows current version

2. **Updates version**
   - Updates `pyproject.toml` with new version
   - Uses semantic versioning (MAJOR.MINOR.PATCH)

3. **Updates changelog**
   - Prompts for changelog entries
   - Adds new version section to `CHANGELOG.md`
   - Includes current date

4. **Reviews changes**
   - Shows diff of changes
   - Asks for confirmation before committing

5. **Creates commit and tag**
   - Commits version bump and changelog
   - Creates annotated git tag (e.g., `v0.1.2`)
   - Optionally pushes to remote

6. **Triggers CI/CD**
   - Docker workflow builds multi-arch images
   - PyPI workflow publishes to PyPI
   - Both trigger automatically on tag push

### Example Session

```bash
$ ./scripts/release.sh 0.1.2
========================================
ansible-inspec Release Script
========================================

Current version: 0.1.1

New version: 0.1.2

Create release v0.1.2? (y/N): y

Step 1: Updating pyproject.toml
✓ Updated pyproject.toml to version 0.1.2

Step 2: Updating CHANGELOG.md
Enter changelog entry (press Ctrl+D when done):
Example:
### Added
- New feature X

### Fixed
- Bug fix Y

### Fixed
- Fixed critical bug in Supermarket integration
^D

✓ Updated CHANGELOG.md

Step 3: Review changes
[Shows diff]

Commit these changes? (y/N): y

Step 4: Committing changes
✓ Committed version bump

Step 5: Creating git tag
Enter tag message (optional, press Enter to use default):
Release with bug fixes
✓ Created tag v0.1.2

Step 6: Pushing to remote
Push to origin (main + tag)? (y/N): y
✓ Pushed to remote

========================================
Release v0.1.2 created successfully!
========================================

Next steps:
  1. Docker workflow will auto-build and push to Docker Hub
  2. PyPI workflow will auto-publish to PyPI
  3. Monitor workflows at: https://github.com/Htunn/ansible-inspec/actions
```

### Version Format

Uses [Semantic Versioning](https://semver.org/):
- **MAJOR** version: Incompatible API changes
- **MINOR** version: New features (backward-compatible)
- **PATCH** version: Bug fixes (backward-compatible)

### Changelog Format

Follows [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security fixes
```

### CI/CD Workflows

After pushing the tag, these workflows trigger automatically:

1. **Docker Workflow** (`.github/workflows/docker.yml`)
   - Builds multi-arch images (linux/amd64, linux/arm64)
   - Pushes to Docker Hub with tags:
     - `htunnthuthu/ansible-inspec:latest`
     - `htunnthuthu/ansible-inspec:0.1.2`
     - `htunnthuthu/ansible-inspec:0.1`
     - `htunnthuthu/ansible-inspec:0`
     - `htunnthuthu/ansible-inspec:main`

2. **PyPI Workflow** (`.github/workflows/publish.yml`)
   - Builds Python package
   - Publishes to PyPI
   - Verifies installation

### Troubleshooting

**"Error: Invalid version format"**
- Use semantic versioning: `MAJOR.MINOR.PATCH`
- Example: `0.1.2`, not `v0.1.2` or `0.1`

**"Error: Not in a git repository"**
- Run from within the repository
- Ensure `.git` directory exists

**PyPI upload fails with "File already exists"**
- Version already published
- Increment version number
- Cannot republish same version to PyPI

**Docker build fails**
- Check Docker Hub credentials in GitHub secrets
- Verify `DOCKER_PASSWORD` is set in `pypi` environment

### Manual Release (if needed)

If the script fails or you need manual control:

```bash
# 1. Update version
vim pyproject.toml  # Change version = "0.1.2"

# 2. Update changelog
vim CHANGELOG.md    # Add new version section

# 3. Commit
git add pyproject.toml CHANGELOG.md
git commit -m "chore: Bump version to 0.1.2"

# 4. Tag
git tag -a v0.1.2 -m "Release version 0.1.2"

# 5. Push
git push origin main
git push origin v0.1.2
```

### Rollback

If you need to undo a release (before pushing):

```bash
# Undo commit
git reset --hard HEAD~1

# Delete tag
git tag -d v0.1.2
```

If already pushed:

```bash
# Delete remote tag
git push origin :refs/tags/v0.1.2

# Force push to revert commit (use with caution!)
git push origin main --force
```

⚠️ **Warning**: Cannot delete PyPI releases. Once published, a version is permanent.
