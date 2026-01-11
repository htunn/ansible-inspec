"""
Tests for InSpec resource translators

These tests verify that translators convert InSpec resources to native
Ansible modules without requiring InSpec on target systems.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import pytest
from ansible_inspec.translators.security_policy import SecurityPolicyTranslator
from ansible_inspec.translators.registry_key import RegistryKeyTranslator
from ansible_inspec.translators.audit_policy import AuditPolicyTranslator
from ansible_inspec.translators.service import ServiceTranslator
from ansible_inspec.translators.windows_feature import WindowsFeatureTranslator
from ansible_inspec.translators.file_resource import FileTranslator
from ansible_inspec.translators import get_translator, RESOURCE_MAPPINGS


class TestSecurityPolicyTranslator:
    """Test SecurityPolicyTranslator converts to win_security_policy"""
    
    def test_can_translate_security_policy(self):
        """Verify translator recognizes security_policy resource"""
        translator = SecurityPolicyTranslator()
        describe = {'resource': 'security_policy'}
        assert translator.can_translate(describe)
    
    def test_translate_password_age_policy(self):
        """Verify MaximumPasswordAge translates to native Ansible"""
        translator = SecurityPolicyTranslator()
        describe = {
            'resource': 'security_policy',
            'tests': [
                {
                    'type': 'its',
                    'property': 'MaximumPasswordAge',
                    'matcher': 'cmp',
                    'value': '365',
                    'negated': False
                }
            ]
        }
        
        result = translator.translate('test_control', describe)
        
        # Should generate native Ansible tasks (export + parse + assert)
        assert len(result.tasks) == 3
        assert not result.requires_inspec  # ✅ NO InSpec required!
        
        # First task: Export security policy with secedit
        assert 'ansible.windows.win_shell' in result.tasks[0]
        assert 'secedit /export' in result.tasks[0]['ansible.windows.win_shell']
        
        # Second task: Parse value
        assert 'ansible.builtin.set_fact' in result.tasks[1]
        
        # Third task: Assert values with ignore_errors and register
        assert 'ansible.builtin.assert' in result.tasks[2]
        assert 'ignore_errors' in result.tasks[2]
        assert result.tasks[2]['ignore_errors'] is True
        assert 'register' in result.tasks[2]
        assert result.tasks[2]['register'] == 'test_control_result'
    
    def test_translate_multiple_password_policies(self):
        """Verify multiple password policy checks"""
        translator = SecurityPolicyTranslator()
        describe = {
            'resource': 'security_policy',
            'tests': [
                {'type': 'its', 'property': 'MaximumPasswordAge', 'matcher': 'cmp', 'value': '365', 'negated': False},
                {'type': 'its', 'property': 'MinimumPasswordAge', 'matcher': 'be_>=', 'value': '1', 'negated': False},
                {'type': 'its', 'property': 'MinimumPasswordLength', 'matcher': 'be_>=', 'value': '14', 'negated': False}
            ]
        }
        
        result = translator.translate('test_control', describe)
        
        assert not result.requires_inspec
        assert len(result.tasks) == 5  # export + 3 parse tasks + assert
        
        # Check last task has assertions for all three properties and includes ignore_errors/register
        assert 'ansible.builtin.assert' in result.tasks[4]
        assert 'ignore_errors' in result.tasks[4]
        assert result.tasks[4]['ignore_errors'] is True
        assert 'register' in result.tasks[4]
        assertions = result.tasks[4]['ansible.builtin.assert']['that']
        assert len(assertions) == 3
        assert any('MaximumPasswordAge' in a for a in assertions)
        assert any('MinimumPasswordAge' in a for a in assertions)
        assert any('MinimumPasswordLength' in a for a in assertions)


class TestRegistryKeyTranslator:
    """Test RegistryKeyTranslator converts to win_reg_stat"""
    
    def test_can_translate_registry_key(self):
        """Verify translator recognizes registry_key resource"""
        translator = RegistryKeyTranslator()
        describe = {'resource': 'registry_key'}
        assert translator.can_translate(describe)
    
    def test_translate_registry_key_existence(self):
        """Verify registry key existence check"""
        translator = RegistryKeyTranslator()
        describe = {
            'resource': 'registry_key',
            'argument': 'HKLM\\Software\\Policies\\Microsoft\\Windows\\System',
            'tests': [
                {'type': 'it', 'matcher': 'exist', 'negated': False}
            ]
        }
        
        result = translator.translate('test_control', describe)
        
        assert not result.requires_inspec  # ✅ NO InSpec required!
        assert len(result.tasks) == 2
        
        # Check win_reg_stat usage
        assert 'ansible.windows.win_reg_stat' in result.tasks[0]
        assert result.tasks[0]['ansible.windows.win_reg_stat']['path'] == 'HKLM:\\Software\\Policies\\Microsoft\\Windows\\System'
        
        # Check existence assertion
        assert 'ansible.builtin.assert' in result.tasks[1]
        assert 'test_control_registry.exists' in result.tasks[1]['ansible.builtin.assert']['that']
    
    def test_translate_registry_value_check(self):
        """Verify registry value property check"""
        translator = RegistryKeyTranslator()
        describe = {
            'resource': 'registry_key',
            'argument': 'HKLM\\Software\\Policies\\Microsoft\\Windows\\System',
            'tests': [
                {'type': 'it', 'matcher': 'exist', 'negated': False},
                {'type': 'its', 'property': 'EnableSmartScreen', 'matcher': 'eq', 'value': '1', 'negated': False}
            ]
        }
        
        result = translator.translate('test_control', describe)
        
        assert not result.requires_inspec
        assertions = result.tasks[1]['ansible.builtin.assert']['that']
        assert len(assertions) == 2
        assert 'test_control_registry.properties.EnableSmartScreen == 1' in assertions
    
    def test_convert_registry_path_formats(self):
        """Verify registry path conversion from InSpec to PowerShell format"""
        translator = RegistryKeyTranslator()
        
        # Test conversions
        assert translator._convert_registry_path('HKLM\\Software\\Test') == 'HKLM:\\Software\\Test'
        assert translator._convert_registry_path('HKEY_LOCAL_MACHINE\\System') == 'HKLM:\\System'
        assert translator._convert_registry_path('HKCU\\Software') == 'HKCU:\\Software'


class TestAuditPolicyTranslator:
    """Test AuditPolicyTranslator converts to auditpol commands"""
    
    def test_can_translate_audit_policy(self):
        """Verify translator recognizes audit_policy resource"""
        translator = AuditPolicyTranslator()
        describe = {'resource': 'audit_policy'}
        assert translator.can_translate(describe)
    
    def test_translate_audit_policy_check(self):
        """Verify audit policy check uses auditpol command"""
        translator = AuditPolicyTranslator()
        describe = {
            'resource': 'audit_policy',
            'tests': [
                {
                    'type': 'its',
                    'property': 'Credential Validation',
                    'matcher': 'eq',
                    'value': 'Success and Failure',
                    'negated': False
                }
            ]
        }
        
        result = translator.translate('test_control', describe)
        
        assert not result.requires_inspec  # ✅ Uses native auditpol.exe!
        assert len(result.tasks) == 2
        
        # Check win_shell with auditpol
        assert 'ansible.windows.win_shell' in result.tasks[0]
        assert 'auditpol /get /subcategory:"Credential Validation"' in result.tasks[0]['ansible.windows.win_shell']
        
        # Check assertion
        assert "'Success and Failure' in test_control_audit_0.stdout" in result.tasks[1]['ansible.builtin.assert']['that']


class TestServiceTranslator:
    """Test ServiceTranslator converts to win_service_info"""
    
    def test_can_translate_service(self):
        """Verify translator recognizes service resource"""
        translator = ServiceTranslator()
        describe = {'resource': 'service'}
        assert translator.can_translate(describe)
    
    def test_translate_service_running_check(self):
        """Verify service running check uses win_service_info"""
        translator = ServiceTranslator()
        describe = {
            'resource': 'service',
            'argument': 'W32Time',
            'tests': [
                {'type': 'it', 'matcher': 'be_installed', 'negated': False},
                {'type': 'it', 'matcher': 'be_running', 'negated': False}
            ]
        }
        
        result = translator.translate('test_control', describe)
        
        assert not result.requires_inspec  # ✅ NO InSpec required!
        assert len(result.tasks) == 2
        
        # Check win_service_info usage
        assert 'ansible.windows.win_service_info' in result.tasks[0]
        assert result.tasks[0]['ansible.windows.win_service_info']['name'] == 'W32Time'
        
        # Check assertions
        assertions = result.tasks[1]['ansible.builtin.assert']['that']
        assert 'test_control_service.exists' in assertions
        assert "test_control_service.services[0].state == 'running'" in assertions


class TestWindowsFeatureTranslator:
    """Test WindowsFeatureTranslator converts to win_feature"""
    
    def test_can_translate_windows_feature(self):
        """Verify translator recognizes windows_feature resource"""
        translator = WindowsFeatureTranslator()
        describe = {'resource': 'windows_feature'}
        assert translator.can_translate(describe)
    
    def test_translate_feature_not_installed(self):
        """Verify feature not installed check"""
        translator = WindowsFeatureTranslator()
        describe = {
            'resource': 'windows_feature',
            'argument': 'Telnet-Client',
            'tests': [
                {'type': 'it', 'matcher': 'be_installed', 'negated': True}
            ]
        }
        
        result = translator.translate('test_control', describe)
        
        assert not result.requires_inspec  # ✅ NO InSpec required!
        assert len(result.tasks) == 2
        
        # Check win_feature usage with query state
        assert 'ansible.windows.win_feature' in result.tasks[0]
        assert result.tasks[0]['ansible.windows.win_feature']['name'] == 'Telnet-Client'
        assert result.tasks[0]['ansible.windows.win_feature']['state'] == 'query'
        
        # Check assertion for NOT installed
        assert 'test_control_feature.installed == false' in result.tasks[1]['ansible.builtin.assert']['that']


class TestFileTranslator:
    """Test FileTranslator converts to win_stat/stat"""
    
    def test_can_translate_file(self):
        """Verify translator recognizes file resource"""
        translator = FileTranslator()
        describe = {'resource': 'file'}
        assert translator.can_translate(describe)
    
    def test_translate_file_exists_check_windows(self):
        """Verify file existence check on Windows"""
        translator = FileTranslator()
        describe = {
            'resource': 'file',
            'argument': 'C:/Windows/System32/drivers/etc/hosts',
            'tests': [
                {'type': 'it', 'matcher': 'exist', 'negated': False}
            ]
        }
        
        result = translator.translate('test_control', describe, is_windows=True)
        
        assert not result.requires_inspec  # ✅ NO InSpec required!
        assert len(result.tasks) == 2
        
        # Check win_stat usage
        assert 'ansible.windows.win_stat' in result.tasks[0]
        assert result.tasks[0]['ansible.windows.win_stat']['path'] == 'C:/Windows/System32/drivers/etc/hosts'


class TestTranslatorRegistry:
    """Test translator registration and lookup"""
    
    def test_get_translator_for_security_policy(self):
        """Verify get_translator returns correct translator"""
        translator = get_translator('security_policy')
        assert translator is not None
        assert isinstance(translator, SecurityPolicyTranslator)
    
    def test_get_translator_for_registry_key(self):
        """Verify registry_key translator lookup"""
        translator = get_translator('registry_key')
        assert translator is not None
        assert isinstance(translator, RegistryKeyTranslator)
    
    def test_get_translator_for_unsupported_resource(self):
        """Verify unsupported resource returns None"""
        translator = get_translator('unsupported_resource_type')
        assert translator is None
    
    def test_resource_mappings_complete(self):
        """Verify RESOURCE_MAPPINGS has expected resources"""
        assert 'security_policy' in RESOURCE_MAPPINGS
        assert 'registry_key' in RESOURCE_MAPPINGS
        assert 'audit_policy' in RESOURCE_MAPPINGS
        assert 'service' in RESOURCE_MAPPINGS
        assert 'windows_feature' in RESOURCE_MAPPINGS
        assert 'file' in RESOURCE_MAPPINGS


class TestNoInSpecDependency:
    """Critical tests: Verify NO InSpec dependency in generated tasks"""
    
    def test_security_policy_no_inspec_command(self):
        """CRITICAL: security_policy should NOT execute 'inspec' command"""
        translator = SecurityPolicyTranslator()
        describe = {
            'resource': 'security_policy',
            'tests': [
                {'type': 'its', 'property': 'MaximumPasswordAge', 'matcher': 'cmp', 'value': '365', 'negated': False}
            ]
        }
        
        result = translator.translate('test', describe)
        
        # Convert tasks to string and check for 'inspec' command
        tasks_str = str(result.tasks)
        assert 'inspec exec' not in tasks_str.lower()
        assert 'inspec' not in tasks_str  # Should not mention InSpec at all
    
    def test_registry_key_no_inspec_command(self):
        """CRITICAL: registry_key should NOT execute 'inspec' command"""
        translator = RegistryKeyTranslator()
        describe = {
            'resource': 'registry_key',
            'argument': 'HKLM\\Software\\Test',
            'tests': [
                {'type': 'it', 'matcher': 'exist', 'negated': False}
            ]
        }
        
        result = translator.translate('test', describe)
        
        tasks_str = str(result.tasks)
        assert 'inspec exec' not in tasks_str.lower()
        assert 'stdin' not in tasks_str  # InSpec wrapper uses stdin
    
    def test_all_translators_use_native_modules(self):
        """CRITICAL: All translators must use native Ansible modules"""
        test_cases = [
            ('security_policy', SecurityPolicyTranslator(), {
                'resource': 'security_policy',
                'tests': [{'type': 'its', 'property': 'MaximumPasswordAge', 'matcher': 'cmp', 'value': '365', 'negated': False}]
            }),
            ('registry_key', RegistryKeyTranslator(), {
                'resource': 'registry_key',
                'argument': 'HKLM\\Software\\Test',
                'tests': [{'type': 'it', 'matcher': 'exist', 'negated': False}]
            }),
            ('service', ServiceTranslator(), {
                'resource': 'service',
                'argument': 'TestService',
                'tests': [{'type': 'it', 'matcher': 'be_running', 'negated': False}]
            }),
        ]
        
        for resource_name, translator, describe in test_cases:
            result = translator.translate(f'test_{resource_name}', describe)
            
            # Must not require InSpec
            assert not result.requires_inspec, f"{resource_name} should not require InSpec!"
            
            # Must generate tasks
            assert len(result.tasks) > 0, f"{resource_name} should generate tasks!"
            
            # Tasks should not contain InSpec commands
            tasks_str = str(result.tasks).lower()
            assert 'inspec exec' not in tasks_str, f"{resource_name} should not use 'inspec exec'!"
