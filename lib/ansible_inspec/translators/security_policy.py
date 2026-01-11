"""
SecurityPolicy Translator - Convert InSpec security_policy to Ansible

Translates InSpec security_policy checks to native Ansible using secedit.
Since ansible.windows.win_security_policy does NOT exist, we use secedit
via win_shell to export and parse Local Security Policy settings.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

from typing import Dict, Any
from .base import ResourceTranslator, TranslationResult


class SecurityPolicyTranslator(ResourceTranslator):
    """
    Translates InSpec security_policy resource to Ansible using secedit.
    
    NOTE: ansible.windows.win_security_policy does NOT exist in the collection.
    This translator uses secedit command via win_shell as a workaround.
    
    InSpec Example:
        describe security_policy do
          its('MaximumPasswordAge') { should cmp == 365 }
          its('MinimumPasswordAge') { should be >= 1 }
          its('PasswordHistorySize') { should cmp == 24 }
        end
    
    Ansible Output:
        - name: Export security policy with secedit
          ansible.windows.win_shell: |
            secedit /export /cfg $env:TEMP\\secpol.cfg /areas SECURITYPOLICY /quiet
            Get-Content $env:TEMP\\secpol.cfg
            Remove-Item $env:TEMP\\secpol.cfg -Force
          register: secpol_export
          changed_when: false
        
        - name: Parse security policy value
          ansible.builtin.set_fact:
            max_password_age: "{{ (secpol_export.stdout_lines | select('match', '^MaximumPasswordAge') | first | split('=') | last | trim) }}"
        
        - name: Validate Maximum Password Age
          ansible.builtin.assert:
            that:
              - max_password_age | int == 365
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
        Translate security_policy checks to Ansible tasks using secedit.
        
        Args:
            control_id: InSpec control ID
            describe: Parsed describe block with tests
        
        Returns:
            TranslationResult with Ansible tasks using secedit via win_shell
        """
        result = TranslationResult()
        var_name = self._sanitize_variable_name(f"{control_id}_secpol")
        
        # Collect all properties we need to check
        properties = []
        for test in describe.get('tests', []):
            if test['type'] == 'its':
                properties.append(test['property'])
        
        if not properties:
            result.warnings.append(
                f"security_policy check in control {control_id} has no properties to check"
            )
            result.requires_inspec = True
            return result
        
        # Task 1: Export security policy using secedit
        # This exports to a temp file, reads it, and cleans up
        export_task = {
            'name': f"Export security policy for control {control_id}",
            'ansible.windows.win_shell': (
                "secedit /export /cfg $env:TEMP\\secpol_{}.cfg /areas SECURITYPOLICY /quiet | Out-Null; "
                "Get-Content $env:TEMP\\secpol_{}.cfg; "
                "Remove-Item $env:TEMP\\secpol_{}.cfg -Force -ErrorAction SilentlyContinue"
            ).format(var_name, var_name, var_name),
            'register': f"{var_name}_export",
            'changed_when': False
        }
        result.tasks.append(export_task)
        
        # Task 2: Parse each policy value from the exported data
        for prop in properties:
            parse_task = {
                'name': f"Parse {prop} from security policy",
                'ansible.builtin.set_fact': {
                    f"{var_name}_{prop}": (
                        "{{{{ ({var}_export.stdout_lines | "
                        "select('match', '^{prop}\\s*=') | "
                        "first | default('{prop} = 0') | "
                        "regex_replace('^{prop}\\s*=\\s*(.*)$', '\\\\1') | "
                        "trim) }}}}"
                    ).format(var=var_name, prop=prop)
                }
            }
            result.tasks.append(parse_task)
        
        # Task 3: Build assertions for validation
        assertions = []
        for test in describe.get('tests', []):
            if test['type'] == 'its':
                property_name = test['property']
                property_path = f"{var_name}_{property_name}"
                
                # Extract operator and value
                operator = test.get('operator')
                value = test['value']
                
                # If value includes operator (like '== 365'), parse it
                if operator and value.startswith(operator):
                    value = value[len(operator):].strip()
                
                # Convert to integer if value is numeric
                if value.isdigit():
                    property_path = f"{property_path} | int"
                    value = int(value)
                
                assertion = self._convert_matcher_to_assertion(
                    property_path,
                    test['matcher'],
                    value,
                    test.get('negated', False),
                    operator
                )
                assertions.append(assertion)
        
        if assertions:
            # Generate a valid register variable name from control_id
            register_name = re.sub(r'[^a-zA-Z0-9_]', '_', control_id)
            register_name = re.sub(r'_+', '_', register_name).strip('_')
            if register_name and register_name[0].isdigit():
                register_name = 'control_' + register_name
            
            assert_task = {
                'name': f"Validate security policy for control {control_id}",
                'ignore_errors': True,
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': f"Security policy check failed for control {control_id}",
                    'success_msg': f"Security policy check passed for control {control_id}"
                },
                'register': f"{register_name}_result"
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
