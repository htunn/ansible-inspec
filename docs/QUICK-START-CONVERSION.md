# Quick Start: Profile Conversion Examples

This guide shows common scenarios for converting InSpec profiles to Ansible collections.

## Example 1: Basic Profile Conversion

Convert a simple InSpec profile with standard resources:

```bash
# Create a basic InSpec profile
mkdir -p myprofile/controls
cat > myprofile/inspec.yml << 'EOF'
name: myprofile
title: My Compliance Profile
version: 1.0.0
EOF

cat > myprofile/controls/basic.rb << 'EOF'
control 'basic-1' do
  impact 1.0
  title 'Basic security checks'
  
  describe package('openssh-server') do
    it { should be_installed }
  end
  
  describe service('sshd') do
    it { should be_running }
  end
end
EOF

# Convert to Ansible collection
ansible-inspec convert myprofile

# Result: collections/ansible_collections/compliance/inspec_profiles/
```

## Example 2: Chef Supermarket Profile

Convert a popular security baseline from Chef Supermarket:

```bash
# Download DevSec Linux Baseline
ansible-inspec exec dev-sec/linux-baseline --supermarket --download ./profiles

# Convert to Ansible collection
ansible-inspec convert ./profiles/linux-baseline \
  --namespace devsec \
  --collection-name linux_baseline \
  --output-dir ./my-collections

# Build and install
cd my-collections/ansible_collections/devsec/linux_baseline
ansible-galaxy collection build
ansible-galaxy collection install *.tar.gz

# Use in playbook
cat > check-compliance.yml << 'EOF'
- name: Linux Security Baseline
  hosts: all
  become: true
  roles:
    - devsec.linux_baseline.controls
EOF

ansible-playbook check-compliance.yml -i inventory.yml
```

## Example 3: Profile with Custom Resources

Convert a complex profile that uses custom resources:

```bash
# Your existing InSpec profile structure:
# custom-app-profile/
# ├── inspec.yml
# ├── controls/
# │   ├── app-config.rb
# │   └── app-security.rb
# └── libraries/
#     └── app_resource.rb

# Convert (preserves custom resources)
ansible-inspec convert custom-app-profile \
  --namespace mycompany \
  --collection-name app_compliance

# The converter will:
# 1. Copy libraries/app_resource.rb to collection
# 2. Generate InSpec wrapper tasks for custom resource usage
# 3. Generate native Ansible tasks for standard resources
# 4. Create complete collection structure

# Install InSpec (required for custom resources)
brew install chef/chef/inspec  # macOS
# or
curl https://omnitruck.chef.io/install.sh | sudo bash -s -- -P inspec  # Linux

# Use the collection
ansible-galaxy collection install \
  ./collections/ansible_collections/mycompany/app_compliance/*.tar.gz
```

## Example 4: Corporate Security Baseline

Create and convert an organization-wide security baseline:

```bash
# Create corporate baseline
mkdir -p acme-baseline/controls

cat > acme-baseline/inspec.yml << 'EOF'
name: acme-baseline
title: ACME Corp Security Baseline
version: 1.0.0
maintainer: ACME Security Team
copyright: ACME Corp
license: Proprietary
summary: Corporate security and compliance requirements
EOF

cat > acme-baseline/controls/users.rb << 'EOF'
control 'acme-users-1' do
  impact 1.0
  title 'Ensure no unauthorized users exist'
  
  describe file('/etc/passwd') do
    its('content') { should_not match /unauthorized/ }
  end
end
EOF

cat > acme-baseline/controls/network.rb << 'EOF'
control 'acme-network-1' do
  impact 0.8
  title 'Ensure firewall is enabled'
  
  describe service('firewalld') do
    it { should be_running }
    it { should be_enabled }
  end
end
EOF

# Convert to private collection
ansible-inspec convert acme-baseline \
  --namespace acme \
  --collection-name security_baseline \
  --output-dir /opt/ansible/collections

# Build for distribution
cd /opt/ansible/collections/ansible_collections/acme/security_baseline
ansible-galaxy collection build

# Publish to private Ansible Galaxy
ansible-galaxy collection publish \
  acme-security_baseline-1.0.0.tar.gz \
  --server https://galaxy.acme.internal
```

## Example 5: CI/CD Integration

Automate profile conversion in CI/CD pipeline:

```bash
#!/bin/bash
# ci/convert-profiles.sh

set -e

PROFILES_DIR="./inspec-profiles"
OUTPUT_DIR="./ansible-collections"
NAMESPACE="acme"

for profile in "$PROFILES_DIR"/*; do
  if [ -d "$profile" ]; then
    profile_name=$(basename "$profile")
    collection_name="${profile_name//-/_}"  # Replace - with _
    
    echo "Converting $profile_name..."
    
    ansible-inspec convert "$profile" \
      --namespace "$NAMESPACE" \
      --collection-name "$collection_name" \
      --output-dir "$OUTPUT_DIR"
    
    # Build collection
    collection_path="$OUTPUT_DIR/ansible_collections/$NAMESPACE/$collection_name"
    cd "$collection_path"
    ansible-galaxy collection build
    
    # Upload to artifact repository
    aws s3 cp *.tar.gz s3://my-ansible-collections/
    
    cd -
  fi
done

echo "All profiles converted successfully!"
```

**GitHub Actions Example:**

```yaml
# .github/workflows/convert-profiles.yml
name: Convert InSpec Profiles

on:
  push:
    paths:
      - 'inspec-profiles/**'

jobs:
  convert:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install ansible-inspec
        run: pip install ansible-inspec
      
      - name: Convert profiles
        run: |
          for profile in inspec-profiles/*; do
            ansible-inspec convert "$profile" \
              --namespace myorg \
              --collection-name "$(basename $profile)"
          done
      
      - name: Build collections
        run: |
          cd collections/ansible_collections/myorg
          for collection in */; do
            cd "$collection"
            ansible-galaxy collection build
            cd ..
          done
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: ansible-collections
          path: collections/**/*.tar.gz
```

## Example 6: Testing Converted Collections

Verify your converted collection works correctly:

```bash
# Convert profile
ansible-inspec convert myprofile \
  --namespace test \
  --collection-name myprofile

# Install locally
cd collections/ansible_collections/test/myprofile
ansible-galaxy collection build
ansible-galaxy collection install *.tar.gz --force

# Create test playbook
cat > test-playbook.yml << 'EOF'
- name: Test converted collection
  hosts: localhost
  connection: local
  become: false
  roles:
    - test.myprofile.basic
EOF

# Run compliance checks
ansible-playbook test-playbook.yml -vv

# Check results
echo "Exit code: $?"  # 0 = all tests passed, 2 = some tests failed
```

## Example 7: Migrating Multiple Profiles

Convert an entire directory of InSpec profiles:

```bash
#!/bin/bash
# migrate-all-profiles.sh

INSPEC_DIR="/opt/inspec-profiles"
ANSIBLE_DIR="/opt/ansible-collections"
NAMESPACE="security"

# Create output directory
mkdir -p "$ANSIBLE_DIR"

# Convert each profile
for profile_path in "$INSPEC_DIR"/*; do
  if [ ! -d "$profile_path" ]; then
    continue
  fi
  
  profile_name=$(basename "$profile_path")
  collection_name="${profile_name//-/_}"
  
  echo "================================================================"
  echo "Converting: $profile_name"
  echo "================================================================"
  
  # Convert
  ansible-inspec convert "$profile_path" \
    --namespace "$NAMESPACE" \
    --collection-name "$collection_name" \
    --output-dir "$ANSIBLE_DIR"
  
  if [ $? -eq 0 ]; then
    echo "✓ Successfully converted $profile_name"
    
    # Build collection
    collection_path="$ANSIBLE_DIR/ansible_collections/$NAMESPACE/$collection_name"
    (cd "$collection_path" && ansible-galaxy collection build)
    
    echo "✓ Built collection: $collection_name"
  else
    echo "✗ Failed to convert $profile_name"
  fi
  
  echo ""
done

# Create collection list
echo "================================================================"
echo "Converted Collections:"
echo "================================================================"
find "$ANSIBLE_DIR" -name "*.tar.gz" -type f
```

## Example 8: Using Conversion Scripts

Use the provided helper script:

```bash
# Simple conversion
./examples/convert_profile.sh examples/profiles/custom-compliance

# Custom namespace and name
./examples/convert_profile.sh \
  /path/to/inspec/profile \
  ./my-output-dir \
  myorg \
  my_collection

# The script will:
# 1. Analyze the InSpec profile
# 2. Convert to Ansible collection
# 3. Build the collection tarball
# 4. Show collection structure
# 5. Provide usage instructions
```

## Common Conversion Options

### Native-Only Mode

Generate only native Ansible tasks (skip custom resources):

```bash
ansible-inspec convert myprofile --native-only

# Use when:
# - Profile has no custom resources
# - Want pure Ansible implementation
# - Avoiding InSpec dependency
```

### Skip Roles

Generate collection without roles:

```bash
ansible-inspec convert myprofile --no-roles

# Use when:
# - Want only playbooks
# - Custom role structure needed
# - Integrating into existing roles
```

### Skip Playbooks

Generate collection without example playbooks:

```bash
ansible-inspec convert myprofile --no-playbooks

# Use when:
# - Want only roles
# - Custom playbooks will be created
# - Library/module distribution only
```

## Troubleshooting

### Custom Resource Not Found

```bash
# Error: Custom resource 'my_resource' not found
# Solution: Ensure resource is in libraries/ directory

ls -la myprofile/libraries/
# Should contain my_resource.rb
```

### InSpec Not Installed

```bash
# Warning: Custom resources require InSpec
# Solution: Install InSpec

# macOS
brew install chef/chef/inspec

# Linux
curl https://omnitruck.chef.io/install.sh | sudo bash -s -- -P inspec

# Verify
inspec version
```

### Collection Build Fails

```bash
# Error: Failed to build collection
# Solution: Check galaxy.yml and directory structure

cd collections/ansible_collections/namespace/collection_name
ls -la  # Should have: galaxy.yml, roles/, playbooks/, README.md

# Validate galaxy.yml
python -c "import yaml; yaml.safe_load(open('galaxy.yml'))"

# Try building with verbose output
ansible-galaxy collection build -vvv
```

## Best Practices

1. **Test Before Converting**
   ```bash
   # Verify InSpec profile works
   inspec exec myprofile --target ssh://testhost
   
   # Then convert
   ansible-inspec convert myprofile
   ```

2. **Use Descriptive Names**
   ```bash
   # Good
   ansible-inspec convert profile \
     --namespace acme_security \
     --collection-name linux_baseline_cis
   
   # Avoid
   ansible-inspec convert profile  # Uses defaults
   ```

3. **Version Your Collections**
   ```bash
   # Update version in inspec.yml before converting
   # It will be carried over to galaxy.yml
   ```

4. **Document Custom Resources**
   ```bash
   # Add detailed comments to custom resources
   # They will appear in generated documentation
   ```

5. **Test Converted Collections**
   ```bash
   # Always test in non-production first
   ansible-playbook collection.playbook -i test_inventory.yml --check
   ```

## Quick Reference

```bash
# Basic conversion
ansible-inspec convert PROFILE

# Full customization
ansible-inspec convert PROFILE \
  --output-dir DIR \
  --namespace NS \
  --collection-name NAME \
  --native-only \
  --no-roles \
  --no-playbooks

# Using helper script
./examples/convert_profile.sh PROFILE [OUTPUT] [NAMESPACE] [NAME]

# Testing
ansible-playbook namespace.collection.playbook -i inventory.yml
```

## Next Steps

1. Read [Profile Conversion Guide](PROFILE-CONVERSION.md)
2. Try example: `./examples/convert_profile.sh examples/profiles/custom-compliance`
3. Convert your own profiles
4. Share your collections on Ansible Galaxy

## Support

- Documentation: [docs/](../docs/)
- Examples: [examples/](../examples/)
- Issues: GitHub Issues
- Community: Ansible Galaxy

Happy converting! 🚀
