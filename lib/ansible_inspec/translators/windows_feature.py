"""
WindowsFeature Translator - Convert InSpec windows_feature to Ansible

Translates InSpec windows_feature checks to native Ansible 
ansible.windows.win_feature module calls.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

from typing import Dict, Any
from .base import ResourceTranslator, TranslationResult


class WindowsFeatureTranslator(ResourceTranslator):
    """
    Translates InSpec windows_feature resource to Ansible win_feature.
    
    InSpec Example:
        describe windows_feature('Telnet-Client') do
          it { should_not be_installed }
        end
        
        describe windows_feature('Web-Server') do
          it { should be_installed }
        end
    
    Ansible Output:
        - name: Check Windows feature Telnet-Client
          ansible.windows.win_feature:
            name: Telnet-Client
            state: query
          register: feature_telnet_client
        
        - name: Validate Telnet-Client not installed
          ansible.builtin.assert:
            that:
              - feature_telnet_client.installed == false
    """
    
    def can_translate(self, describe: Dict[str, Any]) -> bool:
        """Check if describe block is for windows_feature resource"""
        resource = describe.get('resource', '')
        return resource in ['windows_feature', 'windows_feature_dism']
    
    def translate(self, control_id: str, describe: Dict[str, Any]) -> TranslationResult:
        """
        Translate windows_feature checks to native Ansible tasks.
        
        Args:
            control_id: InSpec control ID
            describe: Parsed describe block with feature expectations
        
        Returns:
            TranslationResult with Ansible tasks using win_feature
        """
        result = TranslationResult()
        var_name = self._sanitize_variable_name(f"{control_id}_feature")
        
        # Extract feature name from argument
        feature_name = describe.get('argument', '')
        if not feature_name:
            result.warnings.append(
                f"windows_feature check in control {control_id} has no feature name"
            )
            result.requires_inspec = True
            return result
        
        # Task 1: Query feature status (don't change state, just check)
        fetch_task = {
            'name': f"Check Windows feature {feature_name}",
            'ansible.windows.win_feature': {
                'name': feature_name,
                'state': 'query'
            },
            'register': var_name
        }
        result.tasks.append(fetch_task)
        
        # Task 2: Build assertions
        assertions = []
        
        for test in describe.get('tests', []):
            if test['type'] == 'it':
                matcher = test['matcher']
                negate = test.get('negated', False)
                
                if matcher == 'be_installed':
                    # Check installation status
                    if negate:
                        assertions.append(f"{var_name}.installed == false")
                    else:
                        assertions.append(f"{var_name}.installed == true")
        
        if assertions:
            # Generate a valid register variable name from control_id
            register_name = re.sub(r'[^a-zA-Z0-9_]', '_', control_id)
            register_name = re.sub(r'_+', '_', register_name).strip('_')
            if register_name and register_name[0].isdigit():
                register_name = 'control_' + register_name
            
            assert_task = {
                'name': f"Validate Windows feature {feature_name}",
                'ignore_errors': True,
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': f"Windows feature check failed for {feature_name}",
                    'success_msg': f"Windows feature check passed for {feature_name}"
                },
                'register': f"{register_name}_result"
            }
            result.tasks.append(assert_task)
        
        return result
