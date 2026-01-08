"""
Core functionality for ansible-inspec

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from ansible_inspec.ansible_adapter import AnsibleInventory, InventoryHost
from ansible_inspec.inspec_adapter import InSpecProfile, InSpecRunner, InSpecResult


@dataclass
class ExecutionConfig:
    """Configuration for ansible-inspec execution"""
    profile_path: str
    inventory_path: Optional[str] = None
    target: Optional[str] = None
    group: Optional[str] = None
    host: Optional[str] = None
    reporter: str = 'cli'
    sudo: bool = False
    parallel: bool = False
    max_workers: int = 5
    

@dataclass  
class ExecutionResult:
    """Results from ansible-inspec execution"""
    total_hosts: int
    successful_hosts: int
    failed_hosts: int
    host_results: Dict[str, InSpecResult] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        """Check if all hosts passed"""
        return self.failed_hosts == 0 and len(self.errors) == 0
    
    def summary(self) -> str:
        """Get execution summary"""
        status = "SUCCESS" if self.success else "FAILED"
        return f"{status}: {self.successful_hosts}/{self.total_hosts} hosts passed"


class Config:
    """Configuration management for ansible-inspec"""
    
    def __init__(self):
        self.settings: Dict[str, Any] = {
            'reporter': 'cli',
            'sudo': False,
            'parallel': False,
            'max_workers': 5,
        }
    
    def load_from_file(self, config_path: str):
        """Load configuration from file"""
        import yaml
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f) or {}
        
        self.settings.update(file_config)
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.settings[key] = value


class Runner:
    """Main execution engine for ansible-inspec"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
    
    def run(self, execution_config: ExecutionConfig) -> ExecutionResult:
        """
        Run InSpec profile against targets
        
        Args:
            execution_config: Configuration for this execution
            
        Returns:
            ExecutionResult with test results
        """
        # Load InSpec profile
        profile = InSpecProfile(execution_config.profile_path)
        
        # Determine targets
        targets = self._get_targets(execution_config)
        
        if not targets:
            raise ValueError("No targets specified. Provide inventory, target, or run locally.")
        
        # Execute tests against targets
        result = ExecutionResult(
            total_hosts=len(targets),
            successful_hosts=0,
            failed_hosts=0
        )
        
        for target in targets:
            try:
                # Run InSpec against this target
                runner = InSpecRunner(profile, target.get('uri'))
                test_result = runner.execute(reporter=execution_config.reporter)
                
                # Store result
                host_name = target.get('name', target.get('uri'))
                result.host_results[host_name] = test_result
                
                if test_result.success:
                    result.successful_hosts += 1
                else:
                    result.failed_hosts += 1
                    
            except Exception as e:
                host_name = target.get('name', target.get('uri'))
                result.errors[host_name] = str(e)
                result.failed_hosts += 1
        
        return result
    
    def _get_targets(self, config: ExecutionConfig) -> List[Dict[str, str]]:
        """
        Determine targets from configuration
        
        Args:
            config: Execution configuration
            
        Returns:
            List of target dictionaries with 'name' and 'uri'
        """
        targets = []
        
        # Option 1: Ansible inventory
        if config.inventory_path:
            inventory = AnsibleInventory(config.inventory_path)
            
            # Filter by group or host if specified
            if config.host:
                host = inventory.get_host(config.host)
                if host:
                    targets.append({
                        'name': host.name,
                        'uri': host.get_connection_uri()
                    })
            elif config.group:
                hosts = inventory.get_hosts(config.group)
                for host in hosts:
                    targets.append({
                        'name': host.name,
                        'uri': host.get_connection_uri()
                    })
            else:
                # All hosts
                hosts = inventory.get_hosts()
                for host in hosts:
                    targets.append({
                        'name': host.name,
                        'uri': host.get_connection_uri()
                    })
        
        # Option 2: Direct target URI
        elif config.target:
            targets.append({
                'name': config.target,
                'uri': config.target
            })
        
        # Option 3: Local execution
        else:
            targets.append({
                'name': 'localhost',
                'uri': 'local://'
            })
        
        return targets
    
    def validate_profile(self, profile_path: str) -> bool:
        """
        Validate an InSpec profile
        
        Args:
            profile_path: Path to profile
            
        Returns:
            True if valid
        """
        try:
            profile = InSpecProfile(profile_path)
            return profile.validate()
        except Exception:
            return False


__all__ = ['Config', 'Runner', 'ExecutionConfig', 'ExecutionResult']
