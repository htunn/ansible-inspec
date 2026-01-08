# Getting Started with ansible-inspec

## Introduction

`ansible-inspec` combines the power of Ansible's infrastructure automation with InSpec's compliance testing framework, allowing you to:

- Test infrastructure configurations programmatically
- Validate compliance and security requirements
- Integrate testing into your automation workflows
- Use Ansible inventory for test targeting

## Prerequisites

- Python 3.8 or higher
- Basic knowledge of Ansible
- Basic knowledge of InSpec or infrastructure testing

## Installation

### From PyPI (when available)

```bash
pip install ansible-inspec
```

### From Source

```bash
git clone https://github.com/htunn/ansible-inspec.git
cd ansible-inspec
pip install -e .
```

### Verify Installation

```bash
ansible-inspec --version
```

## Quick Start

### 1. Create Your First Compliance Profile

```bash
ansible-inspec init profile my-first-profile
cd my-first-profile
```

This creates a directory structure:

```
my-first-profile/
├── README.md
├── controls/
│   └── example.rb
└── inspec.yml
```

### 2. Write a Simple Test

Edit `controls/example.rb`:

```ruby
# controls/example.rb
control 'basic-1' do
  impact 1.0
  title 'Ensure SSH is running'
  desc 'The SSH service should be installed and running'
  
  describe service('sshd') do
    it { should be_installed }
    it { should be_running }
  end
end

control 'basic-2' do
  impact 0.7
  title 'Ensure telnet is not installed'
  desc 'Telnet is insecure and should not be present'
  
  describe package('telnetd') do
    it { should_not be_installed }
  end
end
```

### 3. Run Tests Against a Target

```bash
# Test local system
ansible-inspec exec my-first-profile

# Test remote system via SSH
ansible-inspec exec my-first-profile -t ssh://user@hostname

# Test using Ansible inventory
ansible-inspec exec my-first-profile -i inventory.yml
```

## Using with Ansible Inventory

### Create an Inventory File

```yaml
# inventory.yml
all:
  hosts:
    web-01:
      ansible_host: 192.168.1.10
      ansible_user: admin
    web-02:
      ansible_host: 192.168.1.11
      ansible_user: admin
  vars:
    compliance_profile: profiles/web-server
```

### Run Tests

```bash
ansible-inspec exec profiles/web-server -i inventory.yml
```

## Example Compliance Tests

### File Permissions Test

```ruby
control 'file-permissions-1' do
  impact 1.0
  title 'Ensure sensitive files have correct permissions'
  
  describe file('/etc/passwd') do
    it { should exist }
    it { should be_file }
    its('mode') { should cmp '0644' }
    its('owner') { should eq 'root' }
  end
end
```

### Service Configuration Test

```ruby
control 'service-config-1' do
  impact 0.8
  title 'Ensure SSH is configured securely'
  
  describe sshd_config do
    its('PermitRootLogin') { should eq 'no' }
    its('PasswordAuthentication') { should eq 'no' }
    its('PermitEmptyPasswords') { should eq 'no' }
  end
end
```

### Package Compliance Test

```ruby
control 'package-1' do
  impact 0.5
  title 'Ensure required packages are installed'
  
  %w(curl wget git).each do |pkg|
    describe package(pkg) do
      it { should be_installed }
    end
  end
end
```

## Next Steps

- Read the [Command Reference](command-reference.md)
- Learn about [Writing Profiles](profiles.md)
- Explore [Ansible Integration](ansible-integration.md)
- Check out [example profiles](../examples/)

## Common Issues

### Permission Denied

If you get permission errors when testing files:
```bash
# Run with sudo (be careful!)
ansible-inspec exec profile -t ssh://user@host --sudo
```

### Connection Issues

If you can't connect to remote hosts:
```bash
# Test connectivity first
ssh user@hostname

# Specify SSH key
ansible-inspec exec profile -t ssh://user@host -i ~/.ssh/id_rsa
```

## Getting Help

- [GitHub Issues](https://github.com/htunn/ansible-inspec/issues)
- [Discussions](https://github.com/htunn/ansible-inspec/discussions)
- Check the [FAQ](faq.md)
