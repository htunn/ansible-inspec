"""
InSpec adapter module for ansible-inspec

This module provides integration with InSpec testing framework.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0

Note: This module integrates with InSpec, which is licensed under Apache-2.0.
Per Apache-2.0 section 4(b), modifications to InSpec components will be
documented in version control history.
"""

import os
import subprocess
import json
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

__all__ = ['InSpecProfile', 'InSpecRunner', 'InSpecResult']


@dataclass
class InSpecResult:
    """Represents the result of an InSpec test execution"""
    profile: str
    target: str
    passed: int
    failed: int
    skipped: int
    total: int
    controls: List[Dict[str, Any]]
    duration: float
    
    @property
    def success(self) -> bool:
        """Check if all tests passed"""
        return self.failed == 0
    
    def summary(self) -> str:
        """Get a summary string"""
        status = "PASSED" if self.success else "FAILED"
        return f"{status}: {self.passed}/{self.total} tests passed"


class InSpecProfile:
    """
    Adapter for InSpec profiles
    
    This class provides an interface to load and execute InSpec compliance
    profiles.
    """
    
    def __init__(self, profile_path: str, is_supermarket: bool = False):
        """
        Initialize the InSpec profile adapter
        
        Args:
            profile_path: Path to InSpec profile directory or file, or supermarket:// URL
            is_supermarket: Whether this is a Chef Supermarket profile
        """
        self.is_supermarket = is_supermarket
        if is_supermarket:
            # Store supermarket URL as-is, InSpec handles it natively
            self.profile_path = profile_path if profile_path.startswith('supermarket://') else f'supermarket://{profile_path}'
        else:
            self.profile_path = os.path.abspath(profile_path)
        self.metadata: Dict[str, Any] = {}
        self.is_valid = False
        self.load()
    
    def load(self):
        """Load the InSpec profile metadata"""
        # Handle Chef Supermarket profiles
        if self.is_supermarket:
            # Supermarket profiles are validated at runtime by InSpec
            self.is_valid = True
            # Extract profile name from supermarket URL
            profile_name = self.profile_path.replace('supermarket://', '').split('/')[-1]
            self.metadata = {'name': profile_name, 'source': 'Chef Supermarket'}
            return
        
        if not os.path.exists(self.profile_path):
            raise FileNotFoundError(f"Profile not found: {self.profile_path}")
        
        # Check if it's a directory with inspec.yml
        if os.path.isdir(self.profile_path):
            inspec_yml = os.path.join(self.profile_path, 'inspec.yml')
            if os.path.exists(inspec_yml):
                with open(inspec_yml, 'r') as f:
                    self.metadata = yaml.safe_load(f) or {}
                self.is_valid = True
            else:
                # Check for controls directory
                controls_dir = os.path.join(self.profile_path, 'controls')
                if os.path.exists(controls_dir):
                    self.is_valid = True
                    self.metadata = {'name': os.path.basename(self.profile_path)}
        elif os.path.isfile(self.profile_path):
            # Single Ruby file
            self.is_valid = self.profile_path.endswith('.rb')
            self.metadata = {'name': os.path.basename(self.profile_path)}
        
        if not self.is_valid:
            raise ValueError(f"Invalid InSpec profile: {self.profile_path}")
    
    def validate(self) -> bool:
        """Validate profile syntax and structure"""
        if not self.is_valid:
            return False
        
        # Check if inspec command is available
        try:
            subprocess.run(
                ['inspec', 'version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # InSpec not installed, but profile structure is valid
            return True
        
        # Use InSpec to validate
        try:
            result = subprocess.run(
                ['inspec', 'check', self.profile_path],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_name(self) -> str:
        """Get profile name"""
        return self.metadata.get('name', 'unknown')
    
    @classmethod
    def from_supermarket(cls, profile_name: str) -> 'InSpecProfile':
        """
        Create an InSpec profile from Chef Supermarket
        
        Args:
            profile_name: Name of the profile (e.g., 'dev-sec/linux-baseline')
            
        Returns:
            InSpecProfile instance configured for Supermarket
            
        Examples:
            >>> profile = InSpecProfile.from_supermarket('dev-sec/linux-baseline')
            >>> profile = InSpecProfile.from_supermarket('cis-docker-benchmark')
        """
        return cls(profile_name, is_supermarket=True)
    
    def __repr__(self):
        return f"InSpecProfile({self.get_name()}, {self.profile_path})"


class InSpecRunner:
    """
    Adapter for InSpec test execution
    
    This class provides an interface to execute InSpec tests against
    target systems.
    """
    
    def __init__(self, profile: InSpecProfile, target: Optional[str] = None):
        """
        Initialize the InSpec runner
        
        Args:
            profile: InSpec profile to execute
            target: Target to test (uri format), None for local
        """
        self.profile = profile
        self.target = target or 'local://'
        self.results: Optional[InSpecResult] = None
        self._check_inspec_available()
    
    def _check_inspec_available(self):
        """Check if InSpec is installed"""
        try:
            subprocess.run(
                ['inspec', 'version'],
                capture_output=True,
                check=True
            )
        except FileNotFoundError:
            raise RuntimeError(
                "InSpec not found. Please install InSpec:\n"
                "  brew install chef/chef/inspec  # macOS\n"
                "  gem install inspec-bin         # Ruby\n"
                "Visit: https://docs.chef.io/inspec/install/"
            )
    
    def execute(self, reporter: str = 'json') -> InSpecResult:
        """
        Execute InSpec tests
        
        Args:
            reporter: Output format (json, cli, html, etc.)
            
        Returns:
            InSpecResult object
        """
        # Build InSpec command
        cmd = ['inspec', 'exec', self.profile.profile_path]
        
        # Add target if not local
        if self.target and self.target != 'local://':
            cmd.extend(['-t', self.target])
        
        # Add reporter
        cmd.extend(['--reporter', reporter])
        
        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse results
            if reporter == 'json':
                self.results = self._parse_json_output(result.stdout)
            else:
                # For non-JSON reporters, create basic result
                self.results = InSpecResult(
                    profile=self.profile.get_name(),
                    target=self.target,
                    passed=0,
                    failed=0,
                    skipped=0,
                    total=0,
                    controls=[],
                    duration=0.0
                )
                # Store raw output
                self.results.raw_output = result.stdout
            
            return self.results
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("InSpec execution timed out (5 minutes)")
        except Exception as e:
            raise RuntimeError(f"InSpec execution failed: {e}")
    
    def _parse_json_output(self, output: str) -> InSpecResult:
        """
        Parse JSON output from InSpec
        
        Args:
            output: JSON string from InSpec
            
        Returns:
            InSpecResult object
        """
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            # Return empty result if parsing fails
            return InSpecResult(
                profile=self.profile.get_name(),
                target=self.target,
                passed=0,
                failed=0,
                skipped=0,
                total=0,
                controls=[],
                duration=0.0
            )
        
        # Extract statistics
        profiles = data.get('profiles', [])
        if not profiles:
            return InSpecResult(
                profile=self.profile.get_name(),
                target=self.target,
                passed=0,
                failed=0,
                skipped=0,
                total=0,
                controls=[],
                duration=0.0
            )
        
        profile_data = profiles[0]
        controls = profile_data.get('controls', [])
        
        # Count results
        passed = 0
        failed = 0
        skipped = 0
        
        for control in controls:
            results = control.get('results', [])
            for result in results:
                status = result.get('status')
                if status == 'passed':
                    passed += 1
                elif status == 'failed':
                    failed += 1
                elif status == 'skipped':
                    skipped += 1
        
        total = passed + failed + skipped
        duration = data.get('statistics', {}).get('duration', 0.0)
        
        return InSpecResult(
            profile=profile_data.get('name', self.profile.get_name()),
            target=self.target,
            passed=passed,
            failed=failed,
            skipped=skipped,
            total=total,
            controls=controls,
            duration=duration
        )
    
    def get_results(self) -> Optional[InSpecResult]:
        """Get test execution results"""
        return self.results
