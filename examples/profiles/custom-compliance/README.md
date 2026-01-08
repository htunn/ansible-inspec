# Custom Compliance Profile

Example InSpec profile demonstrating custom resources and conversion to Ansible collections.

## Overview

This profile includes:

- **Standard InSpec checks**: package, service, file resources
- **Custom resource**: `application_config` for checking YAML configuration files
- **Multiple controls**: demonstrating different check types

## Profile Structure

```
custom-compliance/
├── inspec.yml              # Profile metadata
├── controls/
│   └── example.rb          # Control definitions
└── libraries/
    └── application_config.rb  # Custom resource
```

## Controls

### basic-1: Required Packages
- Checks if `openssh-server` is installed
- Verifies `sshd` service is running and enabled

### custom-1: Application Configuration
- Uses custom `application_config` resource
- Validates `/etc/myapp/config.yml` exists and is valid
- Checks timeout >= 30 seconds
- Ensures debug mode is disabled

### files-1: File Permissions
- Verifies `/etc/passwd` has mode 0644
- Ensures `/etc/shadow` has mode 0000
- Confirms root ownership

## Custom Resource: application_config

The `application_config` resource reads YAML configuration files and provides methods to check settings.

### Usage

```ruby
describe application_config('/path/to/config.yml') do
  it { should exist }
  it { should be_valid }
  its('setting.key') { should eq 'value' }
end
```

### Methods

- `exists?`: Returns true if config file exists
- `valid?`: Returns true if file exists and is valid YAML
- `setting(key)`: Returns value for specified key

## Running with InSpec

```bash
# Run locally
inspec exec examples/profiles/custom-compliance

# Run against remote host
inspec exec examples/profiles/custom-compliance -t ssh://user@host
```

## Converting to Ansible Collection

```bash
# Convert profile to Ansible collection
ansible-inspec convert examples/profiles/custom-compliance \
  --namespace example \
  --collection-name custom_compliance

# Or use the example script
./examples/convert_profile.sh examples/profiles/custom-compliance
```

The conversion will:

1. Parse all controls from `controls/example.rb`
2. Detect custom resource in `libraries/application_config.rb`
3. Generate native Ansible tasks for standard resources (package, service, file)
4. Generate InSpec wrapper tasks for custom resource usage
5. Create Ansible collection structure with roles and playbooks
6. Copy custom resource to collection's `files/libraries/`
7. Generate documentation

## Converted Collection Usage

After conversion, use the collection in Ansible:

```yaml
- name: Run compliance checks
  hosts: all
  become: true
  roles:
    - example.custom_compliance.example
```

Or use the included playbook:

```bash
ansible-playbook example.custom_compliance.compliance_check -i inventory.yml
```

## Expected Conversion Output

```
Converted controls: 3
Roles created: 1
Custom resources: 1
  - application_config

Warnings:
  - Control 'custom-1' uses custom resource 'application_config' - using InSpec wrapper
```

## Notes

- **Custom resources** require InSpec to be installed on Ansible control node
- **Native Ansible** modules are used where possible for better performance
- **InSpec wrapper** preserves full compatibility with custom resources
- Generated collection can be published to Ansible Galaxy

## Testing

Test the profile before conversion:

```bash
# Create test config file
sudo mkdir -p /etc/myapp
sudo tee /etc/myapp/config.yml << EOF
setting:
  timeout: 60
  debug: false
EOF

# Run InSpec checks
inspec exec examples/profiles/custom-compliance
```

Expected output:
```
Profile: Example Profile with Custom Resources
Version: 1.0.0

  ✔  basic-1: Ensure required packages are installed
     ✔  System Package openssh-server is expected to be installed
     ✔  Service sshd is expected to be running
     ✔  Service sshd is expected to be enabled

  ✔  custom-1: Ensure application is configured correctly
     ✔  Application Config /etc/myapp/config.yml is expected to exist
     ✔  Application Config /etc/myapp/config.yml is expected to be valid
     ✔  Application Config /etc/myapp/config.yml setting.timeout is expected to cmp >= 30
     ✔  Application Config /etc/myapp/config.yml setting.debug is expected to eq false

  ✔  files-1: Ensure critical files have correct permissions
     ✔  File /etc/passwd is expected to exist
     ✔  File /etc/passwd mode is expected to cmp == "0644"
     ✔  File /etc/passwd owner is expected to eq "root"
     ✔  File /etc/shadow is expected to exist
     ✔  File /etc/shadow mode is expected to cmp == "0000"
     ✔  File /etc/shadow owner is expected to eq "root"

Profile Summary: 3 successful controls, 0 control failures, 0 controls skipped
Test Summary: 13 successful, 0 failures, 0 skipped
```

## License

Apache-2.0
