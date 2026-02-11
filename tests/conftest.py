"""
Test configuration

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import sys
import os
import pytest
import tempfile
import shutil
from pathlib import Path

# Add lib directory to path for testing
lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
sys.path.insert(0, lib_path)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires database)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_inspec: mark test as requiring InSpec installation"
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def test_data_dir():
    """Create a test data directory with structure."""
    tmp = tempfile.mkdtemp()
    
    # Create standard directories
    Path(tmp, "job_templates").mkdir()
    Path(tmp, "jobs").mkdir()
    Path(tmp, "workflows").mkdir()
    Path(tmp, "users").mkdir()
    
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def sample_profile_dir(temp_dir):
    """Create a sample InSpec profile for testing."""
    profile_path = Path(temp_dir) / "sample-profile"
    profile_path.mkdir()
    
    # Create inspec.yml
    inspec_yml = profile_path / "inspec.yml"
    inspec_yml.write_text("""
name: sample-profile
title: Sample InSpec Profile
version: 1.0.0
maintainer: Test User
copyright: Test
license: Apache-2.0
summary: A sample profile for testing
""")
    
    # Create controls directory
    controls_dir = profile_path / "controls"
    controls_dir.mkdir()
    
    # Create a sample control
    control_file = controls_dir / "example.rb"
    control_file.write_text("""
control 'tmp-1.0' do
  impact 1.0
  title 'Verify /tmp exists'
  desc 'The /tmp directory should exist'
  describe file('/tmp') do
    it { should exist }
    it { should be_directory }
  end
end

control 'tmp-1.1' do
  impact 0.7
  title 'Verify /tmp is writable'
  desc 'The /tmp directory should be writable'
  describe file('/tmp') do
    it { should be_writable }
  end
end
""")
    
    yield profile_path


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables for testing."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        'DATABASE_URL': 'file:./test.db',
        'JWT_SECRET': 'test-secret-key-for-testing-only-1234567890',
        'AUTH_ENABLED': 'false',
        'VCS_ENABLED': 'false',
        'STORAGE_BACKEND': 'hybrid',
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
