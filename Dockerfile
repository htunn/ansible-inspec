# Multi-stage build for ansible-inspec
FROM python:3.12-slim AS builder

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

# Install the package
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir .

# Final stage - runtime
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  openssh-client \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Install InSpec
RUN curl -fsSL https://omnitruck.chef.io/install.sh | bash -s -- -P inspec

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash ansibleinspec && \
  mkdir -p /workspace && \
  chown -R ansibleinspec:ansibleinspec /workspace

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



