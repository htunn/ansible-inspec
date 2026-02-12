# Multi-stage build for ansible-inspec
FROM python:3.12-slim AS builder

LABEL maintainer="ansible-inspec project contributors"
LABEL description="Compliance testing with Ansible and InSpec integration"
LABEL version="0.2.7"

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  git \
  && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY lib/ lib/

# Install the package and Prisma with multi-architecture support
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    # Install Prisma CLI for migrations
    pip install --no-cache-dir prisma && \
    # Generate Prisma client and fetch query engines for both architectures
    prisma generate && \
    # Explicitly fetch ARM64 query engine binary
    PRISMA_QUERY_ENGINE_BINARY=query-engine-linux-arm64-openssl-3.0.x \
    prisma fetch || echo "ARM64 binary fetch failed, continuing..." && \
    # Explicitly fetch x86_64 query engine binary  
    PRISMA_QUERY_ENGINE_BINARY=query-engine-linux-x86_64-openssl-3.0.x \
    prisma fetch || echo "x86_64 binary fetch failed, continuing..."

# Final stage - runtime
FROM python:3.12-slim

# Install runtime dependencies, InSpec, and create user in single RUN
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://omnitruck.chef.io/install.sh | bash -s -- -P inspec \
    && useradd -m -u 1000 -s /bin/bash ansibleinspec \
    && mkdir -p /workspace \
    && chown -R ansibleinspec:ansibleinspec /workspace

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/ansible-inspec /usr/local/bin/ansible-inspec

# Set user and working directory
USER ansibleinspec
WORKDIR /workspace

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ansible-inspec --version || exit 1

# Default command
ENTRYPOINT ["ansible-inspec"]
CMD ["--help"]



