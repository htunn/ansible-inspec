#!/usr/bin/env python3
"""
Initialize Prisma database for ansible-inspec.

This script:
1. Generates Prisma Client Python
2. Pushes schema to database (creates tables)
3. Creates default admin user
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "lib"))

# Load environment variables from .env file
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ Loaded environment from {env_file}\n")

async def main():
    """Initialize Prisma database."""
    print("=== Ansible-InSpec Prisma Database Initialization ===\n")
    
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE__URL")
    if not database_url:
        print("⚠️  DATABASE_URL environment variable not set")
        print("Using default: postgresql://ansibleinspec:password@localhost:5432/ansibleinspec")
        database_url = "postgresql://ansibleinspec:password@localhost:5432/ansibleinspec"
    
    # Set DATABASE_URL for Prisma
    os.environ["DATABASE_URL"] = database_url
    print(f"✓ Using DATABASE_URL: {database_url.split('@')[1] if '@' in database_url else database_url}\n")
    
    # Step 1: Generate Prisma Client
    print("Step 1: Generating Prisma Client Python...")
    try:
        result = subprocess.run(
            ["prisma", "generate"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("✓ Prisma Client generated\n")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to generate Prisma Client:")
        print(e.stderr)
        return 1
    except FileNotFoundError:
        print("✗ Prisma CLI not found. Install with: pip install prisma")
        return 1
    
    # Step 2: Push schema to database
    print("Step 2: Pushing schema to database...")
    try:
        result = subprocess.run(
            ["prisma", "db", "push", "--accept-data-loss"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("✓ Database schema created\n")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to push schema:")
        print(e.stderr)
        print("\nMake sure PostgreSQL is running and DATABASE_URL is correct")
        return 1
    
    # Step 3: Create default admin user
    print("Step 3: Creating default admin user...")
    try:
        from prisma import Prisma, Json
        
        db = Prisma()
        await db.connect()
        
        # Check if admin user exists
        admin = await db.user.find_unique(where={"username": "admin"})
        
        if admin:
            print("⚠️  Admin user already exists")
        else:
            # Create admin user
            admin = await db.user.create(
                data={
                    "username": "admin",
                    "email": "admin@ansible-inspec.local",
                    "name": "Administrator",
                    "roles": Json(["admin"]),  # Use Json wrapper for JSON fields
                    "active": True,
                }
            )
            print(f"✓ Created admin user: {admin.username} ({admin.email})")
        
        await db.disconnect()
        print("\n✓ Database initialization complete!")
        print("\nNext steps:")
        print("  1. Start the API server: uvicorn ansible_inspec.server.api:app")
        print("  2. Start the UI: streamlit run lib/ansible_inspec/server/ui.py")
        print("  3. Login with username: admin (Azure AD authentication)")
        
        return 0
        
    except Exception as e:
        print(f"✗ Failed to create admin user: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
