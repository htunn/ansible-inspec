# Quick Start Guide

Get started with ansible-inspec in 5 minutes!

## Prerequisites

- Python 3.8+ installed
- Basic familiarity with command line
- (Optional) Ansible and InSpec knowledge helpful but not required

## Installation

### Option 1: Development Installation

```bash
cd /Users/htunn/code/AI/ansible-inspec
pip install -e .
```

### Option 2: Run Directly

```bash
cd /Users/htunn/code/AI/ansible-inspec
bin/ansible-inspec --help
```

## Verify Installation

```bash
ansible-inspec --version
```

Expected output:
```
ansible-inspec version 0.1.0
Licensed under GPL-3.0

Built with components from:
  - ansible: https://github.com/ansible/ansible
    License: GPL-3.0
    Copyright: Red Hat, Inc.
  - inspec: https://github.com/inspec/inspec
    License: Apache-2.0
    Copyright: Progress Software Corp.
```

## Your First Compliance Check

### 1. View the Example Profile

```bash
cat examples/profiles/basic-compliance/controls/basic.rb
```

This shows InSpec test syntax for checking:
- Operating system type
- SSH configuration
- Installed packages
- File permissions

### 2. Run Example Command

```bash
# This is a skeleton - full implementation pending
ansible-inspec exec examples/profiles/basic-compliance
```

### 3. View Command Help

```bash
ansible-inspec exec --help
ansible-inspec init --help
```

## Project Structure at a Glance

```
ansible-inspec/
├── bin/ansible-inspec       # Main executable
├── examples/                # Example profiles
├── lib/ansible_inspec/      # Source code
├── docs/                    # Documentation
├── tests/                   # Test suite
└── README.md               # Full documentation
```

## Common Commands

### Show Version and License
```bash
ansible-inspec --version
ansible-inspec --license
```

### Initialize New Profile
```bash
ansible-inspec init profile my-compliance-checks
```

### Execute Profile (when implemented)
```bash
# Against local system
ansible-inspec exec my-profile/

# Against remote system
ansible-inspec exec my-profile/ -t ssh://user@host

# Using Ansible inventory
ansible-inspec exec my-profile/ -i inventory.yml
```

## Next Steps

1. **Read the full documentation**: [README.md](README.md)
2. **Explore examples**: Check `examples/profiles/basic-compliance/`
3. **Learn about licensing**: See [LICENSE-SUMMARY.md](docs/LICENSE-SUMMARY.md)
4. **Contribute**: Read [CONTRIBUTING.md](CONTRIBUTING.md)

## Current Status

⚠️ **Note**: This is v0.1.0 - a project skeleton

**What works**:
- ✅ Project structure
- ✅ License compliance
- ✅ CLI interface (basic)
- ✅ Documentation

**What's pending**:
- ⏳ Core integration logic
- ⏳ Ansible inventory parsing
- ⏳ InSpec profile execution
- ⏳ Full test suite

## Get Help

- **Documentation**: See `docs/` folder
- **Examples**: See `examples/` folder
- **Issues**: GitHub issues (if repository published)
- **Contributing**: See CONTRIBUTING.md

## Important: License

This project is licensed under **GPL-3.0**.

Key points:
- ✅ Free to use, modify, and distribute
- ✅ Commercial use allowed
- ⚠️ Modifications must be GPL-3.0
- ⚠️ Source code must be provided
- ✅ Properly combines Ansible (GPL-3.0) + InSpec (Apache-2.0)

See [LICENSE](LICENSE) for full terms.

---

**Ready to contribute?** See [CONTRIBUTING.md](CONTRIBUTING.md)  
**Need more details?** See [README.md](README.md)  
**Questions about licensing?** See [docs/LICENSE-SUMMARY.md](docs/LICENSE-SUMMARY.md)
