# Prisma Python Migration Guide

This document explains how to migrate ansible-inspec from SQLAlchemy to Prisma Python ORM.

## What Changed

### Dependencies
- **Removed**: SQLAlchemy, asyncpg, psycopg2-binary, alembic, apscheduler
- **Added**: prisma (Prisma Python ORM)

### Database Schema
- Created `schema.prisma` with all models (User, JobTemplate, Job, WorkflowTemplate, etc.)
- Prisma handles migrations automatically with `prisma db push` or `prisma migrate`

### Storage Backend
- Created `PrismaStorageBackend` in [lib/ansible_inspec/server/storage/prisma_backend.py](lib/ansible_inspec/server/storage/prisma_backend.py)
- All async CRUD operations use Prisma Python client
- Hybrid storage works with Prisma backend for dual-write validation

## Quick Start

### 1. Install Dependencies

```bash
pip install -e .
```

This installs `prisma>=0.15.0` from the updated `pyproject.toml`.

### 2. Set Database URL

```bash
export DATABASE_URL="postgresql://ansible:ansible@localhost:5432/ansible_inspec"
```

**Important**: Prisma uses standard PostgreSQL URLs (no `+asyncpg` or `+aiosqlite` drivers).

### 3. Initialize Database

Run the initialization script:

```bash
python scripts/init_prisma.py
```

This script:
1. Generates Prisma Client Python from `schema.prisma`
2. Creates database tables using `prisma db push`
3. Creates default admin user

Or manually:

```bash
# Generate Prisma Client
prisma generate

# Push schema to database (creates tables)
prisma db push

# View data in Prisma Studio
prisma studio
```

### 4. Start Services

```bash
# API Server
uvicorn ansible_inspec.server.api:app --reload --port 8080

# Streamlit UI
streamlit run lib/ansible_inspec/server/ui.py --server.port 8081
```

## Prisma Commands

### Generate Client

After modifying `schema.prisma`:

```bash
prisma generate
```

### Database Migrations

**Development** (quick schema updates):
```bash
prisma db push
```

**Production** (versioned migrations):
```bash
# Create migration
prisma migrate dev --name add_audit_log

# Apply migrations in production
prisma migrate deploy
```

### View Data

Open Prisma Studio (visual database browser):

```bash
prisma studio
```

### Reset Database

⚠️ **Destructive** - Only use in development:

```bash
prisma migrate reset
```

## Schema Changes

### Adding a New Model

1. Edit `schema.prisma`:

```prisma
model MyNewModel {
  id        String   @id @default(uuid())
  name      String   @unique
  createdAt DateTime @default(now()) @map("created_at")

  @@map("my_new_models")
}
```

2. Generate client and push:

```bash
prisma generate
prisma db push
```

### Adding a Field

1. Edit model in `schema.prisma`:

```prisma
model User {
  // ... existing fields
  phoneNumber String? @map("phone_number")  // Add this
}
```

2. Update schema:

```bash
prisma generate
prisma db push
```

## Usage Examples

### Query Data

```python
from prisma import Prisma

async def get_user():
    db = Prisma()
    await db.connect()
    
    # Find unique
    user = await db.user.find_unique(where={"email": "admin@example.com"})
    
    # Find many with filters
    templates = await db.jobtemplate.find_many(
        where={"vcsSync": True},
        order={"createdAt": "desc"},
        take=10
    )
    
    # Include relations
    job = await db.job.find_first(
        where={"status": "running"},
        include={"template": True, "creator": True}
    )
    
    await db.disconnect()
```

### Create/Update

```python
# Create
user = await db.user.create(
    data={
        "username": "john",
        "email": "john@example.com",
        "roles": ["operator"],
    }
)

# Update
await db.user.update(
    where={"id": user.id},
    data={"roles": ["admin", "operator"]}
)

# Upsert (create or update)
await db.user.upsert(
    where={"email": "john@example.com"},
    data={
        "create": {"username": "john", "email": "john@example.com"},
        "update": {"lastLogin": datetime.now()}
    }
)
```

### Delete

```python
# Delete one
await db.jobtemplate.delete(where={"id": template_id})

# Delete many
await db.job.delete_many(where={"status": "failed"})
```

## Storage Backend Configuration

### File Storage (Default)

```bash
export STORAGE_BACKEND=file
export DATA_DIR=./data
```

### Database Storage (Prisma)

```bash
export STORAGE_BACKEND=database
export DATABASE_URL="postgresql://user:pass@localhost:5432/db"
```

### Hybrid Storage (Migration Mode)

```bash
export STORAGE_BACKEND=hybrid
export DATA_DIR=./data
export DATABASE_URL="postgresql://user:pass@localhost:5432/db"
export VALIDATION_DAYS=30
```

## Differences from SQLAlchemy

| Feature | SQLAlchemy | Prisma |
|---------|------------|--------|
| Schema Definition | Python classes | `schema.prisma` DSL |
| Client Generation | Runtime ORM | Generated code (type-safe) |
| Migrations | Alembic | `prisma migrate` |
| Async Support | `asyncio` extension | Native async |
| Type Safety | Partial (with mypy) | Full (generated types) |
| IDE Autocomplete | Limited | Excellent |
| Query Builder | ORM methods | Fluent API |

## Troubleshooting

### "Prisma CLI not found"

```bash
pip install prisma
```

### "Can't connect to database"

Check DATABASE_URL:
```bash
echo $DATABASE_URL
```

Verify PostgreSQL is running:
```bash
psql $DATABASE_URL -c "SELECT 1"
```

### "Table does not exist"

Run schema push:
```bash
prisma db push
```

### "Client not generated"

```bash
prisma generate
```

### "Schema validation failed"

Check `schema.prisma` syntax:
```bash
prisma validate
```

## Migration from Existing SQLAlchemy Data

If you have existing data in SQLAlchemy tables:

1. **Export existing data**:
```bash
# Your existing file-based data is in ./data/
# Or export from SQLAlchemy database
```

2. **Initialize Prisma**:
```bash
python scripts/init_prisma.py
```

3. **Import data using storage migration**:
```python
from ansible_inspec.server.storage import create_storage
from ansible_inspec.server.storage.file_backend import FileStorageBackend
from ansible_inspec.server.storage.prisma_backend import PrismaStorageBackend

async def migrate_data():
    file_backend = FileStorageBackend(data_dir="./data")
    db_backend = PrismaStorageBackend()
    
    # Migrate job templates
    templates = await file_backend.list_job_templates()
    for template in templates:
        await db_backend.save_job_template(template)
    
    # Migrate jobs
    jobs = await file_backend.list_jobs()
    for job in jobs:
        await db_backend.save_job(job)
```

## Additional Resources

- [Prisma Python Documentation](https://prisma-client-py.readthedocs.io/)
- [Prisma Schema Reference](https://www.prisma.io/docs/reference/api-reference/prisma-schema-reference)
- [Prisma CLI Reference](https://www.prisma.io/docs/reference/api-reference/command-reference)
- [Prisma Python GitHub](https://github.com/RobertCraigie/prisma-client-py)
