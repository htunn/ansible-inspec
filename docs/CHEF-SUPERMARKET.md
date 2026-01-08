# Chef Supermarket Integration

ansible-inspec integrates with [Chef Supermarket](https://supermarket.chef.io) to provide access to 100+ pre-built InSpec compliance profiles. This allows you to leverage community-tested compliance frameworks without writing tests from scratch.

## Overview

Chef Supermarket hosts curated compliance profiles from leading security frameworks:

- **DevSec Hardening Frameworks**: Security baselines for Linux, SSH, Apache, MySQL, Nginx, PostgreSQL
- **CIS Benchmarks**: Center for Internet Security hardening standards
- **DISA STIGs**: Department of Defense Security Technical Implementation Guides
- **Community Profiles**: Custom compliance frameworks shared by the community

## Quick Start

### Basic Usage

Run a Chef Supermarket profile against your infrastructure:

```bash
# Using the --supermarket flag
ansible-inspec exec dev-sec/linux-baseline --supermarket -i inventory.yml

# Test a specific target
ansible-inspec exec dev-sec/ssh-baseline --supermarket -t ssh://user@host

# Docker container testing
ansible-inspec exec cis-docker-benchmark --supermarket -t docker://container_id
```

### Python API

```python
from ansible_inspec.inspec_adapter import InSpecProfile, InSpecRunner

# Load a Supermarket profile
profile = InSpecProfile.from_supermarket('dev-sec/linux-baseline')

# Execute against a target
runner = InSpecRunner(profile, target='ssh://user@host')
result = runner.execute()

print(result.summary())  # PASSED: 45/50 tests passed
```

## Popular Compliance Profiles

### DevSec Hardening Frameworks

Industry-standard security baselines maintained by the DevSec project:

#### Linux Baseline
```bash
ansible-inspec exec dev-sec/linux-baseline --supermarket -i inventory.yml
```
**Tests**: 56 controls covering OS hardening, file permissions, user management, kernel parameters

**Use Cases**: 
- General Linux server hardening
- Meeting SOC 2 security requirements
- Pre-deployment security validation

#### SSH Baseline
```bash
ansible-inspec exec dev-sec/ssh-baseline --supermarket -t ssh://prod-server
```
**Tests**: 28 controls for SSH configuration security

**Key Checks**:
- Disabled password authentication
- Strong cipher configurations
- Proper permission settings
- Protocol version enforcement

#### Apache Baseline
```bash
ansible-inspec exec dev-sec/apache-baseline --supermarket -i web_servers.yml
```
**Tests**: 15 controls for Apache HTTP Server hardening

**Key Checks**:
- Directory listing disabled
- Server tokens hidden
- SSL/TLS configuration
- File permissions

#### MySQL Baseline
```bash
ansible-inspec exec dev-sec/mysql-baseline --supermarket -i database.yml
```
**Tests**: 20+ controls for MySQL/MariaDB security

**Key Checks**:
- Anonymous user removal
- Test database removal
- Strong password policies
- Network exposure controls

#### Nginx Baseline
```bash
ansible-inspec exec dev-sec/nginx-baseline --supermarket -i web_servers.yml
```
**Tests**: 12 controls for Nginx hardening

**Key Checks**:
- Directory listing disabled
- Server version hidden
- SSL/TLS best practices
- Access controls

#### PostgreSQL Baseline
```bash
ansible-inspec exec dev-sec/postgres-baseline --supermarket -i postgres.yml
```
**Tests**: 25+ controls for PostgreSQL security

**Key Checks**:
- Authentication configuration
- Connection encryption
- File permissions
- User privilege separation

### CIS Benchmarks

Center for Internet Security industry-accepted configuration standards:

#### CIS Docker Benchmark
```bash
ansible-inspec exec cis-docker-benchmark --supermarket -t docker://container
```
**Tests**: 100+ controls based on CIS Docker 1.3.0 benchmark

**Coverage**:
- Docker daemon configuration
- Container runtime security
- Image security
- Network configuration
- Logging and auditing

#### CIS Kubernetes Benchmark
```bash
ansible-inspec exec cis-kubernetes-benchmark --supermarket -i k8s_cluster.yml
```
**Tests**: Comprehensive Kubernetes security validation

**Coverage**:
- API server configuration
- Controller manager settings
- Scheduler security
- etcd configuration
- Worker node security

### DISA STIGs

Department of Defense Security Technical Implementation Guides:

```bash
# Red Hat Enterprise Linux STIG
ansible-inspec exec disa-rhel7-stig --supermarket -i rhel_servers.yml

# Windows Server STIG
ansible-inspec exec disa-windows-2019-stig --supermarket -i windows.yml
```

**Compliance Level**: Government-grade security standards for high-security environments

## Advanced Usage

### Multi-Profile Testing

Test against multiple compliance frameworks:

```bash
#!/bin/bash
# multi-profile-test.sh

profiles=(
  "dev-sec/linux-baseline"
  "dev-sec/ssh-baseline"
  "cis-docker-benchmark"
)

for profile in "${profiles[@]}"; do
  echo "Testing: $profile"
  ansible-inspec exec "$profile" --supermarket -i inventory.yml
done
```

### Waiving Specific Controls

Create a waiver file to skip specific controls:

```yaml
# waiver.yml
dev-sec/linux-baseline:
  - control_id: os-05
    reason: Custom kernel parameters required
    expiration: 2026-12-31
  - control_id: os-10
    reason: Legacy application compatibility
```

### Custom Attributes

Override profile defaults with custom attributes:

```bash
ansible-inspec exec dev-sec/linux-baseline \
  --supermarket \
  -i inventory.yml \
  --attrs custom-attributes.yml
```

```yaml
# custom-attributes.yml
password_max_age: 60
password_min_length: 12
login_grace_time: 30
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Compliance Testing

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 2 * * 1'  # Weekly Monday 2am

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install ansible-inspec
        run: pip install ansible-inspec
      
      - name: Install InSpec
        run: |
          curl https://omnitruck.chef.io/install.sh | sudo bash -s -- -P inspec
      
      - name: Run Linux Baseline
        run: |
          ansible-inspec exec dev-sec/linux-baseline \
            --supermarket \
            -i inventory/production.yml \
            --reporter cli json:compliance-results.json
      
      - name: Upload Results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: compliance-results
          path: compliance-results.json
      
      - name: Check Compliance
        run: |
          # Fail if compliance tests failed
          python -c "
          import json, sys
          with open('compliance-results.json') as f:
              data = json.load(f)
              stats = data['statistics']
              if stats['failed'] > 0:
                  print(f'❌ {stats[\"failed\"]} compliance controls failed')
                  sys.exit(1)
              print(f'✅ All {stats[\"passed\"]} compliance controls passed')
          "
```

### GitLab CI

```yaml
# .gitlab-ci.yml
compliance:
  stage: test
  image: python:3.12
  before_script:
    - pip install ansible-inspec
    - curl https://omnitruck.chef.io/install.sh | bash -s -- -P inspec
  script:
    - |
      ansible-inspec exec dev-sec/linux-baseline \
        --supermarket \
        -i inventory.yml \
        --reporter cli json:compliance.json
  artifacts:
    when: always
    reports:
      junit: compliance.json
    paths:
      - compliance.json
  rules:
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    stages {
        stage('Compliance Testing') {
            steps {
                sh '''
                    pip install ansible-inspec
                    curl https://omnitruck.chef.io/install.sh | bash -s -- -P inspec
                '''
                
                script {
                    def profiles = [
                        'dev-sec/linux-baseline',
                        'dev-sec/ssh-baseline',
                        'dev-sec/nginx-baseline'
                    ]
                    
                    profiles.each { profile ->
                        sh """
                            ansible-inspec exec ${profile} \
                                --supermarket \
                                -i inventory.yml \
                                --reporter cli json:${profile.replace('/', '_')}.json
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: '*.json', fingerprint: true
        }
    }
}
```

## Docker Usage

### Using Pre-built Image

```bash
docker run -v $(pwd)/inventory.yml:/inventory.yml \
  htunn/ansible-inspec:latest \
  exec dev-sec/linux-baseline --supermarket -i /inventory.yml
```

### Docker Compose

```yaml
version: '3.8'

services:
  compliance-test:
    image: htunn/ansible-inspec:latest
    volumes:
      - ./inventory:/inventory:ro
      - ./results:/results
    command: >
      exec dev-sec/linux-baseline
      --supermarket
      -i /inventory/production.yml
      --reporter json:/results/compliance.json
```

## Profile Discovery

### Browse Available Profiles

Visit [Chef Supermarket](https://supermarket.chef.io/tools?type=compliance_profile) to browse all available compliance profiles.

### Search Profiles

```bash
# Using InSpec directly
inspec supermarket profiles --search linux

# Common search terms
inspec supermarket profiles --search docker
inspec supermarket profiles --search cis
inspec supermarket profiles --search windows
```

### Profile Information

```bash
# Get detailed info about a profile
inspec supermarket info dev-sec/linux-baseline
```

## Best Practices

### 1. Start with Baseline Profiles

Begin with general baseline profiles before implementing specific benchmarks:

```bash
# Start here
ansible-inspec exec dev-sec/linux-baseline --supermarket -i inventory.yml

# Then add specific profiles
ansible-inspec exec dev-sec/nginx-baseline --supermarket -i web_servers.yml
```

### 2. Use Waivers for Known Exceptions

Don't modify profiles; use waivers for documented exceptions:

```yaml
# waivers.yml
dev-sec/linux-baseline:
  - control_id: os-05
    reason: "Custom kernel parameters required for application X"
    expiration: "2026-12-31"
```

### 3. Test in Stages

Test development → staging → production:

```bash
# Development
ansible-inspec exec dev-sec/linux-baseline --supermarket -i dev.yml

# Staging
ansible-inspec exec dev-sec/linux-baseline --supermarket -i staging.yml

# Production (after validation)
ansible-inspec exec dev-sec/linux-baseline --supermarket -i prod.yml
```

### 4. Combine with Custom Tests

Mix Supermarket profiles with custom controls:

```bash
# Run both Supermarket profile and custom tests
ansible-inspec exec dev-sec/linux-baseline --supermarket -i inventory.yml
ansible-inspec exec ./custom-controls -i inventory.yml
```

### 5. Regular Compliance Monitoring

Schedule regular compliance checks:

```bash
# crontab entry - weekly compliance check
0 2 * * 1 ansible-inspec exec dev-sec/linux-baseline --supermarket -i /etc/ansible/inventory.yml
```

## Troubleshooting

### Profile Download Issues

If profile download fails:

```bash
# Clear InSpec cache
rm -rf ~/.inspec/cache

# Test InSpec connectivity
inspec supermarket profiles
```

### Authentication Requirements

Some profiles may require Chef Supermarket authentication:

```bash
# Login to Chef Supermarket
inspec compliance login https://supermarket.chef.io --user your_username --token your_token

# Then run profiles
ansible-inspec exec dev-sec/linux-baseline --supermarket -i inventory.yml
```

### Version Pinning

Pin specific profile versions for reproducibility:

```bash
# InSpec native syntax (not directly supported via ansible-inspec CLI yet)
inspec exec supermarket://dev-sec/linux-baseline --version 2.8.0
```

## Contributing

### Share Your Custom Profiles

If you've created custom compliance profiles, consider sharing them on Chef Supermarket:

1. Create an InSpec profile
2. Test thoroughly
3. Upload to Chef Supermarket
4. Share with the community

Visit [Chef Supermarket](https://supermarket.chef.io) to learn more about contributing.

## Resources

- **Chef Supermarket**: https://supermarket.chef.io
- **InSpec Documentation**: https://docs.chef.io/inspec/
- **DevSec Project**: https://dev-sec.io
- **CIS Benchmarks**: https://www.cisecurity.org/cis-benchmarks
- **ansible-inspec**: https://github.com/Htunn/ansible-inspec

## Support

For issues specific to Chef Supermarket integration:

1. Check the [ansible-inspec issues](https://github.com/Htunn/ansible-inspec/issues)
2. Review [InSpec documentation](https://docs.chef.io/inspec/)
3. Visit [Chef Supermarket](https://supermarket.chef.io) for profile-specific questions
