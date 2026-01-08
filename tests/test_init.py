"""
Example test showing basic usage of ansible-inspec

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import pytest
from ansible_inspec import __version__, UPSTREAM_PROJECTS


def test_version_format():
    """Test that version follows semantic versioning"""
    parts = __version__.split('.')
    assert len(parts) >= 2, "Version should have at least major.minor"


def test_upstream_projects_defined():
    """Test that upstream project information is available"""
    assert 'ansible' in UPSTREAM_PROJECTS
    assert 'inspec' in UPSTREAM_PROJECTS
    
    ansible_info = UPSTREAM_PROJECTS['ansible']
    assert ansible_info['license'] == 'GPL-3.0'
    assert 'url' in ansible_info
    
    inspec_info = UPSTREAM_PROJECTS['inspec']
    assert inspec_info['license'] == 'Apache-2.0'
    assert 'url' in inspec_info


def test_license_compatibility():
    """
    Test that license information is properly documented
    This is important for legal compliance
    """
    # Ansible uses GPL-3.0
    assert UPSTREAM_PROJECTS['ansible']['license'] == 'GPL-3.0'
    
    # InSpec uses Apache-2.0
    assert UPSTREAM_PROJECTS['inspec']['license'] == 'Apache-2.0'
    
    # Combined work must be GPL-3.0 (more restrictive)
    # This is verified by the LICENSE file
