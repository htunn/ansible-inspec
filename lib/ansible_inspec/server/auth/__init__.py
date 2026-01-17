"""
Authentication module for ansible-inspec server.
"""
from .azure_ad import AzureADAuth, get_azure_ad_auth
from .dependencies import (
    get_current_user,
    get_current_active_user,
    require_role,
    require_admin,
    require_operator,
    require_viewer,
    security
)

__all__ = [
    'AzureADAuth',
    'get_azure_ad_auth',
    'get_current_user',
    'get_current_active_user',
    'require_role',
    'require_admin',
    'require_operator',
    'require_viewer',
    'security',
]
