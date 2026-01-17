# Docker Compose Quick Start Guide

## Prerequisites

- Docker Engine 20.10 or later
- Docker Compose V2
- 4GB RAM minimum
- 10GB disk space

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Htunn/ansible-inspec.git
cd ansible-inspec
```

### 2. Configure Environment

Copy the example environment file and customize:

```bash
cp .env.example .env
```

**Important:** Update these values in `.env` before starting:

```bash
# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update `.env`:
```bash
ENCRYPTION_KEY=<your-generated-key>
AUTH__JWT_SECRET=<your-generated-secret>
POSTGRES_PASSWORD=<strong-password>
```

### 3. Start Services

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 4. Initialize Database

```bash
# Run Prisma migrations
docker compose exec api prisma migrate deploy

# (Optional) Seed data
docker compose exec api prisma db seed
```

### 5. Verify Installation

```bash
# Check API health
curl http://localhost:8080/health

# Access API documentation
open http://localhost:8080/docs
```

## Service Architecture

```
┌─────────────────┐
│   PostgreSQL    │  Port 5432
│   (Database)    │
└────────┬────────┘
         │
         │
┌────────▼────────┐
│  ansible-inspec │  Port 8080
│   API Server    │
└─────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_USER` | PostgreSQL username | `ansibleinspec` | No |
| `POSTGRES_PASSWORD` | PostgreSQL password | - | **Yes** |
| `POSTGRES_DB` | Database name | `ansibleinspec` | No |
| `DATABASE_URL` | Full database URL | Auto-generated | No |
| `ENCRYPTION_KEY` | Fernet encryption key | - | **Yes** |
| `AUTH__JWT_SECRET` | JWT signing secret | - | **Yes** |
| `AUTH__ENABLED` | Enable authentication | `false` | No |
| `STORAGE_BACKEND` | Storage type | `database` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Storage Options

- `database` - All data in PostgreSQL (recommended for production)
- `file` - JSON files only (development/testing)
- `hybrid` - Both database and files (migration/validation)

### Volumes

Data persistence:
- `postgres_data` - PostgreSQL database
- `./data` - Job data, templates, profiles
- `./profiles` - Local InSpec profiles (read-only)

## Common Tasks

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f postgres
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart API only
docker compose restart api
```

### Database Management

```bash
# Access PostgreSQL
docker compose exec postgres psql -U ansibleinspec

# Backup database
docker compose exec postgres pg_dump -U ansibleinspec ansibleinspec > backup.sql

# Restore database
cat backup.sql | docker compose exec -T postgres psql -U ansibleinspec ansibleinspec
```

### Update to Latest Version

```bash
# Pull latest images
docker compose pull

# Rebuild and restart
docker compose up -d --build

# Run migrations
docker compose exec api prisma migrate deploy
```

## Using Job Templates

### Chef Supermarket Profiles

Run compliance profiles from Chef Supermarket:

```bash
curl -X POST http://localhost:8080/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "chef-supermarket-linux-baseline"
  }'
```

### Local InSpec Profiles

1. Place your InSpec profile in `./profiles/my-profile/`
2. Create or use existing job template with `"supermarket": false`
3. Execute job:

```bash
curl -X POST http://localhost:8080/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "local-inspec-profile"
  }'
```

## Troubleshooting

### API Won't Start

```bash
# Check logs
docker compose logs api

# Common issues:
# 1. Database not ready - wait for postgres health check
# 2. Missing environment variables - check .env file
# 3. Port conflict - change API_PORT in .env
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Test connection
docker compose exec postgres pg_isready -U ansibleinspec

# Check DATABASE_URL
docker compose exec api env | grep DATABASE
```

### Permission Issues

```bash
# Fix data directory permissions
sudo chown -R 1000:1000 ./data

# Fix profiles directory permissions
sudo chmod -R 755 ./profiles
```

## Security Considerations

### Production Deployment

1. **Change Default Passwords**: Update all passwords in `.env`
2. **Generate Strong Keys**: Use cryptographically secure keys
3. **Enable Authentication**: Set `AUTH__ENABLED=true`
4. **Use HTTPS**: Configure reverse proxy (nginx/traefik)
5. **Network Security**: Use Docker networks, limit exposed ports
6. **Regular Updates**: Keep images and dependencies updated

### Secrets Management

**Never commit `.env` to version control!**

For production:
- Use Docker secrets
- Use external secret managers (HashiCorp Vault, AWS Secrets Manager)
- Set environment variables via orchestrator (Kubernetes, Docker Swarm)

## Performance Tuning

### Database

```yaml
# In docker-compose.yml, add to postgres service:
environment:
  POSTGRES_SHARED_BUFFERS: 256MB
  POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
  POSTGRES_MAX_CONNECTIONS: 100
```

### API Server

```bash
# In .env
FORKS=10  # Increase parallel execution
```

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8080/health

# Prometheus metrics
curl http://localhost:8080/metrics
```

### Resource Usage

```bash
# Container stats
docker compose stats

# Disk usage
docker compose exec postgres du -sh /var/lib/postgresql/data
```

## Stopping Services

```bash
# Stop services (keep data)
docker compose stop

# Stop and remove containers (keep data)
docker compose down

# Remove everything including volumes (⚠️ deletes data)
docker compose down -v
```

## Next Steps

- Read [API Documentation](../ansible-inspec-docs/reference/api.md)
- Explore [Profile Conversion Guide](../ansible-inspec-docs/guides/profile-conversion.md)
- Learn about [Authentication](../ansible-inspec-docs/guides/authentication.md)
- Check [Real-world Examples](../ansible-inspec-docs/guides/real-world-examples.md)

## Support

- GitHub Issues: https://github.com/Htunn/ansible-inspec/issues
- Documentation: https://github.com/Htunn/ansible-inspec#readme
