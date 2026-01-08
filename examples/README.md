# ansible-inspec Examples

This directory contains practical examples demonstrating various features of ansible-inspec.

## Chef Supermarket Integration

### supermarket_demo.py

Python demonstration of Chef Supermarket profile loading:

```bash
python examples/supermarket_demo.py
```

**Features demonstrated**:
- Loading profiles from Chef Supermarket
- Creating InSpecProfile instances with `from_supermarket()`
- Popular compliance profiles showcase
- Python API usage patterns

### multi_profile_test.sh

Shell script for running multiple Chef Supermarket profiles against infrastructure:

```bash
# Run against your inventory
./examples/multi_profile_test.sh inventory.yml
```

**Features demonstrated**:
- Running multiple compliance profiles in sequence
- Automated compliance testing workflow
- JSON result generation for each profile
- Success/failure tracking and reporting
- Production-ready error handling

**Profiles tested by default**:
- `dev-sec/linux-baseline` - OS hardening (56 controls)
- `dev-sec/ssh-baseline` - SSH security (28 controls)

**Optional profiles** (uncomment in script):
- `dev-sec/apache-baseline` - Apache hardening
- `dev-sec/mysql-baseline` - MySQL security
- `dev-sec/nginx-baseline` - Nginx hardening
- `dev-sec/postgres-baseline` - PostgreSQL security
- `cis-docker-benchmark` - CIS Docker compliance

### Example Output

```bash
$ ./examples/multi_profile_test.sh inventory.yml

========================================
Multi-Profile Compliance Testing
========================================

Inventory: inventory.yml

Results directory: compliance-results-20260108-143022

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Testing Profile: dev-sec/linux-baseline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Profile passed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Testing Profile: dev-sec/ssh-baseline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Profile passed

========================================
COMPLIANCE TESTING SUMMARY
========================================

Total Profiles Tested: 2
Passed:               2
Failed:               0

Results saved to: compliance-results-20260108-143022/

Result Files:
  • dev-sec_linux-baseline.json (45K)
  • dev-sec_ssh-baseline.json (28K)

✓ All compliance profiles passed
```

## Prerequisites

All examples require:
- `ansible-inspec` installed (`pip install ansible-inspec`)
- InSpec installed:
  - **macOS**: `brew install chef/chef/inspec`
  - **Linux**: `curl https://omnitruck.chef.io/install.sh | sudo bash -s -- -P inspec`
- Valid Ansible inventory file

## Creating Your Own Examples

### Python API Example

```python
from ansible_inspec.inspec_adapter import InSpecProfile, InSpecRunner

# Load from Supermarket
profile = InSpecProfile.from_supermarket('dev-sec/linux-baseline')

# Execute against target
runner = InSpecRunner(profile, target='ssh://user@host')
result = runner.execute()

# Check results
if result.success:
    print(f"✓ All {result.total} tests passed")
else:
    print(f"✗ {result.failed} tests failed")
```

### Shell Script Example

```bash
#!/bin/bash
# Run compliance profile
ansible-inspec exec dev-sec/linux-baseline \
  --supermarket \
  -i inventory.yml \
  --reporter cli json:results.json

# Check exit code
if [ $? -eq 0 ]; then
  echo "✓ Compliance passed"
else
  echo "✗ Compliance failed"
  exit 1
fi
```

## Additional Resources

- [Chef Supermarket Guide](../docs/CHEF-SUPERMARKET.md) - Complete Chef Supermarket documentation
- [Docker Usage Guide](../docs/DOCKER.md) - Running examples in Docker
- [Main README](../README.md) - Project overview and quickstart
- [Chef Supermarket](https://supermarket.chef.io) - Browse available profiles

## Contributing Examples

Have a useful example? Contributions are welcome!

1. Create your example file in this directory
2. Add documentation here
3. Submit a pull request

Please ensure examples:
- Are well-commented
- Include usage instructions
- Demonstrate a specific feature or use case
- Follow the project's code style
