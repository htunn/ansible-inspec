"""
Test suite for core functionality

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import pytest
import os
import tempfile
import yaml
from ansible_inspec.core import (
    Config,
    Runner,
    ExecutionConfig,
    ExecutionResult
)


def test_config_creation():
    """Test creating a Config object"""
    config = Config()
    
    assert config.get('reporter') == 'cli'
    assert config.get('sudo') is False


def test_config_get_set():
    """Test getting and setting config values"""
    config = Config()
    
    config.set('custom_key', 'custom_value')
    assert config.get('custom_key') == 'custom_value'
    assert config.get('nonexistent', 'default') == 'default'


def test_execution_config_creation():
    """Test creating ExecutionConfig"""
    exec_config = ExecutionConfig(
        profile_path='/path/to/profile',
        inventory_path='/path/to/inventory.yml'
    )
    
    assert exec_config.profile_path == '/path/to/profile'
    assert exec_config.inventory_path == '/path/to/inventory.yml'
    assert exec_config.reporter == 'cli'  # default


def test_execution_result_creation():
    """Test creating ExecutionResult"""
    result = ExecutionResult(
        total_hosts=5,
        successful_hosts=3,
        failed_hosts=2
    )
    
    assert result.total_hosts == 5
    assert result.successful_hosts == 3
    assert result.failed_hosts == 2
    assert result.success is False  # Has failures


def test_execution_result_success():
    """Test successful execution result"""
    result = ExecutionResult(
        total_hosts=5,
        successful_hosts=5,
        failed_hosts=0
    )
    
    assert result.success is True
    assert 'SUCCESS' in result.summary()


def test_runner_creation():
    """Test creating a Runner"""
    runner = Runner()
    assert runner.config is not None


def test_runner_with_config():
    """Test Runner with custom config"""
    config = Config()
    config.set('custom', 'value')
    
    runner = Runner(config)
    assert runner.config.get('custom') == 'value'


# Integration-style tests would require actual profile and inventory files
# These are tested in the integration test suite
