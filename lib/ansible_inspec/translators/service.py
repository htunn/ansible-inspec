"""
Service Translator - Convert InSpec service to Ansible

Translates InSpec service checks to native Ansible 
ansible.windows.win_service module calls.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

from typing import Dict, Any
from .base import ResourceTranslator, TranslationResult


class ServiceTranslator(ResourceTranslator):
    """
    Translates InSpec service resource to Ansible win_service.
    
    InSpec Example:
        describe service('W32Time') do
          it { should be_installed }
          it { should be_running }
          its('startmode') { should eq 'Auto' }
        end
    
    Ansible Output:
        - name: Check service W32Time
          ansible.windows.win_service_info:
            name: W32Time
          register: service_w32time
        
        - name: Validate service W32Time
          ansible.builtin.assert:
            that:
              - service_w32time.exists
              - service_w32time.services[0].state == 'running'
              - service_w32time.services[0].start_mode == 'auto'
    """
    
    def can_translate(self, describe: Dict[str, Any]) -> bool:
        """Check if describe block is for service resource"""
        return describe.get('resource') == 'service'
    
    def translate(self, control_id: str, describe: Dict[str, Any]) -> TranslationResult:
        """
        Translate service checks to native Ansible tasks.
        
        Args:
            control_id: InSpec control ID
            describe: Parsed describe block with service expectations
        
        Returns:
            TranslationResult with Ansible tasks using win_service_info
        """
        result = TranslationResult()
        var_name = self._sanitize_variable_name(f"{control_id}_service")
        
        # Extract service name from argument
        service_name = describe.get('argument', '')
        if not service_name:
            result.warnings.append(
                f"service check in control {control_id} has no service name"
            )
            result.requires_inspec = True
            return result
        
        # Task 1: Get service information
        fetch_task = {
            'name': f"Get service info for {service_name}",
            'ansible.windows.win_service_info': {
                'name': service_name
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
                
                # Map InSpec matchers to service states
                if matcher == 'be_installed' or matcher == 'exist':
                    if negate:
                        assertions.append(f"not {var_name}.exists")
                    else:
                        assertions.append(f"{var_name}.exists")
                
                elif matcher == 'be_running':
                    if negate:
                        assertions.append(f"{var_name}.services[0].state != 'running'")
                    else:
                        assertions.append(f"{var_name}.services[0].state == 'running'")
                
                elif matcher == 'be_enabled':
                    if negate:
                        assertions.append(f"{var_name}.services[0].start_mode not in ['auto', 'automatic']")
                    else:
                        assertions.append(f"{var_name}.services[0].start_mode in ['auto', 'automatic']")
            
            elif test['type'] == 'its':
                property_name = test['property']
                
                # Map property names
                property_map = {
                    'startmode': 'start_mode',
                    'start_mode': 'start_mode',
                    'state': 'state',
                    'status': 'state'
                }
                
                ansible_property = property_map.get(property_name.lower(), property_name)
                property_path = f"{var_name}.services[0].{ansible_property}"
                
                # Convert startmode values (InSpec uses 'Auto', Ansible uses 'auto')
                value = test['value']
                if property_name.lower() in ['startmode', 'start_mode']:
                    value = value.lower()
                
                assertion = self._convert_matcher_to_assertion(
                    property_path,
                    test['matcher'],
                    value,
                    test.get('negated', False)
                )
                assertions.append(assertion)
        
        if assertions:
            assert_task = {
                'name': f"Validate service {service_name}",
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': f"Service check failed for {service_name}",
                    'success_msg': f"Service check passed for {service_name}"
                }
            }
            result.tasks.append(assert_task)
        
        return result
