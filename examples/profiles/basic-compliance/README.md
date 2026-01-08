# Basic System Compliance Profile

This InSpec profile contains basic compliance checks for system configuration.

## Requirements

- Linux or macOS operating system
- SSH service (for remote testing)

## Usage

### Local Testing
```bash
ansible-inspec exec examples/profiles/basic-compliance
```

### Remote Testing via SSH
```bash
ansible-inspec exec examples/profiles/basic-compliance -t ssh://user@hostname
```

### With Ansible Inventory
```bash
ansible-inspec exec examples/profiles/basic-compliance -i inventory.yml
```

## Controls

- **system-01**: Operating System Check
- **system-02**: SSH Service Configuration
- **system-03**: Insecure Packages Not Installed
- **system-04**: File Permissions

## License

GPL-3.0 - See LICENSE file in project root
