# Prisma Quick Reference for ansible-inspec

## Setup Commands

```bash
# Install dependencies
pip install -e .

# Set database URL
export DATABASE_URL="postgresql://ansible:ansible@localhost:5432/ansible_inspec"

# Generate Prisma client
prisma generate

# Create/update database schema
prisma db push

# View database in browser
prisma studio  # http://localhost:5555

# Initialize with default data
python scripts/init_prisma.py
```

## Common Query Patterns

### Find Unique
```python
from prisma import Prisma

db = Prisma()
await db.connect()

# By ID
user = await db.user.find_unique(where={"id": user_id})

# By unique field
user = await db.user.find_unique(where={"email": "john@example.com"})
```

### Find Many with Filtering
```python
# Basic filter
templates = await db.jobtemplate.find_many(
    where={"vcsSync": True}
)

# Multiple conditions (AND)
templates = await db.jobtemplate.find_many(
    where={
        "vcsSync": True,
        "tenantId": tenant_id
    }
)

# OR conditions
templates = await db.jobtemplate.find_many(
    where={
        "OR": [
            {"name": {"contains": "linux"}},
            {"description": {"contains": "linux"}}
        ]
    }
)

# Pagination
templates = await db.jobtemplate.find_many(
    skip=10,
    take=20,
    order={"createdAt": "desc"}
)
```

### Include Relations
```python
# Include single relation
job = await db.job.find_unique(
    where={"id": job_id},
    include={"template": True, "creator": True}
)
# Access: job.template.name, job.creator.username

# Include nested relations
workflow = await db.workflowtemplate.find_unique(
    where={"id": workflow_id},
    include={
        "nodes": {
            "include": {"template": True}
        }
    }
)
# Access: workflow.nodes[0].template.name
```

### Create Records
```python
# Simple create
user = await db.user.create(
    data={
        "username": "john",
        "email": "john@example.com",
        "roles": ["operator"],
        "active": True
    }
)

# Create with relation
template = await db.jobtemplate.create(
    data={
        "name": "linux-baseline",
        "profile": "https://github.com/dev-sec/linux-baseline.git",
        "createdBy": user.id,
        "vcsRepoId": repo.id
    }
)

# Create many (bulk insert)
await db.user.create_many(
    data=[
        {"username": "user1", "email": "user1@example.com"},
        {"username": "user2", "email": "user2@example.com"}
    ]
)
```

### Update Records
```python
# Update by ID
user = await db.user.update(
    where={"id": user_id},
    data={"lastLogin": datetime.now()}
)

# Update with increment
job = await db.job.update(
    where={"id": job_id},
    data={
        "status": "running",
        "startedAt": datetime.now()
    }
)

# Upsert (create or update)
user = await db.user.upsert(
    where={"email": "john@example.com"},
    data={
        "create": {
            "username": "john",
            "email": "john@example.com",
            "roles": ["viewer"]
        },
        "update": {
            "lastLogin": datetime.now()
        }
    }
)
```

### Delete Records
```python
# Delete one
await db.jobtemplate.delete(where={"id": template_id})

# Delete many
count = await db.job.delete_many(
    where={"status": "failed"}
)
# Returns: {"count": 42}
```

### Count Records
```python
# Count all
total = await db.user.count()

# Count with filter
active_users = await db.user.count(
    where={"active": True}
)
```

### Transactions
```python
async with db.tx() as transaction:
    # Create user
    user = await transaction.user.create(
        data={"username": "john", "email": "john@example.com"}
    )
    
    # Create template
    template = await transaction.jobtemplate.create(
        data={
            "name": "test",
            "profile": "path",
            "createdBy": user.id
        }
    )
    
    # Both committed together or rolled back on error
```

## Schema Management

### Development Workflow
```bash
# 1. Edit schema.prisma
# 2. Generate client
prisma generate

# 3. Push to database (overwrites, no migration history)
prisma db push

# 4. Verify in Studio
prisma studio
```

### Production Workflow
```bash
# 1. Edit schema.prisma
# 2. Create migration
prisma migrate dev --name add_user_roles

# 3. Review migration SQL in prisma/migrations/
# 4. Generate client
prisma generate

# 5. Apply in production
prisma migrate deploy
```

### Common Schema Changes

#### Add Field
```prisma
model User {
  id          String   @id @default(uuid())
  username    String   @unique
  phoneNumber String?  @map("phone_number")  // Add this
}
```

#### Add Index
```prisma
model Job {
  id        String   @id @default(uuid())
  status    String
  createdAt DateTime @default(now())
  
  @@index([status, createdAt])  // Add this
}
```

#### Add Relation
```prisma
model JobTemplate {
  id    String @id @default(uuid())
  name  String
  owner User?  @relation(fields: [ownerId], references: [id])
  ownerId String? @map("owner_id")
}

model User {
  id String @id @default(uuid())
  ownedTemplates JobTemplate[]
}
```

## Context Manager Pattern

```python
from ansible_inspec.server.db.prisma_client import get_db

async def my_function():
    async with get_db() as db:
        # Use db here
        user = await db.user.find_unique(where={"id": user_id})
    # Connection automatically managed
```

## Storage Backend Usage

```python
from ansible_inspec.server.storage import create_storage

# Create backend based on environment
storage = create_storage(
    storage_backend="database",  # or "file", "hybrid"
    data_dir="./data"
)

# Use storage backend
template = await storage.get_job_template(template_id)
await storage.save_job_template(template)
```

## VCS Manager Usage

```python
from ansible_inspec.server.vcs.manager import VCSManager
from ansible_inspec.server.encryption import EncryptionService

encryption = EncryptionService(key=encryption_key)
manager = VCSManager(storage, encryption)

# Sync repository
result = await manager.sync_repository("my-repo")

# Manual trigger
result = await manager.trigger_manual_sync("my-repo")

# List all sync jobs
jobs = await manager.list_sync_jobs()
```

## Troubleshooting

### Client Not Generated
```bash
prisma generate
```

### Table Doesn't Exist
```bash
prisma db push
```

### Connection Error
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### Schema Validation Failed
```bash
# Check syntax
prisma validate

# View error details
prisma db push --help
```

### Type Errors
```bash
# Regenerate client
prisma generate

# Restart IDE/language server
```

## Best Practices

1. **Always use context manager** for database connections
2. **Use transactions** for multi-step operations
3. **Include relations selectively** to avoid over-fetching
4. **Add indexes** for frequently queried fields
5. **Use `create_many`** for bulk inserts (more efficient)
6. **Validate data** before creating records
7. **Handle errors** gracefully (Prisma raises exceptions)
8. **Run migrations** in production (don't use `db push`)
9. **Test schema changes** in development first
10. **Keep Prisma client** in sync with schema

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Optional
PRISMA_QUERY_ENGINE_LIBRARY=/path/to/libquery_engine.so
PRISMA_QUERY_ENGINE_BINARY=/path/to/query-engine
DEBUG=prisma*  # Enable debug logging
```

## References

- [Prisma Python Docs](https://prisma-client-py.readthedocs.io/)
- [Schema Reference](https://www.prisma.io/docs/reference/api-reference/prisma-schema-reference)
- [Query API](https://prisma-client-py.readthedocs.io/en/stable/reference/operations/)
- [Migrations](https://www.prisma.io/docs/concepts/components/prisma-migrate)
