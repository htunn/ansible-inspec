# ansible-inspec

[![PyPI - Version](https://img.shields.io/pypi/v/ansible-inspec)](https://pypi.org/project/ansible-inspec/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ansible-inspec)](https://pypi.org/project/ansible-inspec/)
[![Docker Image Version](https://img.shields.io/docker/v/htunnthuthu/ansible-inspec?label=docker)](https://hub.docker.com/r/htunnthuthu/ansible-inspec)
[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)

A compliance and infrastructure testing tool that combines the power of Ansible's automation capabilities with InSpec's compliance and security testing framework.

## Overview

`ansible-inspec` integrates two powerful open-source projects:
- **[Ansible](https://github.com/ansible/ansible)**: IT automation platform for configuration management and deployment
- **[InSpec](https://github.com/inspec/inspec)**: Infrastructure testing framework for compliance and security

## Why Ansible-InSpec?

### 🎯 The Perfect Bridge

Ansible-InSpec bridges the gap between **infrastructure automation** and **compliance testing**, giving you:

#### ✅ **Unified Workflow**
- **Single Tool, Two Powers**: Combine Ansible's automation with InSpec's compliance testing
- **Same Inventory**: Use your existing Ansible inventory for compliance testing
- **Consistent Access**: Leverage Ansible's SSH/WinRM/Docker connections for testing
- **No Duplicate Configuration**: Manage infrastructure and compliance from one place

#### 🚀 **Accelerated Compliance**
- **Parallel Testing**: Run compliance checks across hundreds of hosts simultaneously
- **Fast Feedback**: Get immediate compliance results after infrastructure changes
- **Continuous Compliance**: Integrate into CI/CD pipelines for automated validation
- **Shift-Left Security**: Test compliance before production deployment

#### 🔒 **Enhanced Security & Governance**
- **CIS Benchmarks**: Test against industry-standard security baselines
- **Custom Policies**: Define organization-specific compliance requirements
- **Audit Ready**: Generate compliance reports for auditors and stakeholders
- **Drift Detection**: Identify configuration drift from security baselines

#### 💡 **Developer Friendly**
- **Readable DSL**: Write compliance tests in InSpec's human-readable language
- **Version Control**: Store compliance tests alongside infrastructure code
- **Test-Driven Infrastructure**: Build infrastructure with compliance tests first
- **Reusable Profiles**: Share compliance tests across teams and projects

#### 🌐 **Multi-Platform Excellence**
- **Linux**: All major distributions (Ubuntu, RHEL, CentOS, Debian, etc.)
- **Windows**: Windows Server and Desktop versions
- **Cloud**: AWS, Azure, GCP resources
- **Containers**: Docker and Kubernetes
- **Network Devices**: Test firewalls, switches, routers

#### 📊 **Comprehensive Reporting**
- **Multiple Formats**: JSON, HTML, JUnit, CLI output
- **Detailed Results**: See exactly what passed/failed and why
- **Trend Analysis**: Track compliance over time
- **Integration Ready**: Feed results into your monitoring/reporting systems

#### 💰 **Cost Effective**
- **Open Source**: Free, GPL-3.0 licensed
- **No Agent Required**: Agentless compliance testing
- **Reduced Tools**: Replace multiple compliance tools with one
- **Lower Training**: Leverage existing Ansible knowledge

### 🆚 Compared to Alternatives

| Feature | Ansible-InSpec | Pure InSpec | Pure Ansible | Other Tools |
|---------|---------------|-------------|--------------|-------------|
| Ansible Inventory | ✅ Native | ❌ Manual | ✅ Native | ❌ Separate |
| Compliance DSL | ✅ InSpec | ✅ InSpec | ⚠️ Tasks | ⚠️ Varies |
| Multi-Platform | ✅ Excellent | ✅ Excellent | ✅ Good | ⚠️ Limited |
| Parallel Execution | ✅ Yes | ⚠️ Limited | ✅ Yes | ⚠️ Varies |
| Learning Curve | ⚠️ Medium | ⚠️ Medium | ⚠️ Medium | ❌ High |
| Open Source | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Varies |

## Features

- **Profile Conversion**: Convert Ruby-based InSpec profiles to Ansible collections with full custom resource support
- **Chef Supermarket Integration**: Access 100+ pre-built compliance profiles from Chef Supermarket (CIS benchmarks, DevSec baselines, DISA STIGs)
- **Infrastructure as Code Testing**: Test your infrastructure configurations using InSpec's DSL
- **Ansible Integration**: Leverage Ansible's inventory and connection mechanisms
- **Compliance Validation**: Validate security and compliance requirements across your infrastructure
- **Multi-Platform Support**: Test Linux, Windows, macOS, and cloud platforms
- **Human-Readable Tests**: Write tests in a clear, understandable languagePyPI (Recommended)

```bash
pip install ansible-inspec
```

### From Docker Hub

```bash
# Pull the latest image
docker pull htunnthuthu/ansible-inspec:latest

# Run with help
docker run --rm htunnthuthu/ansible-inspec:latest --help
```

See [Docker Usage Guide](docs/DOCKER.md) for detailed Docker instructions.

## Documentation

- **[API Documentation](docs/API.md)** - Complete Python API and CLI reference
- **[Publishing Guide](docs/PUBLISHING-GUIDE.md)** - PyPI and Docker publishing instructions
- **[Docker Usage](docs/DOCKER.md)** - Docker-specific usage and examples
- **[Profile Conversion](docs/PROFILE-CONVERSION.md)** - Converting InSpec profiles to Ansible
- **[Reporter Modes](docs/REPORTER-MODES.md)** - Native vs InSpec-free reporting
- **[Chef Supermarket](docs/CHEF-SUPERMARKET.md)** - Accessing compliance profiles
- **[Quick Start](docs/getting-started.md)** - Getting started guide

### From Source

```bash
git clone https://github.com/htunn/ansible-inspec.git
cd ansible-inspec
pip install -e .
```

### Binary Installation

Download the latest binary from the [releases page](https://github.com/htunn/ansible-inspec/releases).

```bash
# Linux/macOS
curl -LO https://github.com/htunn/ansible-inspec/releases/latest/download/ansible-inspec
chmod +x ansible-inspec
sudo mv ansible-inspec /usr/local/bin/
```

## Usage

### Basic Command

```bash
# Run InSpec profile against Ansible inventory
ansible-inspec exec profile.rb -i inventory.yml

# Run compliance tests on specific hosts
ansible-inspec exec compliance/ --target ssh://user@hostname

# Execute with custom reporter and output
ansible-inspec exec profile.rb -i inventory.yml --reporter json --output report.json

# Multiple reporters
ansible-inspec exec profile.rb -i inventory.yml --reporter "cli json:.compliance-reports/report.json html:.compliance-reports/report.html"
```

### Reporter Options

Generate compliance reports in multiple formats:

```bash
# JSON report (InSpec schema-compatible)
ansible-inspec exec profile/ -i inventory.yml --reporter json -o .compliance-reports/report.json

# HTML report
ansible-inspec exec profile/ -i inventory.yml --reporter html -o .compliance-reports/report.html

# JUnit XML for CI/CD integration
ansible-inspec exec profile/ -i inventory.yml --reporter junit -o .compliance-reports/junit.xml

# Multiple formats simultaneously
ansible-inspec exec profile/ -i inventory.yml \
  --reporter "cli json:.compliance-reports/results.json html:.compliance-reports/results.html"
```

**Supported Formats**:
- `cli` - Human-readable console output (default)
- `json` - InSpec JSON schema format
- `html` - HTML report with summary and details
- `junit` - JUnit XML for Jenkins/GitLab CI
- `yaml` - YAML format output

Reports are saved to `.compliance-reports/` by default, compatible with InSpec tooling including Chef Automate and CI/CD pipelines.

### Chef Supermarket Profiles

Leverage 100+ pre-built compliance profiles from [Chef Supermarket](https://supermarket.chef.io):

```bash
# Run DevSec Linux Baseline against your inventory
ansible-inspec exec dev-sec/linux-baseline --supermarket -i inventory.yml

# Test SSH configuration security
ansible-inspec exec dev-sec/ssh-baseline --supermarket -t ssh://prod-server

# Docker CIS Benchmark compliance
ansible-inspec exec cis-docker-benchmark --supermarket -t docker://container_id

# Web server hardening (Apache, Nginx)
ansible-inspec exec dev-sec/nginx-baseline --supermarket -i web_servers.yml

# Database security (MySQL, PostgreSQL)
ansible-inspec exec dev-sec/postgres-baseline --supermarket -i database.yml
```

**Popular Profiles**:
- `dev-sec/linux-baseline` - OS hardening (56 controls)
- `dev-sec/ssh-baseline` - SSH security (28 controls)
- `cis-docker-benchmark` - CIS Docker 1.3.0 (100+ controls)
- `cis-kubernetes-benchmark` - Kubernetes security
- `dev-sec/apache-baseline` - Apache hardening
- `dev-sec/mysql-baseline` - MySQL/MariaDB security
- `dev-sec/nginx-baseline` - Nginx hardening
- `dev-sec/postgres-baseline` - PostgreSQL security

See [Chef Supermarket Guide](docs/CHEF-SUPERMARKET.md) for complete documentation.

### Profile Conversion

Convert InSpec compliance profiles (Ruby) to Ansible collections:

```bash
# Convert local InSpec profile
ansible-inspec convert examples/profiles/custom-compliance \
  --namespace example \
  --collection-name custom_compliance

# Convert Chef Supermarket profile
ansible-inspec exec dev-sec/linux-baseline --supermarket --download ./profiles
ansible-inspec convert ./profiles/linux-baseline \
  --namespace devsec \
  --collection-name linux_baseline

# Use the converted collection
ansible-galaxy collection install ./collections/ansible_collections/example/custom_compliance/*.tar.gz
ansible-playbook example.custom_compliance.compliance_check -i inventory.yml
```

**Automatic Compliance Reporting**: Converted collections include an auto-enabled callback plugin that generates InSpec-compatible reports in `.compliance-reports/`:

```bash
# Reports are automatically generated when running playbooks
cd collections/ansible_collections/example/custom_compliance
ansible-playbook playbooks/compliance_check.yml -i inventory.yml

# Find reports in .compliance-reports/
ls .compliance-reports/
# 20260108-143022-example.custom_compliance-compliance_check.yml.json
# 20260108-143022-example.custom_compliance-compliance_check.yml.html
```

Configure reporting in `ansible.cfg`:

```ini
[defaults]
callbacks_enabled = compliance_reporter
callback_result_dir = .compliance-reports

[callback_compliance_reporter]
output_format = json  # or html, junit
```

**Conversion Features**:
- **Native Ansible Tasks**: Converts standard InSpec resources (file, service, package) to native Ansible modules for better performance
- **Custom Resource Support**: Preserves custom InSpec resources from `libraries/` directory with InSpec wrapper
- **Full Collection Structure**: Generates complete Ansible Galaxy-ready collection with roles, playbooks, and documentation
- **Automatic Detection**: Identifies and handles custom resources automatically
- **Metadata Preservation**: Maintains profile information, tags, and dependencies in `galaxy.yml`

**Example Use Cases**:
- Convert Chef Supermarket profiles for Ansible-native execution
- Migrate existing InSpec compliance tests to Ansible collections
- Publish compliance collections to Ansible Galaxy
- Integrate InSpec-based compliance into Ansible CI/CD pipelines

See [Profile Conversion Guide](docs/PROFILE-CONVERSION.md) for complete documentation.

### Example Profile

```ruby
# compliance/ssh_config.rb
describe sshd_config do
  its('PermitRootLogin') { should eq 'no' }
  its('PasswordAuthentication') { should eq 'no' }
end

describe package('telnetd') do
  it { should_not be_installed }
end
```

### Ansible Inventory Integration

```yaml
# inventory.yml
all:
  hosts:
    web-01:
      ansible_host: 192.168.1.10
    web-02:
      ansible_host: 192.168.1.11
  vars:
    ansible_user: admin
    inspec_profile: compliance/web-server
```

```bash
ansible-inspec exec -i inventory.yml
```

## Quick Start

1. **Install ansible-inspec**
   ```bash
   pip install ansible-inspec
   ```

2. **Create a compliance profile**
   ```bash
   ansible-inspec init profile my-compliance
   ```

3. **Run tests against your infrastructure**
   ```bash
   ansible-inspec exec my-compliance -i inventory.yml
   ```

## Documentation

- [Getting Started Guide](docs/getting-started.md)
- [Writing Compliance Profiles](docs/profiles.md)
- [Ansible Integration](docs/ansible-integration.md)
- [Command Reference](docs/command-reference.md)

## Project Structure

```
ansible-inspec/
├── bin/
│   └── ansible-inspec          # Main executable
├── lib/
│   ├── ansible_inspec/
│   │   ├── ansible_adapter/    # Ansible integration layer
│   │   ├── inspec_adapter/     # InSpec integration layer
│   │   ├── cli/                # CLI interface
│   │   └── core/               # Core functionality
├── profiles/                   # Example compliance profiles
├── tests/                      # Test suite
├── docs/                       # Documentation
└── examples/                   # Usage examples
```

## How It Works

Ansible-InSpec orchestrates compliance testing by combining Ansible's inventory management with InSpec's testing capabilities:

```mermaid
sequenceDiagram
    participant User
    participant CLI as ansible-inspec CLI
    participant Ansible as Ansible Adapter
    participant InSpec as InSpec Adapter
    participant Inventory as Ansible Inventory
    participant Target as Target Hosts
    
    autonumber
    
    rect rgb(230, 240, 255)
    Note over User,CLI: Initialization Phase
    User->>+CLI: ansible-inspec exec profile.rb -i inventory.yml
    CLI->>CLI: Parse arguments & validate inputs
    CLI->>+Ansible: Load inventory configuration
    end
    
    rect rgb(240, 255, 240)
    Note over Ansible,Inventory: Inventory Processing
    Ansible->>+Inventory: Parse YAML inventory
    Inventory-->>-Ansible: Host groups & variables
    Ansible->>Ansible: Build host list with connection details
    Note right of Ansible: Supports SSH, WinRM,<br/>Docker, local connections
    Ansible-->>-CLI: Return target hosts with URIs
    end
    
    rect rgb(255, 245, 230)
    Note over CLI,InSpec: Profile Validation
    CLI->>+InSpec: Load InSpec profile
    InSpec->>InSpec: Validate profile structure
    InSpec->>InSpec: Parse controls & tests
    InSpec-->>-CLI: Profile ready
    end
    
    rect rgb(255, 240, 245)
    Note over CLI,Target: Execution Phase (Parallel)
    par For each target host
        CLI->>+InSpec: Execute profile on host-1
        InSpec->>+Target: SSH/WinRM connection
        Target-->>-InSpec: System information
        InSpec->>Target: Run compliance checks
        Target-->>InSpec: Check results
        InSpec->>InSpec: Aggregate test results
        InSpec-->>-CLI: Host-1 results
    and
        CLI->>+InSpec: Execute profile on host-2
        InSpec->>+Target: SSH/WinRM connection
        Target-->>-InSpec: System information
        InSpec->>Target: Run compliance checks
        Target-->>InSpec: Check results
        InSpec->>InSpec: Aggregate test results
        InSpec-->>-CLI: Host-2 results
    and
        CLI->>+InSpec: Execute profile on host-N
        InSpec->>+Target: SSH/WinRM connection
        Target-->>-InSpec: System information
        InSpec->>Target: Run compliance checks
        Target-->>InSpec: Check results
        InSpec->>InSpec: Aggregate test results
        InSpec-->>-CLI: Host-N results
    end
    end
    
    rect rgb(245, 245, 255)
    Note over CLI,User: Results & Reporting
    CLI->>CLI: Aggregate all host results
    CLI->>CLI: Generate compliance report
    CLI-->>-User: Display results (JSON/CLI/HTML)
    
    alt All tests passed
        Note over User: ✅ Infrastructure compliant
    else Some tests failed
        Note over User: ❌ Non-compliance detected<br/>Review failed controls
    end
    end
```

### Workflow Explanation

1. **Initialization**: User runs `ansible-inspec` with a profile and inventory
2. **Inventory Loading**: Ansible adapter parses the YAML inventory and extracts:
   - Host definitions and groups
   - Connection details (SSH keys, passwords, ports)
   - Variables and host-specific configurations
3. **Profile Validation**: InSpec adapter loads and validates the compliance profile
4. **Parallel Execution**: Tests run simultaneously across all target hosts:
   - Establishes connections using Ansible's connection URIs
   - Executes InSpec controls on each host
   - Collects pass/fail results for each control
5. **Results Aggregation**: Combines results from all hosts into unified report
6. **Output**: Presents compliance status in requested format (JSON, CLI, HTML)

### Connection Flow Details

The tool supports multiple connection types automatically detected from your Ansible inventory:

- **SSH**: `ssh://user@hostname:port` with key or password authentication
- **WinRM**: `winrm://user@hostname:port` for Windows hosts
- **Docker**: `docker://container_id` for containerized targets
- **Local**: `local://` for testing the local system

## Upstream Projects

This project builds upon two excellent open-source projects:

### Ansible
- **Repository**: https://github.com/ansible/ansible
- **License**: GPL-3.0
- **Description**: IT automation platform
- **Website**: https://www.ansible.com

### InSpec
- **Repository**: https://github.com/inspec/inspec
- **License**: Apache-2.0
- **Description**: Compliance and security testing framework
- **Website**: https://www.inspec.io

## Docker Usage

```bash
# Initialize a new InSpec profile
docker run --rm -v $(pwd):/workspace htunnthuthu/ansible-inspec:latest \
  init profile my-compliance-tests

# Run compliance tests with Ansible inventory
docker run --rm \
  -v $(pwd):/workspace \
  -v ~/.ssh:/home/ansibleinspec/.ssh:ro \
  htunnthuthu/ansible-inspec:latest \
  exec /workspace/profiles/cis-benchmark \
  -i /workspace/inventory.yml

# Available tags: latest, v0.1.0, v0.2.0, etc.
docker run --rm htunnthuthu/ansible-inspec:v0.1.0 --version
```

See [Docker Usage Guide](docs/DOCKER.md) for more examples.

## Development

### Quick Start

```bash
# Clone repository
git clone https://github.com/Htunn/ansible-inspec.git
cd ansible-inspec

# Install with dev dependencies
make dev-install

# Run tests
make test

# Format code
make format

# Build package
make build
```

See [QUICKSTART.md](docs/QUICKSTART.md) for detailed development setup.

## Publishing

This project uses automated publishing via GitHub Actions:

1. **PyPI**: Triggered by git tags (e.g., `v0.1.0`)
2. **Docker Hub**: Triggered by git tags, builds multi-arch images

See [Publishing Guide](docs/PUBLISHING.md) for details.

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

Since this project combines components from:
- Ansible (GPL-3.0 licensed)
- InSpec (Apache-2.0 licensed)

The combined work must be distributed under GPL-3.0, as it is the more restrictive license. The Apache-2.0 license is compatible with GPL-3.0, allowing this combination.

See [LICENSE](LICENSE) for the full license text and [NOTICE](NOTICE) for detailed attribution and license compatibility information.

### Why GPL-3.0?

When combining GPL-licensed code (Ansible) with Apache-2.0 licensed code (InSpec), the GPL license governs the combined work. This ensures:
- Compliance with Ansible's GPL-3.0 licensing requirements
- Proper attribution to both upstream projects
- Legal compatibility between the two licenses
- Protection of user freedoms as intended by both projects

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Code of Conduct

This project adheres to the codes of conduct from both upstream projects:
- [Ansible Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
- [InSpec Code of Conduct](https://github.com/inspec/inspec/blob/main/CODE_OF_CONDUCT.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/htunn/ansible-inspec/issues)
- **Discussions**: [GitHub Discussions](https://github.com/htunn/ansible-inspec/discussions)
- **Chat**: Join our community chat

## Acknowledgments

Special thanks to:
- The Ansible team and community at Red Hat
- The InSpec team and community at Progress Chef
- All contributors to both upstream projects

## Roadmap

- [x] Initial project structure and licensing
- [ ] Core integration layer between Ansible and InSpec
- [ ] CLI implementation
- [ ] Ansible inventory support
- [ ] InSpec profile execution engine
- [ ] Documentation and examples
- [ ] Test suite
- [ ] Binary distribution
- [ ] CI/CD pipeline

## Disclaimer

This is an independent project that integrates Ansible and InSpec. It is not officially endorsed by Red Hat, Progress Software, or Chef Software Inc. All trademarks belong to their respective owners.

