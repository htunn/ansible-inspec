# InSpec Profile to Ansible Collection Conversion

Convert Ruby-based InSpec compliance profiles into Ansible collections for native integration with Ansible workflows.

## Overview

The `ansible-inspec convert` command transforms InSpec profiles into Ansible collections, providing:

- **Native Ansible tasks** for common compliance checks
- **Automatic role generation** from control files
- **Custom resource support** via InSpec wrapper
- **Ready-to-use playbooks** for immediate deployment
- **Ansible Galaxy compatibility** for distribution

## Quick Start

```bash
# Convert an InSpec profile
ansible-inspec convert /path/to/inspec-profile \
  --output-dir ./collections \
  --namespace myorg \
  --collection-name compliance_baseline

# Build and install the collection
cd collections/ansible_collections/myorg/compliance_baseline
ansible-galaxy collection build
ansible-galaxy collection install myorg-compliance_baseline-*.tar.gz

# Use the collection
ansible-playbook myorg.compliance_baseline.compliance_check -i inventory.yml
```

## Command Reference

### Basic Usage

```bash
ansible-inspec convert <profile> [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `profile` | Path to InSpec profile directory | Required |
| `-o, --output-dir` | Output directory for collection | `./collections` |
| `--namespace` | Ansible Galaxy namespace | `compliance` |
| `--collection-name` | Collection name | `inspec_profiles` |
| `--native-only` | Only use native Ansible modules | False |
| `--no-roles` | Skip role creation | False |
| `--no-playbooks` | Skip playbook creation | False |

### Examples

#### Convert DevSec Linux Baseline

```bash
# Download profile
git clone https://github.com/dev-sec/linux-baseline
cd linux-baseline

# Convert to Ansible collection
ansible-inspec convert . \
  --namespace devsec \
  --collection-name linux_baseline \
  --output-dir ../collections
```

#### Convert Custom Profile

```bash
ansible-inspec convert ./my-compliance-profile \
  --namespace mycompany \
  --collection-name security_baseline \
  --output-dir /opt/ansible/collections
```

#### Convert with Native Modules Only

```bash
# Skip InSpec wrapper, use only Ansible modules
ansible-inspec convert ./profile \
  --native-only \
  --namespace compliance \
  --collection-name native_checks
```

## Conversion Process

### 1. Profile Analysis

The converter analyzes your InSpec profile:

```
my-profile/
├── inspec.yml          # Profile metadata
├── controls/           # Control files (*.rb)
│   ├── sshd.rb
│   ├── filesystem.rb
│   └── packages.rb
└── libraries/          # Custom resources
    └── custom_config.rb
```

### 2. Resource Mapping

InSpec resources are mapped to Ansible modules:

| InSpec Resource | Ansible Module | Conversion Type |
|----------------|----------------|-----------------|
| `file` | `ansible.builtin.stat` | Native |
| `service` | `ansible.builtin.service_facts` | Native |
| `package` | `ansible.builtin.package_facts` | Native |
| `sshd_config` | `ansible.builtin.lineinfile` | Native |
| `command` | `ansible.builtin.command` | Native |
| `port` | `ansible.builtin.wait_for` | Native |
| `kernel_parameter` | `ansible.posix.sysctl` | Native |
| Custom resources | InSpec wrapper | Wrapper |

### 3. Collection Generation

Creates Ansible collection structure:

```
ansible_collections/
└── myorg/
    └── compliance_baseline/
        ├── galaxy.yml
        ├── README.md
        ├── roles/
        │   ├── sshd/
        │   │   ├── tasks/main.yml
        │   │   ├── meta/main.yml
        │   │   └── defaults/main.yml
        │   ├── filesystem/
        │   └── packages/
        ├── playbooks/
        │   └── compliance_check.yml
        ├── files/
        │   └── libraries/  # Custom resources
        └── docs/
            └── CUSTOM_RESOURCES.md
```

## Conversion Examples

### Example 1: SSH Configuration

**InSpec Control (controls/sshd.rb):**
```ruby
control 'sshd-8' do
  impact 0.8
  title 'Configure SSH service port'
  desc 'SSH should listen on port 22 with secure settings'
  
  describe sshd_config do
    its('Port') { should cmp 22 }
    its('PermitRootLogin') { should eq 'no' }
    its('PasswordAuthentication') { should eq 'no' }
  end
end
```

**Converted Ansible Role (roles/sshd/tasks/main.yml):**
```yaml
- name: Configure SSH service port
  tags: [compliance, high]
  block:
    - name: Check SSH config Port
      ansible.builtin.lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^Port'
        line: 'Port 22'
        state: present
      check_mode: yes
      register: ssh_check_port
      failed_when: ssh_check_port.changed
    
    - name: Check SSH config PermitRootLogin
      ansible.builtin.lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^PermitRootLogin'
        line: 'PermitRootLogin no'
        state: present
      check_mode: yes
      register: ssh_check_permitrootlogin
      failed_when: ssh_check_permitrootlogin.changed
    
    - name: Check SSH config PasswordAuthentication
      ansible.builtin.lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^PasswordAuthentication'
        line: 'PasswordAuthentication no'
        state: present
      check_mode: yes
      register: ssh_check_passwordauthentication
      failed_when: ssh_check_passwordauthentication.changed
```

### Example 2: Service Checks

**InSpec Control:**
```ruby
control 'service-01' do
  impact 0.7
  title 'Critical services running'
  
  describe service('sshd') do
    it { should be_running }
    it { should be_enabled }
  end
end
```

**Converted Ansible Tasks:**
```yaml
- name: Critical services running
  tags: [compliance, high]
  block:
    - name: Gather service facts
      ansible.builtin.service_facts:
    
    - name: Verify sshd service
      ansible.builtin.assert:
        that:
          - services['sshd'].state == 'running'
          - services['sshd'].status == 'enabled'
        fail_msg: "Service sshd is not compliant"
```

### Example 3: Package Checks

**InSpec Control:**
```ruby
control 'packages-01' do
  impact 0.9
  title 'Insecure packages not installed'
  
  describe package('telnetd') do
    it { should_not be_installed }
  end
  
  describe package('rsh-server') do
    it { should_not be_installed }
  end
end
```

**Converted Ansible Tasks:**
```yaml
- name: Insecure packages not installed
  tags: [compliance, critical]
  block:
    - name: Gather package facts
      ansible.builtin.package_facts:
        manager: auto
    
    - name: Verify telnetd package
      ansible.builtin.assert:
        that:
          - "'telnetd' not in ansible_facts.packages"
        fail_msg: "Package telnetd compliance check failed"
    
    - name: Verify rsh-server package
      ansible.builtin.assert:
        that:
          - "'rsh-server' not in ansible_facts.packages"
        fail_msg: "Package rsh-server compliance check failed"
```

## Custom Resources Support

### How It Works

Custom InSpec resources from `libraries/` directory are:

1. **Detected** during conversion
2. **Copied** to `files/libraries/` in the collection
3. **Wrapped** in InSpec execution tasks
4. **Documented** in `docs/CUSTOM_RESOURCES.md`

### Example: Custom Resource

**InSpec Custom Resource (libraries/example_config.rb):**
```ruby
class ExampleConfig < Inspec.resource(1)
  name 'example_config'
  desc 'Custom configuration file resource'
  
  def initialize(path = nil)
    @path = path || '/etc/example.conf'
    @params = SimpleConfig.new(read_content)
  end
  
  def signal
    @params['signal']
  end
  
  private
  
  def read_content
    inspec.file(@path).content
  end
end
```

**InSpec Control Using Custom Resource:**
```ruby
control 'example-01' do
  impact 0.7
  title 'Check example configuration'
  
  describe example_config('/etc/example.conf') do
    its('signal') { should eq 'on' }
  end
end
```

**Converted Ansible Task:**
```yaml
- name: Check example configuration
  tags: [compliance, high]
  block:
    - name: Execute custom resource check example_config
      ansible.builtin.shell:
        cmd: inspec exec - -t local:// --controls example-01
        stdin: |
          control 'example-01' do
            impact 0.7
            title 'Check example configuration'
            
            describe example_config('/etc/example.conf') do
              its('signal') { should eq 'on' }
            end
          end
      register: inspec_example_01_result
      failed_when: inspec_example_01_result.rc != 0
      environment:
        INSPEC_LOAD_PATH: '{{ role_path }}/files/libraries'
```

### Requirements for Custom Resources

When your collection uses custom resources:

1. **InSpec must be installed** on target or control node
2. **Custom resource files** are bundled in the collection
3. **INSPEC_LOAD_PATH** environment variable is set automatically

## Using Converted Collections

### Installation

```bash
# From local build
ansible-galaxy collection install ./myorg-compliance_baseline-1.0.0.tar.gz

# From file
ansible-galaxy collection install /path/to/collection.tar.gz

# List installed
ansible-galaxy collection list
```

### Running Compliance Checks

#### Using Roles

```yaml
# playbook.yml
- name: Run compliance checks
  hosts: all
  become: true
  roles:
    - myorg.compliance_baseline.sshd
    - myorg.compliance_baseline.filesystem
    - myorg.compliance_baseline.packages
```

```bash
ansible-playbook playbook.yml -i inventory.yml
```

#### Using Included Playbook

```bash
ansible-playbook myorg.compliance_baseline.compliance_check -i inventory.yml
```

#### Selective Tag Execution

```bash
# Run only critical checks
ansible-playbook playbook.yml --tags critical

# Run high and critical
ansible-playbook playbook.yml --tags "high,critical"

# Skip low impact checks
ansible-playbook playbook.yml --skip-tags low
```

## Best Practices

### 1. Profile Organization

Organize InSpec profiles before conversion:

```
my-profile/
├── inspec.yml              # Clear metadata
├── controls/
│   ├── 01-system.rb        # Numbered for order
│   ├── 02-network.rb
│   └── 03-services.rb
└── libraries/
    └── custom_helpers.rb   # Well-documented
```

### 2. Namespace Selection

Choose meaningful namespaces:

```bash
# Company namespace
--namespace mycompany

# Team namespace
--namespace security_team

# Standard namespace
--namespace compliance
```

### 3. Collection Naming

Use descriptive collection names:

```bash
# Good
--collection-name linux_security_baseline
--collection-name cis_docker_benchmark
--collection-name pci_dss_compliance

# Avoid
--collection-name profile1
--collection-name test
```

### 4. Version Control

Maintain both profiles and collections:

```
.
├── inspec-profiles/          # Source profiles
│   └── linux-baseline/
└── ansible-collections/      # Converted collections
    └── myorg.linux_baseline/
```

### 5. Testing

Test converted collections before deployment:

```bash
# Syntax check
ansible-playbook --syntax-check playbook.yml

# Check mode (dry run)
ansible-playbook playbook.yml --check

# Limit to test hosts
ansible-playbook playbook.yml --limit test-hosts

# Verbose output
ansible-playbook playbook.yml -vvv
```

## Troubleshooting

### Conversion Fails

**Problem**: "Invalid InSpec profile"

**Solution**: Ensure profile has `inspec.yml` or `controls/` directory:
```bash
ls -la my-profile/
# Should show inspec.yml and/or controls/
```

### Custom Resources Not Working

**Problem**: Custom resource checks fail

**Solution**: Verify InSpec is installed and in PATH:
```bash
inspec version
# Should show InSpec version

# Install if missing
brew install chef/chef/inspec  # macOS
# or
curl https://omnitruck.chef.io/install.sh | sudo bash -s -- -P inspec
```

### Role Tasks Not Generated

**Problem**: Roles created but tasks empty

**Solution**: Check control file syntax:
```bash
inspec check my-profile/
# Should show no errors
```

### Ansible Module Not Found

**Problem**: Module not found errors when running playbook

**Solution**: Install required collections:
```bash
ansible-galaxy collection install ansible.posix
ansible-galaxy collection install community.general
```

## Advanced Usage

### Custom Collection Structure

Modify converted collection before building:

```bash
# Convert
ansible-inspec convert profile/ -o collections/

# Navigate
cd collections/ansible_collections/namespace/name/

# Add custom files
mkdir plugins/modules/
# Add custom modules

# Add documentation
vim docs/USAGE.md

# Build
ansible-galaxy collection build
```

### Integration with CI/CD

```yaml
# .github/workflows/compliance.yml
name: Compliance Testing

on: [push, pull_request]

jobs:
  convert-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install ansible-inspec
        run: pip install ansible-inspec
      
      - name: Convert profile
        run: |
          ansible-inspec convert inspec-profile/ \
            --namespace ci \
            --collection-name compliance \
            -o ./collections
      
      - name: Build collection
        run: |
          cd collections/ansible_collections/ci/compliance
          ansible-galaxy collection build
      
      - name: Install collection
        run: ansible-galaxy collection install collections/ansible_collections/ci/compliance/*.tar.gz
      
      - name: Run compliance checks
        run: ansible-playbook ci.compliance.compliance_check -i inventory.yml
```

### Publishing to Galaxy

```bash
# Build collection
cd collections/ansible_collections/myorg/myproject
ansible-galaxy collection build

# Publish to Ansible Galaxy
ansible-galaxy collection publish myorg-myproject-1.0.0.tar.gz --api-key=<your-key>
```

## Resources

- [Ansible Collections Documentation](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html)
- [InSpec Documentation](https://docs.chef.io/inspec/)
- [Ansible Galaxy](https://galaxy.ansible.com/)
- [ansible-inspec Repository](https://github.com/Htunn/ansible-inspec)

## Support

For issues with profile conversion:

1. Check [GitHub Issues](https://github.com/Htunn/ansible-inspec/issues)
2. Review [Examples](../examples/)
3. Read [InSpec Profile Documentation](https://docs.chef.io/inspec/7.0/profiles/)

## License

GPL-3.0-or-later

---

**Generated by ansible-inspec** - https://github.com/Htunn/ansible-inspec
