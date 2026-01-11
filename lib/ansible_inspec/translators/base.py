"""
Base classes for InSpec resource translators

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TranslationResult:
    """Result of translating an InSpec resource to Ansible tasks"""
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    requires_inspec: bool = False  # True if translation requires InSpec fallback
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class ResourceTranslator(ABC):
    """
    Base class for InSpec resource to Ansible module translators.
    
    Each translator converts an InSpec describe block into equivalent
    native Ansible tasks that perform the same compliance checks without
    requiring InSpec to be installed on target systems.
    """
    
    @abstractmethod
    def can_translate(self, describe: Dict[str, Any]) -> bool:
        """
        Check if this translator can handle the given InSpec describe block.
        
        Args:
            describe: Parsed InSpec describe block containing:
                - resource: Resource type (e.g., 'security_policy')
                - argument: Resource argument if any
                - expectations: List of property checks
        
        Returns:
            True if translator can convert to native Ansible, False otherwise
        """
        pass
    
    @abstractmethod
    def translate(self, control_id: str, describe: Dict[str, Any]) -> TranslationResult:
        """
        Translate InSpec describe block to native Ansible tasks.
        
        Args:
            control_id: InSpec control ID (for task naming)
            describe: Parsed InSpec describe block
        
        Returns:
            TranslationResult with generated Ansible tasks
        
        Example Input (describe):
            {
                'resource': 'security_policy',
                'expectations': [
                    {
                        'type': 'its',
                        'property': 'MaximumPasswordAge',
                        'matcher': 'cmp',
                        'value': '365',
                        'negate': False
                    }
                ]
            }
        
        Example Output (tasks):
            [
                {
                    'name': 'Get security policy settings',
                    'ansible.windows.win_security_policy': {
                        'section': 'System Access'
                    },
                    'register': 'security_policy_result'
                },
                {
                    'name': 'Validate Maximum Password Age',
                    'ansible.builtin.assert': {
                        'that': ['security_policy_result.MaximumPasswordAge == 365'],
                        'fail_msg': 'MaximumPasswordAge should be 365'
                    }
                }
            ]
        """
        pass
    
    def _convert_matcher_to_assertion(self, property_path: str, matcher: str, 
                                      value: Any, negate: bool = False, operator: str = None) -> str:
        """
        Convert InSpec matcher to Ansible assertion expression.
        
        Args:
            property_path: Jinja2 path to property (e.g., 'result.MaximumPasswordAge')
            matcher: InSpec matcher (eq, cmp, be, match, etc.)
            value: Expected value
            negate: True for should_not, False for should
            operator: Optional operator (==, >=, <=, etc.) from InSpec test
        
        Returns:
            Ansible assertion string
        
        Examples:
            >>> _convert_matcher_to_assertion('result.value', 'eq', 1, False)
            'result.value == 1'
            
            >>> _convert_matcher_to_assertion('result.age', 'cmp', 365, False, '==')
            'result.age == 365'
            
            >>> _convert_matcher_to_assertion('result.age', 'be', 1, False, '>=')
            'result.age >= 1'
        """
        # If operator is provided, use it directly
        if operator:
            # Quote string values if needed
            if isinstance(value, str) and not value.isdigit() and not value.startswith("'"):
                value = f"'{value}'"
            
            if negate:
                # Invert operator
                operator_inverse = {
                    '==': '!=',
                    '!=': '==',
                    '>=': '<',
                    '<=': '>',
                    '>': '<=',
                    '<': '>='
                }
                operator = operator_inverse.get(operator, operator)
            
            return f"{property_path} {operator} {value}"
        
        # Handle different matcher types
        operator_map = {
            'eq': '==',
            'cmp': '==',
            'be': '==',
            'be_in': 'in',
        }
        
        if matcher in ['match', 'regex']:
            # Convert regex matcher to Ansible regex test
            pattern = value.strip('/').strip()  # Remove regex delimiters
            assertion = f"{property_path} is match('{pattern}')"
            if negate:
                assertion = f"{property_path} is not match('{pattern}')"
        elif matcher == 'be_in':
            # Handle inclusion checks
            assertion = f"{value} in {property_path}"
            if negate:
                assertion = f"{value} not in {property_path}"
        elif matcher == 'include':
            # Handle contains checks
            assertion = f"'{value}' in {property_path}"
            if negate:
                assertion = f"'{value}' not in {property_path}"
        elif matcher in ['be_>=', 'be_>']:
            # Handle comparison operators
            op = matcher.replace('be_', '')
            assertion = f"{property_path} {op} {value}"
            if negate:
                # Invert comparison
                op = '<' if op == '>=' else '<='
                assertion = f"{property_path} {op} {value}"
        elif matcher in ['be_<=', 'be_<']:
            op = matcher.replace('be_', '')
            assertion = f"{property_path} {op} {value}"
            if negate:
                op = '>' if op == '<=' else '>='
                assertion = f"{property_path} {op} {value}"
        else:
            # Default to equality check
            operator = operator_map.get(matcher, '==')
            # Quote string values
            if isinstance(value, str) and not value.isdigit():
                value = f"'{value}'"
            assertion = f"{property_path} {operator} {value}"
            if negate:
                assertion = f"{property_path} != {value}"
        
        return assertion
    
    def _sanitize_variable_name(self, name: str) -> str:
        """Convert name to valid Ansible variable name"""
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        sanitized = re.sub(r'_+', '_', sanitized)
        if sanitized and sanitized[0].isdigit():
            sanitized = 'var_' + sanitized
        return sanitized.strip('_') or 'var_result'
