"""
Custom Resource Dynamic Translator - Auto-translate custom InSpec resources

Analyzes custom InSpec resources and dynamically maps them to native Ansible
modules based on the resource's implementation patterns. This eliminates the
need for InSpec on target systems even when custom resources are used.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import re
from typing import Dict, Any, List, Optional
from .base import ResourceTranslator, TranslationResult


class CustomResourceTranslator(ResourceTranslator):
    """
    Dynamically translates custom InSpec resources to native Ansible.
    
    Analyzes the custom resource Ruby code to understand its behavior
    and maps to appropriate Ansible modules.
    """
    
    def __init__(self, custom_resources: Dict[str, Dict[str, Any]]):
        """
        Initialize with parsed custom resources.
        
        Args:
            custom_resources: Dict mapping resource names to their metadata
                              (from CustomResourceParser)
        """
        self.custom_resources = custom_resources
        self.pattern_matchers = {
            'dism_feature': self._translate_dism_feature,
            'systeminfo_domain': self._translate_systeminfo_domain,
            'powershell_command': self._translate_powershell_command,
            'wmi_query': self._translate_wmi_query,
            'registry_check': self._translate_registry_check,
        }
    
    def can_translate(self, describe: Dict[str, Any]) -> bool:
        """Check if describe block uses a known custom resource"""
        resource = describe.get('resource', '')
        return resource in self.custom_resources
    
    def translate(self, control_id: str, describe: Dict[str, Any]) -> TranslationResult:
        """
        Dynamically translate custom resource to native Ansible.
        
        Analyzes the resource implementation and maps to appropriate modules.
        """
        result = TranslationResult()
        resource_name = describe.get('resource', '')
        
        if resource_name not in self.custom_resources:
            result.warnings.append(f"Unknown custom resource: {resource_name}")
            result.requires_inspec = True
            return result
        
        resource_info = self.custom_resources[resource_name]
        resource_content = resource_info.get('content', '')
        
        # Detect resource pattern and translate accordingly
        pattern_type = self._detect_pattern(resource_content, resource_name)
        
        if pattern_type and pattern_type in self.pattern_matchers:
            translator_func = self.pattern_matchers[pattern_type]
            return translator_func(control_id, describe, resource_info)
        else:
            # Generic fallback - try to extract command and translate
            return self._translate_generic_command(control_id, describe, resource_info)
    
    def _detect_pattern(self, content: str, resource_name: str) -> Optional[str]:
        """Detect what type of resource pattern this is"""
        
        # Check for DISM feature queries
        if 'dism' in content.lower() and 'featurename' in content.lower():
            return 'dism_feature'
        
        # Check for systeminfo domain/workgroup checks
        if 'systeminfo' in content.lower() and 'domain' in content.lower():
            return 'systeminfo_domain'
        
        # Check for PowerShell commands
        if 'powershell' in content.lower() or 'Get-' in content:
            return 'powershell_command'
        
        # Check for WMI queries
        if 'win32_' in content.lower() or 'wmi' in content.lower():
            return 'wmi_query'
        
        # Check for registry operations
        if 'registry' in content.lower() or 'hklm' in content.lower():
            return 'registry_check'
        
        return None
    
    def _translate_dism_feature(
        self,
        control_id: str,
        describe: Dict[str, Any],
        resource_info: Dict[str, Any]
    ) -> TranslationResult:
        """
        Translate DISM-based Windows feature checks to win_feature.
        
        Handles custom resources like win_feature_dism that use DISM.exe
        """
        result = TranslationResult()
        var_name = self._sanitize_variable_name(f"{control_id}_feature")
        
        # Extract feature name from argument
        feature_name = describe.get('argument', '')
        if not feature_name:
            result.warnings.append("DISM feature check has no feature name")
            result.requires_inspec = True
            return result
        
        # Use native win_feature module instead of DISM
        fetch_task = {
            'name': f"Check Windows feature {feature_name} (DISM)",
            'ansible.windows.win_feature': {
                'name': feature_name,
                'state': 'query'
            },
            'register': var_name
        }
        result.tasks.append(fetch_task)
        
        # Build assertions from tests
        assertions = []
        for test in describe.get('tests', []):
            if test['type'] == 'its':
                prop = test['property']
                
                if prop == 'installed':
                    # Map installed? to win_feature.installed
                    matcher = test.get('matcher', 'eq')
                    value = test.get('value', 'true')
                    
                    if matcher in ['eq', 'cmp']:
                        assertions.append(f"{var_name}.installed == {value}")
                    elif matcher == 'be':
                        assertions.append(f"{var_name}.installed == {value}")
                
                elif prop == 'exist':
                    # Map exist? to feature being found
                    value = test.get('value', 'true')
                    assertions.append(f"{var_name}.feature_result | length > 0")
            
            elif test['type'] == 'it':
                matcher = test['matcher']
                negate = test.get('negated', False)
                
                if matcher == 'be_installed':
                    if negate:
                        assertions.append(f"{var_name}.installed == false")
                    else:
                        assertions.append(f"{var_name}.installed == true")
        
        if assertions:
            assert_task = {
                'name': f"Validate Windows feature {feature_name}",
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': f"Feature check failed for {feature_name}",
                    'success_msg': f"Feature check passed for {feature_name}"
                }
            }
            result.tasks.append(assert_task)
        
        return result
    
    def _translate_systeminfo_domain(
        self,
        control_id: str,
        describe: Dict[str, Any],
        resource_info: Dict[str, Any]
    ) -> TranslationResult:
        """
        Translate systeminfo domain/workgroup checks.
        
        Handles resources like is_workgrp that check domain membership.
        """
        result = TranslationResult()
        var_name = self._sanitize_variable_name(f"{control_id}_domain")
        
        # Use win_domain_membership facts
        fetch_task = {
            'name': "Check domain membership status",
            'ansible.windows.win_shell': 'systeminfo | findstr /B "Domain"',
            'register': var_name,
            'changed_when': False
        }
        result.tasks.append(fetch_task)
        
        # Parse the output to check for WORKGROUP
        assertions = []
        for test in describe.get('tests', []):
            if test['type'] == 'its':
                prop = test['property']
                
                if prop in ['exist', 'wkgrp']:
                    # Check if machine is in workgroup
                    value = test.get('value', 'true')
                    matcher = test.get('matcher', 'eq')
                    
                    if matcher in ['eq', 'cmp']:
                        if value in ['true', True]:
                            # Should be in workgroup
                            assertions.append(f"'WORKGROUP' in {var_name}.stdout")
                        else:
                            # Should NOT be in workgroup (domain joined)
                            assertions.append(f"'WORKGROUP' not in {var_name}.stdout")
        
        if assertions:
            assert_task = {
                'name': "Validate domain membership",
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': "Domain membership check failed",
                    'success_msg': "Domain membership check passed"
                }
            }
            result.tasks.append(assert_task)
        
        return result
    
    def _translate_powershell_command(
        self,
        control_id: str,
        describe: Dict[str, Any],
        resource_info: Dict[str, Any]
    ) -> TranslationResult:
        """Translate PowerShell-based custom resources"""
        result = TranslationResult()
        var_name = self._sanitize_variable_name(f"{control_id}_ps")
        
        # Extract PowerShell command from resource content
        content = resource_info.get('content', '')
        ps_cmd_match = re.search(r'powershell.*?["\'](.+?)["\']', content, re.IGNORECASE)
        
        if ps_cmd_match:
            ps_command = ps_cmd_match.group(1)
            
            fetch_task = {
                'name': f"Execute PowerShell check",
                'ansible.windows.win_shell': ps_command,
                'register': var_name,
                'changed_when': False
            }
            result.tasks.append(fetch_task)
            
            # Add generic validation
            assertions = [f"{var_name}.rc == 0"]
            
            assert_task = {
                'name': "Validate PowerShell check",
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': "PowerShell check failed",
                    'success_msg': "PowerShell check passed"
                }
            }
            result.tasks.append(assert_task)
        else:
            result.warnings.append("Could not extract PowerShell command")
            result.requires_inspec = True
        
        return result
    
    def _translate_wmi_query(
        self,
        control_id: str,
        describe: Dict[str, Any],
        resource_info: Dict[str, Any]
    ) -> TranslationResult:
        """Translate WMI-based custom resources"""
        result = TranslationResult()
        var_name = self._sanitize_variable_name(f"{control_id}_wmi")
        
        # Extract WMI class from resource content
        content = resource_info.get('content', '')
        wmi_class_match = re.search(r'Win32_(\w+)', content, re.IGNORECASE)
        
        if wmi_class_match:
            wmi_class = f"Win32_{wmi_class_match.group(1)}"
            
            fetch_task = {
                'name': f"Query WMI {wmi_class}",
                'ansible.windows.win_shell': f"Get-WmiObject -Class {wmi_class} | ConvertTo-Json",
                'register': var_name,
                'changed_when': False
            }
            result.tasks.append(fetch_task)
            
            # Add parsing and validation
            assertions = [f"{var_name}.rc == 0"]
            
            assert_task = {
                'name': f"Validate {wmi_class} query",
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': f"WMI query failed for {wmi_class}",
                    'success_msg': f"WMI query passed for {wmi_class}"
                }
            }
            result.tasks.append(assert_task)
        else:
            result.warnings.append("Could not extract WMI class")
            result.requires_inspec = True
        
        return result
    
    def _translate_registry_check(
        self,
        control_id: str,
        describe: Dict[str, Any],
        resource_info: Dict[str, Any]
    ) -> TranslationResult:
        """Translate registry-based custom resources"""
        result = TranslationResult()
        var_name = self._sanitize_variable_name(f"{control_id}_reg")
        
        # Use win_reg_stat or win_shell with reg query
        # This is a simplified version - could be enhanced
        
        fetch_task = {
            'name': "Check registry value",
            'ansible.windows.win_shell': 'echo "Registry check needed"',
            'register': var_name,
            'changed_when': False
        }
        result.tasks.append(fetch_task)
        
        result.warnings.append("Registry custom resource needs manual review")
        
        return result
    
    def _translate_generic_command(
        self,
        control_id: str,
        describe: Dict[str, Any],
        resource_info: Dict[str, Any]
    ) -> TranslationResult:
        """
        Generic fallback for custom resources we can't specifically translate.
        
        Attempts to extract the command being executed and run it via win_shell.
        Better than requiring InSpec, but not as clean as specific translators.
        """
        result = TranslationResult()
        var_name = self._sanitize_variable_name(f"{control_id}_custom")
        
        # Try to extract command patterns
        content = resource_info.get('content', '')
        
        # Look for command execution patterns
        cmd_patterns = [
            r'inspec\.command\(["\'](.+?)["\']\)',
            r'command\(["\'](.+?)["\']\)',
            r'cmd\s*=\s*["\'](.+?)["\']',
        ]
        
        extracted_cmd = None
        for pattern in cmd_patterns:
            match = re.search(pattern, content)
            if match:
                extracted_cmd = match.group(1)
                break
        
        if extracted_cmd:
            # Determine if Windows or Linux command
            is_windows_cmd = any(x in extracted_cmd.lower() for x in ['systeminfo', 'findstr', 'dism', 'powershell'])
            
            if is_windows_cmd:
                fetch_task = {
                    'name': f"Execute custom check: {describe.get('resource')}",
                    'ansible.windows.win_shell': extracted_cmd,
                    'register': var_name,
                    'changed_when': False
                }
            else:
                fetch_task = {
                    'name': f"Execute custom check: {describe.get('resource')}",
                    'ansible.builtin.shell': extracted_cmd,
                    'register': var_name,
                    'changed_when': False
                }
            
            result.tasks.append(fetch_task)
            
            # Basic validation
            assertions = [f"{var_name}.rc == 0"]
            
            assert_task = {
                'name': f"Validate {describe.get('resource')} check",
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': f"Custom resource check failed",
                    'success_msg': f"Custom resource check passed"
                }
            }
            result.tasks.append(assert_task)
            
            result.warnings.append(
                f"Custom resource '{describe.get('resource')}' translated to generic command execution. "
                "Consider creating a specific translator for better results."
            )
        else:
            # Could not extract - this will require InSpec
            result.warnings.append(
                f"Could not translate custom resource '{describe.get('resource')}'. "
                "Falling back to InSpec wrapper."
            )
            result.requires_inspec = True
        
        return result
