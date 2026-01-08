# Docker Usage Guide

Ansible-InSpec is available as a Docker image for easy deployment and isolation.

## Quick Start

```bash
# Pull the latest image
docker pull htunnthuthu/ansible-inspec:latest

# Run with --help
docker run --rm htunnthuthu/ansible-inspec:latest --help

# Check version
docker run --rm htunnthuthu/ansible-inspec:latest --version
```

## Available Tags

- `latest` - Latest stable release
- `v0.1.0`, `v0.2.0`, etc. - Specific version tags
- `main` - Latest development build (if available)

## Common Usage Patterns

### Initialize a New InSpec Profile

```bash
# Create a new profile in the current directory
docker run --rm -v $(pwd):/workspace htunnthuthu/ansible-inspec:latest \
  init profile my-compliance-profile

# This creates: ./my-compliance-profile/
```

### Execute InSpec Tests Against Infrastructure

```bash
# Run InSpec tests with Ansible inventory
docker run --rm \
  -v $(pwd)/profiles:/workspace/profiles \
  -v $(pwd)/inventory.yml:/workspace/inventory.yml \
  -v ~/.ssh:/home/ansibleinspec/.ssh:ro \
  htunnthuthu/ansible-inspec:latest \
  exec /workspace/profiles/my-profile \
  -i /workspace/inventory.yml

# With specific targets
docker run --rm \
  -v $(pwd):/workspace \
  htunnthuthu/ansible-inspec:latest \
  exec ./profiles/security-baseline \
  -i ./inventory.yml \
  -t web-servers
```

### Mount SSH Keys for Remote Connections

```bash
# Mount SSH keys for remote host access
docker run --rm \
  -v $(pwd):/workspace \
  -v ~/.ssh:/home/ansibleinspec/.ssh:ro \
  htunnthuthu/ansible-inspec:latest \
  exec ./profiles/cis-benchmark \
  -i ./inventory.yml
```

### Save Results to Host

```bash
# Save JSON results to host directory
docker run --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/results:/workspace/results \
  htunnthuthu/ansible-inspec:latest \
  exec ./profiles/compliance-tests \
  -i ./inventory.yml \
  -o /workspace/results/report.json
```

## Docker Compose Example

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  ansible-inspec:
    image: htunnthuthu/ansible-inspec:latest
    volumes:
      - ./profiles:/workspace/profiles
      - ./inventory.yml:/workspace/inventory.yml
      - ./results:/workspace/results
      - ~/.ssh:/home/ansibleinspec/.ssh:ro
    command: >
      exec /workspace/profiles/my-profile
      -i /workspace/inventory.yml
      -o /workspace/results/report.json
```

Run with:
```bash
docker-compose run --rm ansible-inspec
```

## Building Custom Images

If you need to customize the image:

```bash
# Clone the repository
git clone https://github.com/Htunn/ansible-inspec.git
cd ansible-inspec

# Build custom image
docker build -t my-ansible-inspec:custom .

# Or with specific version
docker build --build-arg VERSION=0.1.0 -t my-ansible-inspec:0.1.0 .
```

## Multi-Architecture Support

Images are built for:
- `linux/amd64` - Intel/AMD 64-bit
- `linux/arm64` - ARM 64-bit (Apple Silicon, ARM servers)

Docker will automatically pull the correct architecture for your platform.

## Environment Variables

```bash
# Set log level
docker run --rm \
  -e LOG_LEVEL=DEBUG \
  htunnthuthu/ansible-inspec:latest --help

# Custom InSpec configuration
docker run --rm \
  -e INSPEC_CONFIG=/workspace/inspec-config.json \
  -v $(pwd):/workspace \
  htunnthuthu/ansible-inspec:latest exec ./profiles/my-profile
```

## Troubleshooting

### Permission Issues

If you encounter permission errors with mounted volumes:

```bash
# Run with user mapping
docker run --rm \
  --user $(id -u):$(id -g) \
  -v $(pwd):/workspace \
  htunnthuthu/ansible-inspec:latest --help
```

### SSH Connection Issues

Ensure SSH keys have correct permissions:

```bash
# Fix SSH key permissions before mounting
chmod 600 ~/.ssh/id_rsa

# Mount with read-only flag
docker run --rm \
  -v ~/.ssh:/home/ansibleinspec/.ssh:ro \
  ...
```

### Debugging

Run with interactive shell:

```bash
docker run -it --rm \
  -v $(pwd):/workspace \
  --entrypoint /bin/bash \
  htunnthuthu/ansible-inspec:latest
```

## Security Considerations

1. **SSH Keys**: Always mount SSH keys as read-only (`:ro`)
2. **User Isolation**: The container runs as non-root user `ansibleinspec`
3. **Network**: Consider using `--network=host` if needed for local testing
4. **Secrets**: Use Docker secrets or environment files for sensitive data

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run Compliance Tests
  run: |
    docker run --rm \
      -v ${{ github.workspace }}:/workspace \
      htunnthuthu/ansible-inspec:latest \
      exec /workspace/profiles/compliance \
      -i /workspace/inventory.yml \
      -o /workspace/results.json
```

### GitLab CI

```yaml
compliance-test:
  image: htunnthuthu/ansible-inspec:latest
  script:
    - ansible-inspec exec ./profiles/security -i ./inventory.yml
  artifacts:
    paths:
      - results/
```

## Performance Tips

1. **Use volumes for caching**:
   ```bash
   docker volume create inspec-cache
   docker run --rm -v inspec-cache:/home/ansibleinspec/.inspec ...
   ```

2. **Reduce image pulls with specific tags**:
   ```bash
   # Instead of :latest, use specific version
   docker pull htunnthuthu/ansible-inspec:v0.1.0
   ```

3. **Multi-stage builds** are already optimized in the official image

## Support

For issues with Docker images:
- GitHub Issues: https://github.com/Htunn/ansible-inspec/issues
- Docker Hub: https://hub.docker.com/r/htunnthuthu/ansible-inspec
