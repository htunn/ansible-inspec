"""
SecurityPolicy Translator - Convert InSpec security_policy to Ansible

Translates InSpec security_policy checks to native Ansible 
ansible.windows.win_security_policy module calls.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

from typing import Dict, Any
from .base import ResourceTranslator, TranslationResult


class SecurityPolicyTranslator(ResourceTranslator):
    """
    Translates InSpec security_policy resource to Ansible win_security_policy.
    
    InSpec Example:
        describe security_policy do
          its('MaximumPasswordAge') { should cmp == 365 }
          its('MinimumPasswordAge') { should be >= 1 }
          its('PasswordHistorySize') { should cmp == 24 }
        end
    
    Ansible Output:
        - name: Get security policy settings
          ansible.windows.win_security_policy:
            section: System Access
          register: security_policy_result
        
        - name: Validate Maximum Password Age
          ansible.builtin.assert:
            that:
              - security_policy_result.MaximumPasswordAge == 365
            fail_msg: "MaximumPasswordAge should be 365, got {{ security_policy_result.MaximumPasswordAge }}"
    """
    
    # Map property names to security policy sections
    SECTION_MAP = {
        'MaximumPasswordAge': 'System Access',
        'MinimumPasswordAge': 'System Access',
        'MinimumPasswordLength': 'System Access',
        'PasswordComplexity': 'System Access',
        'PasswordHistorySize': 'System Access',
        'LockoutBadCount': 'System Access',
        'ResetLockoutCount': 'System Access',
        'LockoutDuration': 'System Access',
        'RequireLogonToChangePassword': 'System Access',
        'ClearTextPassword': 'System Access',
        'LSAAnonymousNameLookup': 'System Access',
        'EnableAdminAccount': 'System Access',
        'EnableGuestAccount': 'System Access',
        # Add more as needed
    }
    
    def can_translate(self, describe: Dict[str, Any]) -> bool:
        """Check if describe block is for security_policy resource"""
        return describe.get('resource') == 'security_policy'
    
    def translate(self, control_id: str, describe: Dict[str, Any]) -> TranslationResult:
        """
        Translate security_policy checks to native Ansible tasks.
        
        Args:
            control_id: InSpec control ID
            describe: Parsed describe block with tests
        
        Returns:
            TranslationResult with Ansible tasks using win_security_policy
        """
        result = TranslationResult()
        var_name = self._sanitize_variable_name(f"{control_id}_security_policy")
        
        # Determine which section(s) to query
        sections = self._determine_sections(describe)
        
        if not sections:
            # No recognized properties - fallback required
            result.warnings.append(
                f"security_policy check in control {control_id} has no recognized properties"
            )
            result.requires_inspec = True
            return result
        
        # Task 1: Get security policy settings
        # Note: win_security_policy returns all settings when no specific key is requested
        fetch_task = {
            'name': f"Get security policy settings for control {control_id}",
            'ansible.windows.win_security_policy': {
                'section': sections[0]  # Use first section (most have same section)
            },
            'register': var_name
        }
        result.tasks.append(fetch_task)
        
        # Task 2: Add assertions for each test
        assertions = []
        for test in describe.get('tests', []):
            if test['type'] == 'its':
                property_name = test['property']
                property_path = f"{var_name}.{property_name}"
                
                # Extract operator and value from the test
                operator = test.get('operator')
                value = test['value']
                
                # If value includes operator (like '== 365'), parse it
                if operator and value.startswith(operator):
                    # Remove operator from value
                    value = value[len(operator):].strip()
                
                assertion = self._convert_matcher_to_assertion(
                    property_path,
                    test['matcher'],
                    value,
                    test.get('negated', False),
                    operator
                )
                assertions.append(assertion)
        
        if assertions:
            assert_task = {
                'name': f"Validate security policy for control {control_id}",
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': f"Security policy check failed for control {control_id}",
                    'success_msg': f"Security policy check passed for control {control_id}"
                }
            }
            result.tasks.append(assert_task)
        
        return result
    
    def _determine_sections(self, describe: Dict[str, Any]) -> list:
        """Determine which security policy sections are needed"""
        sections = set()
        
        for test in describe.get('tests', []):
            if test['type'] == 'its':
                property_name = test['property']
                section = self.SECTION_MAP.get(property_name, 'System Access')
                sections.add(section)
        
        return list(sections)
