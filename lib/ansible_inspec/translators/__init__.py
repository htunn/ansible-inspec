"""
Resource Translators for InSpec to Ansible Conversion

This module provides translators that convert InSpec resource checks
into native Ansible module tasks, eliminating the need for InSpec
installation on target systems.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

from .base import ResourceTranslator, TranslationResult
from .security_policy import SecurityPolicyTranslator
from .registry_key import RegistryKeyTranslator
from .audit_policy import AuditPolicyTranslator
from .service import ServiceTranslator
from .windows_feature import WindowsFeatureTranslator
from .file_resource import FileTranslator
from .custom_resource import CustomResourceTranslator

__all__ = [
    'ResourceTranslator',
    'TranslationResult',
    'SecurityPolicyTranslator',
    'RegistryKeyTranslator',
    'AuditPolicyTranslator',
    'ServiceTranslator',
    'WindowsFeatureTranslator',
    'FileTranslator',
    'CustomResourceTranslator',
    'get_translator',
    'RESOURCE_MAPPINGS'
]

# Resource translation mappings
RESOURCE_MAPPINGS = {
    'security_policy': SecurityPolicyTranslator,
    'registry_key': RegistryKeyTranslator,
    'audit_policy': AuditPolicyTranslator,
    'service': ServiceTranslator,
    'windows_feature': WindowsFeatureTranslator,
    'windows_feature_dism': WindowsFeatureTranslator,
    'file': FileTranslator,
    # Add more mappings as translators are implemented
}


def get_translator(resource_type: str, custom_resources: dict = None) -> 'ResourceTranslator':
    """
    Get appropriate translator for InSpec resource type.
    
    Args:
        resource_type: InSpec resource name (e.g., 'security_policy', 'registry_key')
        custom_resources: Optional dict of parsed custom resources for dynamic translation
    
    Returns:
        Translator instance for the resource type, or None if no translator available
    
    Example:
        >>> translator = get_translator('security_policy')
        >>> if translator:
        ...     tasks = translator.translate(inspec_describe)
        
        >>> # For custom resources
        >>> translator = get_translator('win_feature_dism', custom_resources)
        >>> if translator:
        ...     tasks = translator.translate(inspec_describe)
    """
    # First check if it's a built-in resource with a dedicated translator
    translator_class = RESOURCE_MAPPINGS.get(resource_type)
    if translator_class:
        return translator_class()
    
    # If not found and custom_resources provided, try dynamic custom resource translator
    if custom_resources and resource_type in custom_resources:
        return CustomResourceTranslator(custom_resources)
    
    return None
