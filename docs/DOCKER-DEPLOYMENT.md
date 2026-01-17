# Docker Deployment Guide

## Quick Start

### 1. Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- At least 2GB RAM available
- Port 8080 and 5432 available

### 2. Setup Environment

```bash
# Copy Docker environment template
cp .env.docker .env

# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env and set:
# - POSTGRES_PASSWORD (required)
# - ENCRYPTION_KEY (generated above)
# - AUTH__JWT_SECRET (generated above)
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec api prisma db push

# Verify database connection
docker-compose exec api prisma db execute --stdin <<< "SELECT 1"
```

### 5. Access the API

- **API**: http://localhost:8080
- **Health Check**: http://localhost:8080/health
- **API Docs**: http://localhost:8080/docs
- **OpenAPI Schema**: http://localhost:8080/openapi.json

## Configuration

### Environment Variables

All configuration is done via the `.env` file. Key variables:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `POSTGRES_PASSWORD` | PostgreSQL password | ✅ | - |
| `ENCRYPTION_KEY` | Fernet encryption key | ✅ | - |
| `AUTH__JWT_SECRET` | JWT signing secret | ✅ | - |
| `AUTH__ENABLED` | Enable Azure AD auth | ❌ | `false` |
| `STORAGE_BACKEND` | Storage type: file/database/hybrid | ❌ | `database` |
| `VCS__ENABLED` | Enable VCS sync | ❌ | `false` |

### Volumes

- `postgres_data` - PostgreSQL database files (persistent)
- `./data` - Application data directory (mounted)
- `./profiles` - Local InSpec profiles directory (mounted, read-only)

### Networks

- `ansible-inspec-network` - Bridge network for services

## Usage

### Create Job Template

```bash
# Using curl
curl -X POST http://localhost:8080/api/v1/job-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "linux-baseline",
    "description": "CIS Linux Baseline",
    "profile": "dev-sec/linux-baseline",
    "supermarket": true,
    "inventory": ["hosts.yml"]
  }'
```

### List Job Templates

```bash
curl http://localhost:8080/api/v1/job-templates
```

### Execute Job

```bash
curl -X POST http://localhost:8080/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "linux-baseline"
  }'
```

## Management

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres
```

### Restart Services

```bash
# Restart API
docker-compose restart api

# Restart all
docker-compose restart
```

### Stop Services

```bash
# Stop all services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (⚠️  destroys data)
docker-compose down -v
```

### Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U ansibleinspec ansibleinspec > backup.sql

# Restore
cat backup.sql | docker-compose exec -T postgres psql -U ansibleinspec ansibleinspec
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

## Production Deployment

### Security Checklist

- [ ] Change `POSTGRES_PASSWORD` from default
- [ ] Generate unique `ENCRYPTION_KEY`
- [ ] Generate unique `AUTH__JWT_SECRET`
- [ ] Enable `AUTH__ENABLED=true` with Azure AD credentials
- [ ] Set `DEBUG=false`
- [ ] Configure HTTPS reverse proxy (nginx/traefik)
- [ ] Set up automated backups
- [ ] Configure monitoring/alerting
- [ ] Review CORS origins
- [ ] Use named volumes for production data

### Recommended nginx Configuration

```nginx
server {
    listen 80;
    server_name ansible-inspec.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ansible-inspec.example.com;

    ssl_certificate /etc/ssl/certs/ansible-inspec.crt;
    ssl_certificate_key /etc/ssl/private/ansible-inspec.key;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Health Monitoring

```bash
# Health check endpoint
curl http://localhost:8080/health

# Response:
# {
#   "status": "healthy",
#   "version": "0.4.0",
#   "storage_backend": "database",
#   "auth_enabled": false,
#   "vcs_enabled": false
# }
```

### Prometheus Metrics

Metrics are available at `http://localhost:8080/metrics` for monitoring:

```bash
curl http://localhost:8080/metrics
```

## Troubleshooting

### API Won't Start

```bash
# Check logs
docker-compose logs api

# Common issues:
# 1. Database not ready - wait for postgres health check
# 2. Missing environment variables - check .env file
# 3. Port conflict - change API_PORT in .env
```

### Database Connection Failed

```bash
# Check postgres is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U ansibleinspec -d ansibleinspec -c "SELECT 1"

# Check DATABASE_URL format
docker-compose exec api env | grep DATABASE
```

### Permission Issues

```bash
# Fix data directory permissions
sudo chown -R 1000:1000 ./data

# Recreate container
docker-compose down
docker-compose up -d
```

## Development

### Development Mode

```bash
# Mount source code for live reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Run tests
docker-compose exec api pytest

# Access shell
docker-compose exec api bash
```

### Database Shell

```bash
# PostgreSQL shell
docker-compose exec postgres psql -U ansibleinspec

# Prisma Studio (database browser)
docker-compose exec api prisma studio
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/htunn/ansible-inspec/issues
- Documentation: https://github.com/htunn/ansible-inspec/tree/main/docs
