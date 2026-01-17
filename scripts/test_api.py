#!/usr/bin/env python3
"""
Quick test script for ansible-inspec API with Prisma.

Tests basic API functionality without starting the full server.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "lib"))

async def test_api():
    """Test API components."""
    print("=== Testing Ansible-InSpec API Components ===\n")
    
    # Test 1: Import modules
    print("Test 1: Importing modules...")
    try:
        from ansible_inspec.server.config import Settings
        from ansible_inspec.server.db.prisma_client import get_prisma_client
        from ansible_inspec.server.storage import create_storage
        print("✓ Core modules imported successfully\n")
    except ImportError as e:
        print(f"✗ Import error: {e}\n")
        return False
    
    # Test 2: Load settings
    print("Test 2: Loading settings...")
    try:
        settings = Settings()
        print(f"✓ Settings loaded")
        print(f"  - Storage backend: {settings.storage_backend}")
        print(f"  - Auth enabled: {settings.auth.enabled}")
        print(f"  - VCS enabled: {settings.vcs.enabled}\n")
    except Exception as e:
        print(f"✗ Settings error: {e}\n")
        return False
    
    # Test 3: Check if Prisma is available
    print("Test 3: Checking Prisma availability...")
    try:
        from prisma import Prisma
        print("✓ Prisma Python client is available\n")
    except ImportError:
        print("✗ Prisma not found. Run: pip install prisma && prisma generate\n")
        return False
    
    # Test 4: Check storage backend
    print("Test 4: Checking storage backend...")
    try:
        storage = create_storage(
            storage_backend="file",  # Use file for testing
            data_dir="./data"
        )
        print(f"✓ Storage backend created: {type(storage).__name__}\n")
    except Exception as e:
        print(f"✗ Storage error: {e}\n")
        return False
    
    # Test 5: Import API module
    print("Test 5: Importing API module...")
    try:
        from ansible_inspec.server import api
        print("✓ API module imported successfully")
        print(f"  - App title: {api.app.title}")
        print(f"  - App version: {api.app.version}\n")
    except Exception as e:
        print(f"✗ API import error: {e}\n")
        return False
    
    print("=== All Tests Passed! ===\n")
    print("To start the API server:")
    print("  uvicorn ansible_inspec.server.api:app --reload --port 8080\n")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_api())
    sys.exit(0 if success else 1)
