"""
Test suite for InSpec adapter

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import pytest
import os
import tempfile
import yaml
from ansible_inspec.inspec_adapter import (
    InSpecProfile,
    InSpecRunner,
    InSpecResult
)


@pytest.fixture
def sample_profile_dir():
    """Create a sample InSpec profile directory"""
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    
    # Create inspec.yml
    inspec_yml = {
        'name': 'test-profile',
        'title': 'Test Profile',
        'version': '1.0.0',
        'summary': 'A test profile'
    }
    
    with open(os.path.join(temp_dir, 'inspec.yml'), 'w') as f:
        yaml.dump(inspec_yml, f)
    
    # Create controls directory
    controls_dir = os.path.join(temp_dir, 'controls')
    os.makedirs(controls_dir)
    
    # Create a simple control file
    control_content = """
control 'test-01' do
  impact 1.0
  title 'Test Control'
  desc 'A simple test'
  
  describe file('/etc/passwd') do
    it { should exist }
  end
end
"""
    
    with open(os.path.join(controls_dir, 'test.rb'), 'w') as f:
        f.write(control_content)
    
    yield temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


def test_inspec_result_creation():
    """Test creating an InSpecResult"""
    result = InSpecResult(
        profile='test-profile',
        target='local://',
        passed=10,
        failed=2,
        skipped=1,
        total=13,
        controls=[],
        duration=5.2
    )
    
    assert result.profile == 'test-profile'
    assert result.passed == 10
    assert result.failed == 2
    assert result.total == 13
    assert result.success is False  # Has failures
    assert 'FAILED' in result.summary()


def test_inspec_result_success():
    """Test successful result"""
    result = InSpecResult(
        profile='test-profile',
        target='local://',
        passed=10,
        failed=0,
        skipped=0,
        total=10,
        controls=[],
        duration=3.0
    )
    
    assert result.success is True
    assert 'PASSED' in result.summary()


def test_inspec_profile_loading(sample_profile_dir):
    """Test loading an InSpec profile"""
    profile = InSpecProfile(sample_profile_dir)
    
    assert profile.is_valid
    assert profile.get_name() == 'test-profile'
    assert profile.metadata['title'] == 'Test Profile'


def test_inspec_profile_single_file():
    """Test loading a single Ruby file as profile"""
    # Create temp Ruby file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
        f.write("describe file('/etc/passwd') do\n  it { should exist }\nend")
        temp_path = f.name
    
    try:
        profile = InSpecProfile(temp_path)
        assert profile.is_valid
    finally:
        os.unlink(temp_path)


def test_inspec_profile_not_found():
    """Test handling of missing profile"""
    with pytest.raises(FileNotFoundError):
        InSpecProfile('/nonexistent/profile')


def test_inspec_profile_invalid():
    """Test handling of invalid profile"""
    # Create temp directory without inspec.yml or controls
    temp_dir = tempfile.mkdtemp()
    
    try:
        with pytest.raises(ValueError):
            InSpecProfile(temp_dir)
    finally:
        os.rmdir(temp_dir)


def test_inspec_runner_creation(sample_profile_dir):
    """Test creating an InSpecRunner"""
    profile = InSpecProfile(sample_profile_dir)
    
    # This will fail if InSpec is not installed, but we test object creation
    try:
        runner = InSpecRunner(profile, 'local://')
        assert runner.profile == profile
        assert runner.target == 'local://'
    except RuntimeError as e:
        # InSpec not installed - that's ok for unit test
        if 'InSpec not found' in str(e):
            pytest.skip("InSpec not installed")
        else:
            raise


def test_inspec_runner_target_default(sample_profile_dir):
    """Test default target is local"""
    profile = InSpecProfile(sample_profile_dir)
    
    try:
        runner = InSpecRunner(profile)
        assert runner.target == 'local://'
    except RuntimeError as e:
        if 'InSpec not found' in str(e):
            pytest.skip("InSpec not installed")
        else:
            raise


# Note: Actual execution tests require InSpec to be installed
# These would be integration tests rather than unit tests
