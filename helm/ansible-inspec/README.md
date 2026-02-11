# Ansible InSpec Helm Chart

This Helm chart deploys the Ansible InSpec server with PostgreSQL database on Kubernetes.

## Overview

Ansible InSpec is a compliance and security automation tool that integrates InSpec profiles with Ansible workflows. It provides:

- **REST API Server**: FastAPI-based server with 30+ endpoints
- **Database Backend**: PostgreSQL with Prisma ORM
- **Authentication**: Azure AD OAuth2, local password auth, JWT tokens
- **RBAC**: Admin, operator, and viewer roles
- **VCS Integration**: GitHub, GitLab with webhook support
- **Job Management**: Execute InSpec profiles via Ansible
- **Security**: Encrypted credentials, secure secrets management

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PV provisioner support in the underlying infrastructure (for persistent storage)
- PostgreSQL 12+ (if using external database)

## Installation

### Basic Installation

```bash
helm install ansible-inspec ./ansible-inspec
```

### Installation with Custom Values

```bash
helm install ansible-inspec ./ansible-inspec \
  --set image.tag=0.2.6 \
  --set postgresql.auth.password=changeme \
  --set secrets.jwtSecret=your-jwt-secret \
  --set secrets.encryptionKey=your-encryption-key
```

### Installation from Repository

```bash
helm repo add ansible-inspec https://harrytunn.github.io/ansible-inspec-charts
helm install ansible-inspec ansible-inspec/ansible-inspec
```

## Configuration

The following table lists the configurable parameters and their default values.

### Common Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `2` |
| `image.repository` | Image repository | `ghcr.io/htunn/ansible-inspec` |
| `image.tag` | Image tag | `0.2.6` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `8080` |

### Security Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `podSecurityContext.runAsNonRoot` | Run as non-root user | `true` |
| `podSecurityContext.runAsUser` | User ID | `1000` |
| `podSecurityContext.fsGroup` | Filesystem group | `1000` |
| `securityContext.allowPrivilegeEscalation` | Allow privilege escalation | `false` |
| `securityContext.capabilities.drop` | Dropped capabilities | `["ALL"]` |

### Database Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgresql.enabled` | Enable PostgreSQL subchart | `true` |
| `postgresql.auth.username` | Database username | `ansible_inspec` |
| `postgresql.auth.password` | Database password | `changeme` |
| `postgresql.auth.database` | Database name | `ansible_inspec` |
| `externalDatabase.enabled` | Use external database | `false` |

### Storage Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable persistence | `true` |
| `persistence.size` | PVC size | `10Gi` |
| `vcsStorage.enabled` | Enable VCS storage | `true` |
| `vcsStorage.size` | VCS PVC size | `20Gi` |

### Autoscaling Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `autoscaling.enabled` | Enable HPA | `true` |
| `autoscaling.minReplicas` | Minimum replicas | `2` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU % | `70` |

### Ingress Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class | `nginx` |
| `ingress.tls` | TLS configuration | `[]` |

## Example Configurations

### Production Setup with External Database

```yaml
# production-values.yaml
replicaCount: 3

postgresql:
  enabled: false

externalDatabase:
  enabled: true
  host: postgres.example.com
  port: 5432
  user: ansible_inspec
  password: "super-secret-password"
  database: ansible_inspec_prod

secrets:
  jwtSecret: "production-jwt-secret"
  encryptionKey: "production-encryption-key"

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: ansible-inspec.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: ansible-inspec-tls
      hosts:
        - ansible-inspec.example.com

resources:
  limits:
    cpu: 4000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 60
  targetMemoryUtilizationPercentage: 70
```

Install:
```bash
helm install ansible-inspec ./ansible-inspec -f production-values.yaml
```

### Azure AD Authentication

```yaml
# azure-auth-values.yaml
config:
  auth:
    enabled: true
    azureTenantId: "your-tenant-id"
    azureClientId: "your-client-id"
    azureClientSecret: "your-client-secret"
    oauthRedirectUri: "https://ansible-inspec.example.com/auth/callback"
    streamlitUiUrl: "https://ui.example.com"
```

### High Availability Setup

```yaml
# ha-values.yaml
replicaCount: 3

podDisruptionBudget:
  enabled: true
  minAvailable: 2

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          topologyKey: kubernetes.io/hostname
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: ansible-inspec

postgresql:
  primary:
    persistence:
      enabled: true
      size: 50Gi
  readReplicas:
    replicaCount: 2
```

## Security Best Practices

### 1. Change Default Secrets

**CRITICAL**: Always change default secrets in production!

```bash
# Generate secure secrets
JWT_SECRET=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)
DB_PASSWORD=$(openssl rand -base64 32)

helm install ansible-inspec ./ansible-inspec \
  --set secrets.jwtSecret="$JWT_SECRET" \
  --set secrets.encryptionKey="$ENCRYPTION_KEY" \
  --set postgresql.auth.password="$DB_PASSWORD"
```

### 2. Use Kubernetes Secrets

```bash
# Create secret externally
kubectl create secret generic ansible-inspec-secrets \
  --from-literal=jwtSecret="$JWT_SECRET" \
  --from-literal=encryptionKey="$ENCRYPTION_KEY" \
  --from-literal=postgresPassword="$DB_PASSWORD"

# Reference in values
helm install ansible-inspec ./ansible-inspec \
  --set secrets.existingSecret=ansible-inspec-secrets
```

### 3. Enable TLS on Ingress

```yaml
ingress:
  enabled: true
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  tls:
    - secretName: ansible-inspec-tls
      hosts:
        - ansible-inspec.example.com
```

### 4. Network Policies

Network policies are enabled by default to restrict traffic:
- Pods can only receive traffic from ingress controller
- Egress is limited to DNS, PostgreSQL, and HTTPS

### 5. RBAC Configuration

The chart uses a dedicated ServiceAccount with minimal permissions.

### 6. Pod Security

- Runs as non-root user (UID 1000)
- All capabilities dropped
- Read-only root filesystem
- Seccomp profile: RuntimeDefault

## Monitoring

### Prometheus Metrics

Enable ServiceMonitor for Prometheus Operator:

```yaml
serviceMonitor:
  enabled: true
  interval: 30s
  labels:
    prometheus: kube-prometheus
```

Metrics available at `/metrics` endpoint.

### Health Checks

- Liveness: `/health`
- Readiness: `/health`
- Startup: `/health` (90-second timeout)

## Persistence

### Data Persistence

Three persistent volumes are used:
1. **Data** (`/app/data`): Job templates, jobs, users
2. **VCS Repos** (`/tmp/ansible-inspec-repos`): Cloned Git repositories
3. **Profiles** (`/app/profiles`): InSpec profiles

### Backup Strategy

```bash
# Backup data PVC
kubectl exec -it deployment/ansible-inspec -- tar czf - /app/data | \
  gzip > backup-data-$(date +%Y%m%d).tar.gz

# Backup database
kubectl exec -it ansible-inspec-postgresql-0 -- pg_dump -U ansible_inspec ansible_inspec | \
  gzip > backup-db-$(date +%Y%m%d).sql.gz
```

### Disaster Recovery

```bash
# Restore data
kubectl cp backup-data-20240101.tar.gz ansible-inspec-pod:/tmp/
kubectl exec -it ansible-inspec-pod -- tar xzf /tmp/backup-data-20240101.tar.gz -C /

# Restore database
gunzip -c backup-db-20240101.sql.gz | \
  kubectl exec -i ansible-inspec-postgresql-0 -- psql -U ansible_inspec ansible_inspec
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app.kubernetes.io/name=ansible-inspec
kubectl logs -l app.kubernetes.io/name=ansible-inspec --tail=100
```

### Database Connection Issues

```bash
# Check database readiness
kubectl exec -it ansible-inspec-postgresql-0 -- pg_isready

# Test connection from app pod
kubectl exec -it deployment/ansible-inspec -- env | grep DATABASE_URL
```

### Migration Issues

```bash
# Check init container logs
kubectl logs deployment/ansible-inspec -c db-migrate

# Manual migration
kubectl exec -it deployment/ansible-inspec -- npx prisma migrate deploy
```

### Permission Issues

```bash
# Check security context
kubectl get pod ansible-inspec-xxx -o jsonpath='{.spec.securityContext}'

# Check file permissions
kubectl exec -it deployment/ansible-inspec -- ls -la /app/data
```

## Upgrading

### Upgrade Process

```bash
# Update chart
helm repo update

# Check what will change
helm diff upgrade ansible-inspec ansible-inspec/ansible-inspec

# Upgrade
helm upgrade ansible-inspec ansible-inspec/ansible-inspec

# Rollback if needed
helm rollback ansible-inspec
```

### Version Compatibility

| Chart Version | App Version | Kubernetes | PostgreSQL |
|---------------|-------------|------------|------------|
| 0.2.6 | 0.2.6 | 1.19+ | 12+ |

## Uninstalling

```bash
# Uninstall release
helm uninstall ansible-inspec

# Delete PVCs (if needed)
kubectl delete pvc -l app.kubernetes.io/instance=ansible-inspec
```

## Support

- **Documentation**: https://github.com/harrytunn/ansible-inspec
- **Issues**: https://github.com/harrytunn/ansible-inspec/issues
- **License**: GPL-3.0

## Contributing

Contributions are welcome! Please read the [Contributing Guide](../../CONTRIBUTING.md).
