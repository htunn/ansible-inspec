"""
File Translator - Convert InSpec file to Ansible

Translates InSpec file checks to native Ansible 
ansible.windows.win_stat or ansible.builtin.stat module calls.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

from typing import Dict, Any
from .base import ResourceTranslator, TranslationResult


class FileTranslator(ResourceTranslator):
    """
    Translates InSpec file resource to Ansible win_stat or stat.
    
    InSpec Example:
        describe file('C:/Windows/System32/drivers/etc/hosts') do
          it { should exist }
          it { should_not be_writable }
        end
    
    Ansible Output:
        - name: Check file C:/Windows/System32/drivers/etc/hosts
          ansible.windows.win_stat:
            path: C:/Windows/System32/drivers/etc/hosts
          register: file_hosts
        
        - name: Validate file
          ansible.builtin.assert:
            that:
              - file_hosts.stat.exists
              - not file_hosts.stat.writable
    """
    
    def can_translate(self, describe: Dict[str, Any]) -> bool:
        """Check if describe block is for file resource"""
        return describe.get('resource') == 'file'
    
    def translate(self, control_id: str, describe: Dict[str, Any], 
                  is_windows: bool = True) -> TranslationResult:
        """
        Translate file checks to native Ansible tasks.
        
        Args:
            control_id: InSpec control ID
            describe: Parsed describe block with file expectations
            is_windows: True for Windows targets (use win_stat), False for Linux (use stat)
        
        Returns:
            TranslationResult with Ansible tasks using win_stat or stat
        """
        result = TranslationResult()
        var_name = self._sanitize_variable_name(f"{control_id}_file")
        
        # Extract file path from argument
        file_path = describe.get('argument', '')
        if not file_path:
            result.warnings.append(
                f"file check in control {control_id} has no path specified"
            )
            result.requires_inspec = True
            return result
        
        # Task 1: Get file stats
        if is_windows:
            fetch_task = {
                'name': f"Check file {file_path}",
                'ansible.windows.win_stat': {
                    'path': file_path
                },
                'register': var_name
            }
        else:
            fetch_task = {
                'name': f"Check file {file_path}",
                'ansible.builtin.stat': {
                    'path': file_path
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
                
                # Map InSpec file matchers to stat properties
                matcher_map = {
                    'exist': f"{var_name}.stat.exists",
                    'be_file': f"{var_name}.stat.isreg",
                    'be_directory': f"{var_name}.stat.isdir",
                    'be_readable': f"{var_name}.stat.readable",
                    'be_writable': f"{var_name}.stat.writable",
                    'be_executable': f"{var_name}.stat.executable",
                }
                
                property_path = matcher_map.get(matcher)
                if property_path:
                    if negate:
                        assertions.append(f"not {property_path}")
                    else:
                        assertions.append(property_path)
            
            elif test['type'] == 'its':
                property_name = test['property']
                
                # Map InSpec properties to stat properties
                property_map = {
                    'mode': 'mode',
                    'owner': 'owner',
                    'group': 'gr_name',
                    'size': 'size',
                    'mtime': 'mtime'
                }
                
                ansible_property = property_map.get(property_name, property_name)
                property_path = f"{var_name}.stat.{ansible_property}"
                
                assertion = self._convert_matcher_to_assertion(
                    property_path,
                    test['matcher'],
                    test['value'],
                    test.get('negated', False)
                )
                assertions.append(assertion)
        
        if assertions:
            # Generate a valid register variable name from control_id
            register_name = re.sub(r'[^a-zA-Z0-9_]', '_', control_id)
            register_name = re.sub(r'_+', '_', register_name).strip('_')
            if register_name and register_name[0].isdigit():
                register_name = 'control_' + register_name
            
            assert_task = {
                'name': f"Validate file {file_path}",
                'ignore_errors': True,
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': f"File check failed for {file_path}",
                    'success_msg': f"File check passed for {file_path}"
                },
                'register': f"{register_name}_result"
            }
            result.tasks.append(assert_task)
        
        return result
