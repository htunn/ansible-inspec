# Helm Charts

This directory contains Helm charts for deploying Ansible InSpec on Kubernetes.

## Available Charts

### ansible-inspec

Production-ready Helm chart for deploying Ansible InSpec server with PostgreSQL database.

**Features:**
- PostgreSQL database (Bitnami subchart)
- Security hardening (Pod Security Standards)
- Horizontal Pod Autoscaler
- Network Policies
- Persistent volumes for data and VCS repos
- Ingress with TLS support
- Prometheus metrics
- Health probes

**Quick Start:**

```bash
cd ansible-inspec
helm install ansible-inspec . \
  --set postgresql.auth.password=changeme \
  --set secrets.jwtSecret=$(openssl rand -base64 32) \
  --set secrets.encryptionKey=$(openssl rand -base64 32)
```

See [ansible-inspec/README.md](ansible-inspec/README.md) for full documentation.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PV provisioner support (for persistent storage)

## Installation

```bash
# Add helm repository (when published)
helm repo add ansible-inspec https://harrytunn.github.io/ansible-inspec-charts
helm repo update

# Install chart
helm install my-release ansible-inspec/ansible-inspec
```

## Development

### Linting

```bash
helm lint ansible-inspec/
```

### Template Rendering

```bash
helm template ansible-inspec ./ansible-inspec --debug
```

### Dry Run

```bash
helm install ansible-inspec ./ansible-inspec --dry-run --debug
```

### Testing

```bash
# Install chart
helm install test-release ./ansible-inspec

# Run tests
helm test test-release

# Cleanup
helm uninstall test-release
```

## Publishing Charts

```bash
# Package chart
helm package ansible-inspec/

# Generate index
helm repo index .

# Commit and push to gh-pages branch
git checkout gh-pages
cp ansible-inspec-*.tgz .
git add .
git commit -m "Release ansible-inspec chart version X.Y.Z"
git push origin gh-pages
```

## License

GPL-3.0 - See [LICENSE](../LICENSE) file for details.
