# ansible-inspec Quick Reference

Essential commands and examples for ansible-inspec.

## Installation

```bash
# PyPI (recommended)
pip install ansible-inspec

# Docker
docker pull htunnthuthu/ansible-inspec:latest

# Verify installation
ansible-inspec --version
```

## Common Commands

### Execute InSpec Profiles

```bash
# Local system
ansible-inspec exec profile/ --target local://

# Remote host
ansible-inspec exec profile/ --target user@hostname

# Ansible inventory
ansible-inspec exec profile/ --target inventory.yml

# Docker container
ansible-inspec exec profile/ --target docker://container_name
```

### Generate Reports

```bash
# JSON report
ansible-inspec exec profile/ --target local:// \
  --reporter json --output report.json

# HTML report
ansible-inspec exec profile/ --target local:// \
  --reporter html --output report.html

# Multiple reports
ansible-inspec exec profile/ --target local:// \
  --reporter "json:report.json html:report.html"
```

### Convert Profiles

```bash
# Basic conversion
ansible-inspec convert profile/

# Custom namespace and name
ansible-inspec convert profile/ \
  --namespace myorg \
  --collection-name security

# Specify output directory
ansible-inspec convert profile/ --output-dir ./collections
```

### Chef Supermarket

```bash
# Search profiles
ansible-inspec supermarket search CIS

# Get profile info
ansible-inspec supermarket info dev-sec/linux-baseline

# Download profile
ansible-inspec supermarket download dev-sec/linux-baseline

# Download and convert
ansible-inspec convert dev-sec/linux-baseline \
  --namespace devsec \
  --collection-name linux_baseline
```

## Python API

```python
from ansible_inspec import Runner, ProfileConverter
from ansible_inspec.core import ExecutionConfig

# Execute profile
config = ExecutionConfig(
    profile_path="./profile",
    target="local://",
    reporter="json"
)
runner = Runner(config)
result = runner.run()

# Save reports
result.save("report.json", format="json")
result.save("report.html", format="html")

# Convert profile
converter = ProfileConverter(
    profile_path="./profile",
    namespace="myorg",
    collection_name="security"
)
converter.convert()
```

## Docker Usage

```bash
# Run profile (mount current directory)
docker run --rm -v $(pwd):/workspace \
  htunnthuthu/ansible-inspec:latest \
  exec profile/ --target local://

# Convert profile
docker run --rm -v $(pwd):/workspace \
  htunnthuthu/ansible-inspec:latest \
  convert profile/ --namespace myorg

# Search Supermarket
docker run --rm htunnthuthu/ansible-inspec:latest \
  supermarket search CIS
```

## Common Workflows

### Workflow 1: Download and Run CIS Benchmark

```bash
# Download CIS profile
ansible-inspec supermarket download cis/cis-ubuntu-20-04-server-level1

# Run on local system
ansible-inspec exec cis-ubuntu-20-04-server-level1/ \
  --target local:// \
  --reporter html --output cis-report.html

# View report
open cis-report.html
```

### Workflow 2: Convert Profile to Ansible Collection

```bash
# Convert DevSec baseline
ansible-inspec supermarket download dev-sec/linux-baseline

ansible-inspec convert linux-baseline/ \
  --namespace devsec \
  --collection-name linux_baseline \
  --output-dir ./collections

# Install collection
cd collections/ansible_collections/devsec/linux_baseline
ansible-galaxy collection build
ansible-galaxy collection install devsec-linux_baseline-*.tar.gz

# Run as Ansible playbook (InSpec-free!)
ansible-playbook playbooks/compliance_check.yml -i inventory.yml
```

### Workflow 3: CI/CD Integration

```bash
# Run compliance tests in CI
ansible-inspec exec profile/ \
  --target inventory.yml \
  --reporter junit --output test-results.xml

# Exit code: 0 = pass, 1 = fail
echo $?
```

### Workflow 4: Multi-Host Compliance Scan

```bash
# Create inventory
cat > inventory.yml << EOF
all:
  hosts:
    web1:
      ansible_host: 192.168.1.10
    web2:
      ansible_host: 192.168.1.11
    db1:
      ansible_host: 192.168.1.20
EOF

# Run compliance scan
ansible-inspec exec cis-benchmark/ \
  --target inventory.yml \
  --reporter "json:compliance.json html:compliance.html"

# Check results
open compliance.html
```

## Report Formats

### JSON (InSpec Schema)

```bash
ansible-inspec exec profile/ --target local:// \
  --reporter json --output report.json
```

**Use for:**
- API integration
- Custom tooling
- Data analysis
- CI/CD pipelines

### HTML (Interactive)

```bash
ansible-inspec exec profile/ --target local:// \
  --reporter html --output report.html
```

**Use for:**
- Human review
- Stakeholder reports
- Audit documentation

### JUnit XML

```bash
ansible-inspec exec profile/ --target local:// \
  --reporter junit --output results.xml
```

**Use for:**
- Jenkins integration
- GitLab CI
- GitHub Actions
- Azure DevOps

## Filtering Controls

```bash
# Run specific controls
ansible-inspec exec profile/ --target local:// \
  --controls "ssh-1,ssh-2,firewall-1"

# Filter by tags
ansible-inspec exec profile/ --target local:// \
  --tags "critical,security"
```

## Environment Variables

```bash
# Default reporter
export ANSIBLE_INSPEC_REPORTER=json

# Output directory
export ANSIBLE_INSPEC_OUTPUT_DIR=.compliance-reports

# Ansible configuration
export ANSIBLE_CONFIG=./ansible.cfg
export ANSIBLE_INVENTORY=./inventory.yml
```

## Common Issues

### InSpec Not Found

**Native mode requires InSpec:**
```bash
# macOS
brew install chef/chef/inspec

# Linux
curl -fsSL https://omnitruck.chef.io/install.sh | sudo bash -s -- -P inspec
```

**Or use InSpec-free mode:**
```bash
# Convert profile to Ansible collection
ansible-inspec convert profile/ --namespace myorg
# Run without InSpec
cd collections/ansible_collections/myorg/profile/
ansible-playbook playbooks/compliance_check.yml -i inventory.yml
```

### Permission Denied

```bash
# Run with sudo for system checks
sudo ansible-inspec exec profile/ --target local://

# Or use SSH for remote
ansible-inspec exec profile/ --target user@hostname
```

### Connection Timeout

```bash
# Increase SSH timeout in ansible.cfg
[ssh_connection]
ssh_args = -o ConnectTimeout=60
```

## Tips and Tricks

### Dry Run

```bash
# Check profile without executing
ansible-inspec exec profile/ --target local:// --dry-run
```

### Verbose Output

```bash
# See detailed execution
ansible-inspec -v exec profile/ --target local://
```

### Background Execution

```bash
# Run in background, redirect output
nohup ansible-inspec exec profile/ --target inventory.yml \
  --reporter json --output report.json > run.log 2>&1 &
```

### Auto-Reporting with Collections

```yaml
# ansible.cfg in converted collection
[defaults]
callbacks_enabled = compliance_reporter
callback_result_dir = .compliance-reports

[callback_compliance_reporter]
output_dir = .compliance-reports
output_format = json
```

## Resources

- **PyPI**: https://pypi.org/project/ansible-inspec/
- **Docker Hub**: https://hub.docker.com/r/htunnthuthu/ansible-inspec
- **GitHub**: https://github.com/Htunn/ansible-inspec
- **API Docs**: [docs/API.md](API.md)
- **Publishing**: [docs/PUBLISHING-GUIDE.md](PUBLISHING-GUIDE.md)

## License

GPL-3.0-or-later
