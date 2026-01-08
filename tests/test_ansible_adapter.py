"""
Test suite for Ansible adapter

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import pytest
import os
import tempfile
import yaml
from ansible_inspec.ansible_adapter import (
    AnsibleInventory, 
    InventoryHost, 
    AnsibleConnection
)


@pytest.fixture
def sample_inventory_file():
    """Create a sample inventory file for testing"""
    inventory_data = {
        'all': {
            'hosts': {
                'web-01': {
                    'ansible_host': '192.168.1.10',
                    'ansible_user': 'admin',
                    'ansible_port': 22
                },
                'web-02': {
                    'ansible_host': '192.168.1.11',
                    'ansible_user': 'admin'
                }
            },
            'children': {
                'webservers': {
                    'hosts': {
                        'web-01': None,
                        'web-02': None
                    },
                    'vars': {
                        'http_port': 80
                    }
                },
                'databases': {
                    'hosts': {
                        'db-01': {
                            'ansible_host': '192.168.1.20',
                            'ansible_user': 'dbadmin'
                        }
                    }
                }
            },
            'vars': {
                'ansible_connection': 'ssh'
            }
        }
    }
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(inventory_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


def test_inventory_host_creation():
    """Test creating an InventoryHost"""
    host = InventoryHost('test-host', {
        'ansible_host': '192.168.1.100',
        'ansible_user': 'testuser'
    })
    
    assert host.name == 'test-host'
    assert host.ansible_host == '192.168.1.100'
    assert host.ansible_user == 'testuser'
    assert host.ansible_port == 22  # default


def test_inventory_host_connection_uri():
    """Test connection URI generation"""
    # SSH connection
    host = InventoryHost('ssh-host', {
        'ansible_host': '192.168.1.100',
        'ansible_user': 'admin',
        'ansible_port': 2222
    })
    assert host.get_connection_uri() == 'ssh://admin@192.168.1.100:2222'
    
    # Local connection
    local_host = InventoryHost('local', {'ansible_connection': 'local'})
    assert local_host.get_connection_uri() == 'local://'
    
    # Docker connection
    docker_host = InventoryHost('container', {
        'ansible_connection': 'docker',
        'ansible_host': 'my-container'
    })
    assert docker_host.get_connection_uri() == 'docker://my-container'


def test_ansible_inventory_loading(sample_inventory_file):
    """Test loading an Ansible inventory file"""
    inventory = AnsibleInventory(sample_inventory_file)
    
    # Check hosts were loaded
    assert len(inventory.hosts) > 0
    assert 'web-01' in inventory.hosts
    assert 'web-02' in inventory.hosts
    assert 'db-01' in inventory.hosts


def test_ansible_inventory_get_hosts(sample_inventory_file):
    """Test getting hosts from inventory"""
    inventory = AnsibleInventory(sample_inventory_file)
    
    # Get all hosts
    all_hosts = inventory.get_hosts()
    assert len(all_hosts) >= 3
    
    # Get hosts by group
    web_hosts = inventory.get_hosts('webservers')
    assert len(web_hosts) == 2


def test_ansible_inventory_get_host(sample_inventory_file):
    """Test getting a specific host"""
    inventory = AnsibleInventory(sample_inventory_file)
    
    host = inventory.get_host('web-01')
    assert host is not None
    assert host.name == 'web-01'
    assert host.ansible_host == '192.168.1.10'


def test_ansible_inventory_get_groups(sample_inventory_file):
    """Test getting groups"""
    inventory = AnsibleInventory(sample_inventory_file)
    
    groups = inventory.get_groups()
    assert 'all' in groups
    assert 'webservers' in groups
    assert 'databases' in groups


def test_ansible_inventory_file_not_found():
    """Test handling of missing inventory file"""
    with pytest.raises(FileNotFoundError):
        AnsibleInventory('/nonexistent/inventory.yml')


def test_ansible_connection():
    """Test AnsibleConnection"""
    host = InventoryHost('test-host', {
        'ansible_host': '192.168.1.100',
        'ansible_user': 'testuser'
    })
    
    connection = AnsibleConnection(host)
    assert connection.host == host
    assert connection.get_target_uri() == 'ssh://testuser@192.168.1.100:22'
