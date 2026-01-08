"""
Ansible adapter module for ansible-inspec

This module provides integration with Ansible inventory and connection systems.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0

Note: This module integrates with Ansible, which is licensed under GPL-3.0
"""

import os
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path

__all__ = ['AnsibleInventory', 'AnsibleConnection', 'InventoryHost']


class InventoryHost:
    """Represents a host from Ansible inventory"""
    
    def __init__(self, name: str, host_vars: Optional[Dict[str, Any]] = None):
        """
        Initialize an inventory host
        
        Args:
            name: Host name
            host_vars: Host-specific variables
        """
        self.name = name
        self.vars = host_vars or {}
        self.ansible_host = self.vars.get('ansible_host', name)
        self.ansible_port = self.vars.get('ansible_port', 22)
        self.ansible_user = self.vars.get('ansible_user', 'root')
        self.ansible_connection = self.vars.get('ansible_connection', 'ssh')
    
    def get_connection_uri(self) -> str:
        """
        Get connection URI for this host
        
        Returns:
            Connection URI string (e.g., 'ssh://user@host:port')
        """
        if self.ansible_connection == 'local':
            return 'local://'
        elif self.ansible_connection == 'docker':
            return f'docker://{self.ansible_host}'
        elif self.ansible_connection == 'winrm':
            return f'winrm://{self.ansible_user}@{self.ansible_host}:{self.ansible_port}'
        else:  # ssh or default
            return f'ssh://{self.ansible_user}@{self.ansible_host}:{self.ansible_port}'
    
    def __repr__(self):
        return f"InventoryHost({self.name}, {self.ansible_host})"


class AnsibleInventory:
    """
    Adapter for Ansible inventory systems
    
    This class provides an interface to read and parse Ansible inventory
    files and integrate them with InSpec testing.
    """
    
    def __init__(self, inventory_path: str):
        """
        Initialize the Ansible inventory adapter
        
        Args:
            inventory_path: Path to Ansible inventory file
        """
        self.inventory_path = inventory_path
        self.hosts: Dict[str, InventoryHost] = {}
        self.groups: Dict[str, List[str]] = {}
        self.group_vars: Dict[str, Dict[str, Any]] = {}
        self._parse_inventory()
    
    def _parse_inventory(self):
        """Parse the inventory file"""
        if not os.path.exists(self.inventory_path):
            raise FileNotFoundError(f"Inventory file not found: {self.inventory_path}")
        
        with open(self.inventory_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return
        
        # Parse the inventory structure
        self._parse_group(data.get('all', {}), 'all')
    
    def _parse_group(self, group_data: Dict[str, Any], group_name: str):
        """
        Recursively parse a group and its children
        
        Args:
            group_data: Group data dictionary
            group_name: Name of the group
        """
        # Store group variables
        if 'vars' in group_data:
            self.group_vars[group_name] = group_data['vars']
        
        # Parse hosts in this group
        if 'hosts' in group_data:
            if group_name not in self.groups:
                self.groups[group_name] = []
            
            for host_name, host_vars in group_data['hosts'].items():
                # Check if host already exists
                if host_name in self.hosts:
                    # Host already exists, just add to this group
                    if host_name not in self.groups[group_name]:
                        self.groups[group_name].append(host_name)
                    # Update vars if new ones provided
                    if host_vars:
                        self.hosts[host_name].vars.update(host_vars)
                else:
                    # Merge group vars with host vars
                    merged_vars = {}
                    if group_name in self.group_vars:
                        merged_vars.update(self.group_vars[group_name])
                    if host_vars:
                        merged_vars.update(host_vars)
                    
                    # Create host object
                    host = InventoryHost(host_name, merged_vars)
                    self.hosts[host_name] = host
                    self.groups[group_name].append(host_name)
        
        # Parse child groups
        if 'children' in group_data:
            for child_name, child_data in group_data['children'].items():
                self._parse_group(child_data or {}, child_name)
    
    def get_hosts(self, group: Optional[str] = None) -> List[InventoryHost]:
        """
        Get list of hosts from inventory
        
        Args:
            group: Optional group name to filter hosts
            
        Returns:
            List of InventoryHost objects
        """
        if group:
            if group not in self.groups:
                return []
            host_names = self.groups[group]
            return [self.hosts[name] for name in host_names if name in self.hosts]
        
        return list(self.hosts.values())
    
    def get_host(self, name: str) -> Optional[InventoryHost]:
        """
        Get a specific host by name
        
        Args:
            name: Host name
            
        Returns:
            InventoryHost object or None
        """
        return self.hosts.get(name)
    
    def get_groups(self) -> List[str]:
        """Get list of all groups"""
        return list(self.groups.keys())


class AnsibleConnection:
    """
    Adapter for Ansible connection systems
    
    This class provides an interface to use Ansible's connection plugins
    for executing InSpec tests on remote systems.
    """
    
    def __init__(self, host: InventoryHost):
        """
        Initialize the Ansible connection adapter
        
        Args:
            host: InventoryHost object with connection details
        """
        self.host = host
        self.connection_uri = host.get_connection_uri()
    
    def get_target_uri(self) -> str:
        """
        Get the target URI for InSpec
        
        Returns:
            Target URI string
        """
        return self.connection_uri
    
    def __repr__(self):
        return f"AnsibleConnection({self.host.name}, {self.connection_uri})"
