"""
InSpec Execution Server - Web UI and REST API for ansible-inspec

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0

This module provides a web-based execution platform for InSpec profile execution
with ansible-inspec, offering job templates, workflow management, and REST API access.
"""

from .api import app
from .models import JobTemplate, Job, WorkflowTemplate
from .executor import JobExecutor

__all__ = ['app', 'JobTemplate', 'Job', 'WorkflowTemplate', 'JobExecutor']
