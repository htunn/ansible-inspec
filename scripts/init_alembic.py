#!/usr/bin/env python3
"""
Initialize Alembic for ansible-inspec database migrations.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run shell command and return output"""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    
    return result.stdout


def main():
    """Initialize Alembic"""
    print("=" * 70)
    print("Initializing Alembic for ansible-inspec")
    print("=" * 70)
    print()
    
    # Check if already initialized
    alembic_dir = Path("alembic")
    if alembic_dir.exists():
        print("⚠️  Alembic already initialized!")
        response = input("Reinitialize? This will delete existing alembic/ directory (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
        
        # Remove existing alembic directory
        import shutil
        shutil.rmtree(alembic_dir)
        print("✓ Removed existing alembic/ directory")
    
    # Initialize Alembic
    print("Initializing Alembic...")
    run_command("alembic init alembic")
    print("✓ Alembic initialized")
    print()
    
    # Update env.py
    print("Configuring alembic/env.py...")
    
    env_py = alembic_dir / "env.py"
    with open(env_py, 'r') as f:
        content = f.read()
    
    # Add imports
    imports = """
# ansible-inspec imports
from ansible_inspec.server.db import Base
from ansible_inspec.server.config import settings
"""
    
    content = content.replace(
        "from alembic import context",
        f"from alembic import context{imports}"
    )
    
    # Set target_metadata
    content = content.replace(
        "target_metadata = None",
        "target_metadata = Base.metadata"
    )
    
    # Set database URL from settings
    url_config = """
    # Get database URL from settings
    configuration = context.config
    configuration.set_main_option(
        "sqlalchemy.url",
        settings.database.sync_url
    )
"""
    
    content = content.replace(
        "def run_migrations_online():",
        f"def run_migrations_online():{url_config}\n"
    )
    
    with open(env_py, 'w') as f:
        f.write(content)
    
    print("✓ Updated alembic/env.py")
    print()
    
    # Create initial migration
    print("Creating initial migration...")
    run_command("alembic revision --autogenerate -m 'Initial schema'")
    print("✓ Created initial migration")
    print()
    
    print("=" * 70)
    print("Alembic initialization complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Review migration in alembic/versions/")
    print("2. Apply migration: alembic upgrade head")
    print("3. Check database tables: psql -U ansibleinspec -d ansibleinspec -c '\\dt'")
    print()


if __name__ == "__main__":
    main()
