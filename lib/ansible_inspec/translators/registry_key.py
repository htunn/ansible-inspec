"""
RegistryKey Translator - Convert InSpec registry_key to Ansible

Translates InSpec registry_key checks to native Ansible 
ansible.windows.win_reg_stat module calls.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

from typing import Dict, Any
from .base import ResourceTranslator, TranslationResult


class RegistryKeyTranslator(ResourceTranslator):
    """
    Translates InSpec registry_key resource to Ansible win_reg_stat.
    
    InSpec Example:
        describe registry_key('HKLM\\\\Software\\\\Policies\\\\Microsoft\\\\Windows\\\\System') do
          it { should exist }
          its('EnableSmartScreen') { should eq 1 }
        end
    
    Ansible Output:
        - name: Check registry key exists
          ansible.windows.win_reg_stat:
            path: HKLM:\\Software\\Policies\\Microsoft\\Windows\\System
          register: registry_result
        
        - name: Validate registry key
          ansible.builtin.assert:
            that:
              - registry_result.exists
              - registry_result.properties.EnableSmartScreen == 1
    """
    
    def can_translate(self, describe: Dict[str, Any]) -> bool:
        """Check if describe block is for registry_key resource"""
        return describe.get('resource') == 'registry_key'
    
    def translate(self, control_id: str, describe: Dict[str, Any]) -> TranslationResult:
        """
        Translate registry_key checks to native Ansible tasks.
        
        Args:
            control_id: InSpec control ID
            describe: Parsed describe block with registry path and expectations
        
        Returns:
            TranslationResult with Ansible tasks using win_reg_stat
        """
        result = TranslationResult()
        var_name = self._sanitize_variable_name(f"{control_id}_registry")
        
        # Extract registry path from argument
        registry_path = describe.get('argument', '')
        if not registry_path:
            result.warnings.append(
                f"registry_key in control {control_id} has no path specified"
            )
            result.requires_inspec = True
            return result
        
        # Convert InSpec path format to PowerShell format
        # InSpec: HKLM\Software\... → PowerShell: HKLM:\Software\...
        ps_path = self._convert_registry_path(registry_path)
        
        # Task 1: Get registry key information
        fetch_task = {
            'name': f"Get registry key for control {control_id}",
            'ansible.windows.win_reg_stat': {
                'path': ps_path
            },
            'register': var_name
        }
        result.tasks.append(fetch_task)
        
        # Task 2: Build assertions
        assertions = []
        
        for test in describe.get('tests', []):
            if test['type'] == 'it':
                # Handle 'it { should exist }' checks
                matcher = test['matcher']
                negate = test.get('negated', False)
                
                if matcher == 'exist':
                    if negate:
                        assertions.append(f"not {var_name}.exists")
                    else:
                        assertions.append(f"{var_name}.exists")
            
            elif test['type'] == 'its':
                # Handle property checks: its('PropertyName') { should eq value }
                property_name = test['property']
                property_path = f"{var_name}.properties.{property_name}"
                
                assertion = self._convert_matcher_to_assertion(
                    property_path,
                    test['matcher'],
                    test['value'],
                    test.get('negated', False)
                )
                assertions.append(assertion)
        
        if assertions:
            assert_task = {
                'name': f"Validate registry key for control {control_id}",
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': f"Registry key check failed for control {control_id}",
                    'success_msg': f"Registry key check passed for control {control_id}"
                }
            }
            result.tasks.append(assert_task)
        
        return result
    
    def _convert_registry_path(self, inspec_path: str) -> str:
        """
        Convert InSpec registry path to PowerShell format.
        
        Args:
            inspec_path: InSpec path like "HKLM\\Software\\..."
        
        Returns:
            PowerShell path like "HKLM:\\Software\\..."
        
        Examples:
            >>> _convert_registry_path("HKLM\\Software\\Microsoft")
            "HKLM:\\Software\\Microsoft"
            
            >>> _convert_registry_path("HKEY_LOCAL_MACHINE\\System")
            "HKLM:\\System"
        """
        # Normalize path separators
        path = inspec_path.replace('/', '\\')
        
        # Convert long hive names to short names
        hive_map = {
            'HKEY_LOCAL_MACHINE': 'HKLM',
            'HKEY_CURRENT_USER': 'HKCU',
            'HKEY_CLASSES_ROOT': 'HKCR',
            'HKEY_USERS': 'HKU',
            'HKEY_CURRENT_CONFIG': 'HKCC'
        }
        
        for long_name, short_name in hive_map.items():
            if path.startswith(long_name):
                path = path.replace(long_name, short_name, 1)
                break
        
        # Add colon after hive if not present
        # HKLM\... → HKLM:\...
        parts = path.split('\\', 1)
        if len(parts) == 2 and ':' not in parts[0]:
            path = f"{parts[0]}:\\{parts[1]}"
        elif len(parts) == 1 and ':' not in parts[0]:
            path = f"{parts[0]}:"
        
        return path
