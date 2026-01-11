"""
AuditPolicy Translator - Convert InSpec audit_policy to Ansible

Translates InSpec audit_policy checks to native Ansible PowerShell commands
using the Windows auditpol.exe utility.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

from typing import Dict, Any
from .base import ResourceTranslator, TranslationResult


class AuditPolicyTranslator(ResourceTranslator):
    """
    Translates InSpec audit_policy resource to Ansible win_shell with auditpol.
    
    InSpec Example:
        describe audit_policy do
          its('Credential Validation') { should eq 'Success and Failure' }
          its('Logon') { should eq 'Success and Failure' }
        end
    
    Ansible Output:
        - name: Get audit policy for Credential Validation
          ansible.windows.win_shell: |
            auditpol /get /subcategory:"Credential Validation" | Select-String "Credential Validation"
          register: audit_credential_validation
        
        - name: Validate Credential Validation audit policy
          ansible.builtin.assert:
            that:
              - "'Success and Failure' in audit_credential_validation.stdout"
    """
    
    def can_translate(self, describe: Dict[str, Any]) -> bool:
        """Check if describe block is for audit_policy resource"""
        return describe.get('resource') == 'audit_policy'
    
    def translate(self, control_id: str, describe: Dict[str, Any]) -> TranslationResult:
        """
        Translate audit_policy checks to native Ansible tasks.
        
        Args:
            control_id: InSpec control ID
            describe: Parsed describe block with audit policy expectations
        
        Returns:
            TranslationResult with Ansible tasks using win_shell + auditpol
        """
        result = TranslationResult()
        base_var = self._sanitize_variable_name(f"{control_id}_audit")
        
        # Generate tasks for each audit policy check
        for idx, test in enumerate(describe.get('tests', [])):
            if test['type'] != 'its':
                continue
            
            subcategory = test['property']
            expected_value = test['value']
            negate = test.get('negated', False)
            var_name = f"{base_var}_{idx}"
            
            # Task 1: Query audit policy for this subcategory
            fetch_task = {
                'name': f"Get audit policy for {subcategory}",
                'ansible.windows.win_shell': f'auditpol /get /subcategory:"{subcategory}"',
                'register': var_name,
                'changed_when': False
            }
            result.tasks.append(fetch_task)
            
            # Task 2: Validate the setting
            # auditpol output format: "  Subcategory  Setting"
            # We check if expected value appears in output
            if negate:
                assertion = f"'{expected_value}' not in {var_name}.stdout"
            else:
                assertion = f"'{expected_value}' in {var_name}.stdout"
            
            assert_task = {
                'name': f"Validate {subcategory} audit policy",
                'ansible.builtin.assert': {
                    'that': [assertion],
                    'fail_msg': f"Audit policy for {subcategory} should{' not' if negate else ''} be '{expected_value}'",
                    'success_msg': f"Audit policy for {subcategory} is correct"
                }
            }
            result.tasks.append(assert_task)
        
        return result
