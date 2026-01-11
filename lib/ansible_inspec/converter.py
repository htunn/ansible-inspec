"""
InSpec Profile to Ansible Collection Converter

This module converts Ruby-based InSpec profiles into Ansible collections,
enabling compliance testing through native Ansible playbooks and roles.
Supports custom InSpec resources from libraries/ directory.

v0.2.0: Major architectural change - translates InSpec resources to native
Ansible modules instead of wrapping InSpec commands. This eliminates the
requirement to install InSpec on target systems.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import os
import re
import yaml
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

# Import resource translators
from .translators import get_translator, RESOURCE_MAPPINGS

__all__ = ['ProfileConverter', 'ConversionConfig', 'ConversionResult', 'sanitize_variable_name']


def sanitize_variable_name(control_id: str) -> str:
    """
    Convert InSpec control ID to valid Ansible variable name.
    
    Ansible variable names must:
    - Start with a letter or underscore
    - Contain only letters, numbers, and underscores
    
    Args:
        control_id: InSpec control ID (may contain special characters)
    
    Returns:
        Sanitized variable name safe for use in Ansible
    
    Examples:
        >>> sanitize_variable_name("2.2.27 (L1) Ensure Enable...")
        'inspec_2_2_27_L1_Ensure_Enable'
        >>> sanitize_variable_name("test-1.2.3")
        'test_1_2_3'
        >>> sanitize_variable_name("123test")
        'inspec_123test'
    """
    # Replace all non-alphanumeric characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', control_id)
    
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Ensure it starts with a letter or underscore (not a digit)
    if sanitized and sanitized[0].isdigit():
        sanitized = 'inspec_' + sanitized
    
    # Remove leading and trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = 'inspec_control'
    
    return sanitized


@dataclass
class ConversionConfig:
    """Configuration for profile conversion"""
    source_profile: str  # Path to InSpec profile
    output_dir: str  # Where to create collection
    namespace: str = "compliance"  # Ansible Galaxy namespace
    collection_name: str = "inspec_profiles"  # Collection name
    create_roles: bool = True  # Create roles for each control file
    create_playbooks: bool = True  # Create example playbooks
    use_native_modules: bool = True  # Prefer Ansible modules over InSpec wrapper
    license: str = "GPL-3.0-or-later"
    version: str = "1.0.0"


@dataclass
class ConversionResult:
    """Result of profile conversion"""
    success: bool
    collection_path: str
    roles_created: List[str] = field(default_factory=list)
    playbooks_created: List[str] = field(default_factory=list)
    controls_converted: int = 0
    custom_resources_found: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class CustomResourceParser:
    """
    Parses InSpec custom resources from libraries/ directory
    """
    
    RESOURCE_CLASS_PATTERN = re.compile(
        r"class\s+(\w+)\s+<\s+Inspec\.resource\(\d+\)(.*?)^end",
        re.MULTILINE | re.DOTALL
    )
    
    NAME_PATTERN = re.compile(r"name\s+['\"](\w+)['\"]")
    SUPPORTS_PATTERN = re.compile(r"supports\s+(.*?)$", re.MULTILINE)
    DESC_PATTERN = re.compile(r"desc\s+['\"]([^'\"]+)['\"]", re.DOTALL)
    
    def __init__(self, libraries_dir: str):
        self.libraries_dir = libraries_dir
        self.custom_resources = {}
    
    def parse(self) -> Dict[str, Dict[str, Any]]:
        """Parse all custom resources in libraries directory"""
        if not os.path.exists(self.libraries_dir):
            return {}
        
        for resource_file in Path(self.libraries_dir).glob('*.rb'):
            self._parse_resource_file(resource_file)
        
        return self.custom_resources
    
    def _parse_resource_file(self, filepath: Path):
        """Parse a single custom resource file"""
        with open(filepath, 'r') as f:
            content = f.read()
        
        for match in self.RESOURCE_CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            class_body = match.group(2)
            
            # Extract resource name
            name_match = self.NAME_PATTERN.search(class_body)
            resource_name = name_match.group(1) if name_match else class_name.lower()
            
            # Extract description
            desc_match = self.DESC_PATTERN.search(class_body)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # Extract platform support
            supports = []
            for support_match in self.SUPPORTS_PATTERN.finditer(class_body):
                supports.append(support_match.group(1).strip())
            
            self.custom_resources[resource_name] = {
                'class_name': class_name,
                'file': filepath.name,
                'supports': supports,
                'description': description,
                'content': content,
                'methods': self._extract_methods(class_body)
            }
    
    def _extract_methods(self, class_body: str) -> List[str]:
        """Extract public method names from resource class"""
        method_pattern = re.compile(r"^\s{2}def\s+(\w+)", re.MULTILINE)
        methods = []
        for m in method_pattern.finditer(class_body):
            method_name = m.group(1)
            # Skip private methods and initialize
            if not method_name.startswith('_') and method_name != 'initialize':
                methods.append(method_name)
        return methods


class InSpecControlParser:
    """
    Parses Ruby InSpec control blocks into structured data
    """
    
    # Fixed pattern: properly handles control IDs containing quotes
    CONTROL_PATTERN = re.compile(
        r"control\s+(['\"])(.+?)\1\s+do(.*?)^end",
        re.MULTILINE | re.DOTALL
    )
    
    DESCRIBE_PATTERN = re.compile(
        r"describe\s+(\w+)(?:\(['\"]?([^'\")\s]+)['\"]?\))?\s+do(.*?)^\s{2}end",
        re.MULTILINE | re.DOTALL
    )
    
    ITS_PATTERN = re.compile(
        r"its\(['\"]([^'\"]+)['\"]\)\s+{\s+should(_not)?\s+(\w+)\s*([=<>!]+)?\s*([^}]+)?\s*}",
        re.MULTILINE
    )
    
    IT_PATTERN = re.compile(
        r"it\s+{\s+should(_not)?\s+(\w+)\s*}",
        re.MULTILINE
    )
    
    def __init__(self, content: str):
        self.content = content
    
    def parse(self) -> List[Dict[str, Any]]:
        """Parse InSpec control file and extract controls"""
        controls = []
        
        # Updated to use group 2 for control_id, group 3 for body (added quote capture group)
        for match in self.CONTROL_PATTERN.finditer(self.content):
            control_id = match.group(2)
            control_body = match.group(3)
            
            control_data = {
                'id': control_id,
                'impact': self._extract_impact(control_body),
                'title': self._extract_title(control_body),
                'desc': self._extract_desc(control_body),
                'tags': self._extract_tags(control_body),
                'refs': self._extract_refs(control_body),
                'describes': self._parse_describe_blocks(control_body)
            }
            
            controls.append(control_data)
        
        return controls
    
    def _extract_impact(self, body: str) -> float:
        """Extract impact value"""
        match = re.search(r"impact\s+([\d.]+|['\"](?:none|low|medium|high|critical)['\"])", body)
        if match:
            value = match.group(1).strip("'\"")
            impact_map = {
                'none': 0.0,
                'low': 0.3,
                'medium': 0.5,
                'high': 0.8,
                'critical': 1.0
            }
            return impact_map.get(value, float(value) if value.replace('.', '').isdigit() else 0.5)
        return 0.5
    
    def _extract_title(self, body: str) -> str:
        """Extract title"""
        match = re.search(r"title\s+['\"]([^'\"]+)['\"]", body)
        return match.group(1) if match else ""
    
    def _extract_desc(self, body: str) -> str:
        """Extract description"""
        match = re.search(r"desc\s+['\"]([^'\"]+)['\"]", body, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_tags(self, body: str) -> List[str]:
        """Extract tags"""
        tags = []
        for match in re.finditer(r"tag\s+['\"]?(\w+)['\"]?", body):
            tags.append(match.group(1))
        return tags
    
    def _extract_refs(self, body: str) -> List[str]:
        """Extract references"""
        refs = []
        for match in re.finditer(r"ref\s+['\"]([^'\"]+)['\"]", body):
            refs.append(match.group(1))
        return refs
    
    def _parse_describe_blocks(self, body: str) -> List[Dict[str, Any]]:
        """Parse describe blocks within control"""
        describes = []
        
        for match in self.DESCRIBE_PATTERN.finditer(body):
            resource_type = match.group(1)
            resource_arg = match.group(2) or ""
            describe_body = match.group(3)
            
            describe_data = {
                'resource': resource_type,
                'argument': resource_arg,
                'tests': []
            }
            
            # Parse 'its' matchers
            for its_match in self.ITS_PATTERN.finditer(describe_body):
                # Groups: (property, negated, matcher, operator, value)
                operator = its_match.group(4)
                value_str = its_match.group(5) or ""
                
                # Clean up value - strip quotes and whitespace
                value_clean = value_str.strip().strip("'\"")
                
                # Combine operator and value if both exist
                if operator and value_clean:
                    full_value = f"{operator} {value_clean}"
                else:
                    full_value = value_clean
                
                describe_data['tests'].append({
                    'type': 'its',
                    'property': its_match.group(1),
                    'negated': its_match.group(2) == '_not',
                    'matcher': its_match.group(3),
                    'operator': operator,
                    'value': full_value
                })
            
            # Parse 'it' matchers
            for it_match in self.IT_PATTERN.finditer(describe_body):
                describe_data['tests'].append({
                    'type': 'it',
                    'negated': it_match.group(1) == '_not',
                    'matcher': it_match.group(2)
                })
            
            describes.append(describe_data)
        
        return describes


class AnsibleTaskGenerator:
    """
    Generates Ansible tasks from InSpec controls
    """
    
    # Mapping of InSpec resources to Ansible modules
    RESOURCE_MAP = {
        'file': 'ansible.builtin.stat',
        'directory': 'ansible.builtin.stat',
        'service': 'ansible.builtin.service_facts',
        'package': 'ansible.builtin.package_facts',
        'user': 'ansible.builtin.getent',
        'group': 'ansible.builtin.getent',
        'command': 'ansible.builtin.command',
        'sshd_config': 'ansible.builtin.lineinfile',
        'registry_key': 'ansible.windows.win_reg_stat',
        'security_policy': 'ansible.windows.win_security_policy',
        'postgres_session': 'community.postgresql.postgresql_query',
        'mysql_session': 'community.mysql.mysql_query',
        'port': 'ansible.builtin.wait_for',
        'processes': 'ansible.builtin.shell',
        'kernel_parameter': 'ansible.posix.sysctl',
    }
    
    def __init__(self, custom_resources: Optional[Dict] = None, is_windows_profile: bool = False):
        self.custom_resources = custom_resources or {}
        self.is_windows_profile = is_windows_profile
    
    def generate_tasks(self, controls: List[Dict[str, Any]], use_native: bool = True) -> List[Dict[str, Any]]:
        """Generate Ansible tasks from parsed controls"""
        tasks = []
        
        for control in controls:
            control_tasks = []
            
            for describe in control['describes']:
                resource_type = describe['resource']
                
                # Try to get translator (handles both built-in and custom resources)
                translator = get_translator(resource_type, self.custom_resources)
                
                if translator and translator.can_translate(describe):
                    # Use dynamic translator - supports custom resources!
                    translation_result = translator.translate(control['id'], describe)
                    
                    # If translation succeeded without requiring InSpec, use it
                    if translation_result.tasks and not translation_result.requires_inspec:
                        control_tasks.extend(translation_result.tasks)
                        continue
                
                # Fallback to legacy native tasks generation
                if use_native and resource_type in self.RESOURCE_MAP:
                    control_tasks.extend(
                        self._generate_native_tasks(control, describe)
                    )
                else:
                    # Final fallback to InSpec wrapper for unsupported resources
                    control_tasks.append(self._generate_inspec_fallback_task(control, describe))
            
            # Wrap in block with metadata
            if control_tasks:
                task_block = {
                    'name': control.get('title') or f"Control {control['id']}",
                    'tags': self._generate_tags(control),
                    'block': control_tasks
                }
                tasks.append(task_block)
        
        return tasks
    
    def _generate_native_tasks(self, control: Dict, describe: Dict) -> List[Dict[str, Any]]:
        """
        Generate native Ansible tasks for a describe block.
        
        v0.2.0: Uses resource translators to convert InSpec resources to native
        Ansible modules, eliminating the need for InSpec on target systems.
        
        Args:
            control: Parsed control data with id, title, etc.
            describe: Parsed describe block with resource and expectations
        
        Returns:
            List of native Ansible tasks (or InSpec fallback if unsupported)
        """
        resource = describe['resource']
        
        # Try to get a translator for this resource type
        translator = get_translator(resource)
        
        if translator and translator.can_translate(describe):
            # Use native translator - NO InSpec required!
            translation_result = translator.translate(control['id'], describe)
            
            # Log any warnings
            for warning in translation_result.warnings:
                # Could add to conversion result warnings
                pass
            
            # If translation succeeded, return native tasks
            if translation_result.tasks and not translation_result.requires_inspec:
                return translation_result.tasks
            # Otherwise fall through to legacy handling
        
        # Legacy fallback for resources not yet migrated to translator pattern
        if resource in ['file', 'directory']:
            return self._generate_file_tasks(describe)
        elif resource == 'service' and not translator:
            return self._generate_service_tasks(describe)
        elif resource == 'package':
            return self._generate_package_tasks(describe)
        elif resource == 'sshd_config':
            return self._generate_sshd_config_tasks(describe)
        elif resource == 'command':
            return self._generate_command_tasks(describe)
        elif resource == 'port':
            return self._generate_port_tasks(describe)
        elif resource == 'kernel_parameter':
            return self._generate_kernel_parameter_tasks(describe)
        else:
            # No translator and no legacy support - use InSpec fallback
            return [self._generate_inspec_fallback_task(control, describe)]
    
    def _generate_file_tasks(self, describe: Dict) -> List[Dict[str, Any]]:
        """Generate tasks for file/directory checks"""
        tasks = []
        path = describe['argument']
        var_name = f"stat_{path.replace('/', '_').replace('.', '_')}"
        
        tasks.append({
            'name': f"Gather stats for {path}",
            'ansible.builtin.stat': {'path': path},
            'register': var_name
        })
        
        assertions = []
        for test in describe['tests']:
            if test['type'] == 'it':
                matcher = test['matcher']
                negated = test.get('negated', False)
                
                if matcher == 'be_file':
                    assertions.append(f"{'not ' if negated else ''}{var_name}.stat.isreg")
                elif matcher == 'be_directory':
                    assertions.append(f"{'not ' if negated else ''}{var_name}.stat.isdir")
                elif matcher == 'exist':
                    assertions.append(f"{'not ' if negated else ''}{var_name}.stat.exists")
            elif test['type'] == 'its':
                prop = test['property']
                value = test['value']
                if prop == 'mode':
                    assertions.append(f"{var_name}.stat.mode == '{value}'")
                elif prop == 'owner':
                    assertions.append(f"{var_name}.stat.pw_name == '{value}'")
        
        if assertions:
            tasks.append({
                'name': f"Verify {path} compliance",
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': f"Compliance check failed for {path}"
                }
            })
        
        return tasks
    
    def _generate_service_tasks(self, describe: Dict) -> List[Dict[str, Any]]:
        """Generate tasks for service checks"""
        tasks = [{'name': "Gather service facts", 'ansible.builtin.service_facts': {}}]
        
        service_name = describe['argument']
        assertions = []
        
        for test in describe['tests']:
            if test['type'] == 'it':
                matcher = test['matcher']
                negated = test.get('negated', False)
                
                if matcher == 'be_running':
                    assertions.append(
                        f"services['{service_name}'].state {'!=' if negated else '=='} 'running'"
                    )
                elif matcher == 'be_enabled':
                    assertions.append(
                        f"services['{service_name}'].status {'!=' if negated else '=='} 'enabled'"
                    )
                elif matcher == 'be_installed':
                    assertions.append(
                        f"'{service_name}' {'not ' if negated else ''}in services"
                    )
        
        if assertions:
            tasks.append({
                'name': f"Verify {service_name} service",
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': f"Service {service_name} is not compliant"
                }
            })
        
        return tasks
    
    def _generate_package_tasks(self, describe: Dict) -> List[Dict[str, Any]]:
        """Generate tasks for package checks"""
        tasks = [{'name': "Gather package facts", 'ansible.builtin.package_facts': {'manager': 'auto'}}]
        
        package_name = describe['argument']
        assertions = []
        
        for test in describe['tests']:
            if test['type'] == 'it' and test['matcher'] == 'be_installed':
                negated = test.get('negated', False)
                assertions.append(
                    f"'{package_name}' {'not ' if negated else ''}in ansible_facts.packages"
                )
        
        if assertions:
            tasks.append({
                'name': f"Verify {package_name} package",
                'ansible.builtin.assert': {
                    'that': assertions,
                    'fail_msg': f"Package {package_name} compliance check failed"
                }
            })
        
        return tasks
    
    def _generate_sshd_config_tasks(self, describe: Dict) -> List[Dict[str, Any]]:
        """Generate tasks for sshd_config checks"""
        tasks = []
        
        for test in describe['tests']:
            if test['type'] == 'its':
                prop = test['property']
                value = test['value']
                var_name = f"ssh_check_{prop.lower()}"
                
                tasks.append({
                    'name': f"Check SSH config: {prop}",
                    'ansible.builtin.lineinfile': {
                        'path': '/etc/ssh/sshd_config',
                        'regexp': f"^{prop}",
                        'line': f"{prop} {value}",
                        'state': 'present'
                    },
                    'check_mode': True,
                    'register': var_name,
                    'failed_when': f"{var_name}.changed"
                })
        
        return tasks
    
    def _generate_command_tasks(self, describe: Dict) -> List[Dict[str, Any]]:
        """Generate tasks for command checks"""
        tasks = []
        command = describe['argument']
        
        tasks.append({
            'name': f"Execute: {command}",
            'ansible.builtin.command': command,
            'register': 'command_result',
            'changed_when': False
        })
        
        assertions = []
        for test in describe['tests']:
            if test['type'] == 'its':
                prop = test['property']
                matcher = test['matcher']
                value = test['value']
                
                if prop in ['exit_status', 'exit_code']:
                    assertions.append(f"command_result.rc == {value}")
                elif prop == 'stdout':
                    if matcher == 'match':
                        assertions.append(f"command_result.stdout is search('{value}')")
                    elif matcher in ['eq', 'cmp']:
                        assertions.append(f"command_result.stdout == '{value}'")
        
        if assertions:
            tasks.append({
                'name': "Verify command output",
                'ansible.builtin.assert': {'that': assertions}
            })
        
        return tasks
    
    def _generate_port_tasks(self, describe: Dict) -> List[Dict[str, Any]]:
        """Generate tasks for port checks"""
        port = describe['argument']
        return [{
            'name': f"Check port {port}",
            'ansible.builtin.wait_for': {
                'port': int(port),
                'timeout': 1,
                'state': 'started'
            }
        }]
    
    def _generate_kernel_parameter_tasks(self, describe: Dict) -> List[Dict[str, Any]]:
        """Generate tasks for kernel parameter checks"""
        param = describe['argument']
        tasks = []
        
        for test in describe['tests']:
            if test['type'] == 'its' and test['property'] == 'value':
                tasks.append({
                    'name': f"Check kernel parameter {param}",
                    'ansible.posix.sysctl': {
                        'name': param,
                        'value': test['value']
                    },
                    'check_mode': True,
                    'register': 'sysctl_check',
                    'failed_when': 'sysctl_check.changed'
                })
        
        return tasks
    
    def _generate_custom_resource_task(self, control: Dict, describe: Dict) -> Dict[str, Any]:
        """Generate task for custom InSpec resource using InSpec wrapper"""
        resource_name = describe['resource']
        var_name = sanitize_variable_name(control['id'])
        
        # Quote control ID for PowerShell to handle special characters
        if self.is_windows_profile:
            # Escape double quotes with backtick for PowerShell
            quoted_id = control['id'].replace('"', '`"')
            cmd = f'inspec exec - -t local:// --controls "{quoted_id}"'
        else:
            # Linux - quote for shell safety
            quoted_id = control['id'].replace('"', '\\"')
            cmd = f'inspec exec - -t local:// --controls "{quoted_id}"'
        
        stdin_content = self._generate_custom_resource_control(control, describe)
        
        # Windows module requires free-form syntax, Linux accepts both
        if self.is_windows_profile:
            task = {
                'name': f"Execute custom resource check: {resource_name}",
                'ansible.windows.win_shell': cmd,  # Free-form command
                'args': {
                    'stdin': stdin_content
                },
                'register': f"{var_name}_result",
                'failed_when': f"{var_name}_result.rc != 0",
                'environment': {
                    'INSPEC_LOAD_PATH': '{{ role_path }}/files/libraries'
                }
            }
        else:
            task = {
                'name': f"Execute custom resource check: {resource_name}",
                'ansible.builtin.shell': {
                    'cmd': cmd,
                    'stdin': stdin_content
                },
                'register': f"{var_name}_result",
                'failed_when': f"{var_name}_result.rc != 0",
                'environment': {
                    'INSPEC_LOAD_PATH': '{{ role_path }}/files/libraries'
                }
            }
        
        return task
    
    def _generate_inspec_fallback_task(self, control: Dict, describe: Dict) -> Dict[str, Any]:
        """Generate InSpec wrapper task for unsupported resources"""
        var_name = sanitize_variable_name(control['id'])
        
        # Quote control ID for PowerShell to handle special characters
        if self.is_windows_profile:
            # Escape double quotes with backtick for PowerShell
            quoted_id = control['id'].replace('"', '`"')
            cmd = f'inspec exec - -t local:// --controls "{quoted_id}"'
        else:
            # Linux - quote for shell safety
            quoted_id = control['id'].replace('"', '\\"')
            cmd = f'inspec exec - -t local:// --controls "{quoted_id}"'
        
        stdin_content = self._generate_control_snippet(control, describe)
        
        # Windows module requires free-form syntax, Linux accepts both
        if self.is_windows_profile:
            task = {
                'name': f"Execute InSpec check for {describe['resource']}",
                'ansible.windows.win_shell': cmd,  # Free-form command
                'args': {
                    'stdin': stdin_content
                },
                'register': f"{var_name}_result",
                'failed_when': f"{var_name}_result.rc != 0"
            }
        else:
            task = {
                'name': f"Execute InSpec check for {describe['resource']}",
                'ansible.builtin.shell': {
                    'cmd': cmd,
                    'stdin': stdin_content
                },
                'register': f"{var_name}_result",
                'failed_when': f"{var_name}_result.rc != 0"
            }
        
        return task
    
    def _generate_custom_resource_control(self, control: Dict, describe: Dict) -> str:
        """Generate InSpec control content for custom resource"""
        return self._generate_control_snippet(control, describe)
    
    def _generate_control_snippet(self, control: Dict, describe: Dict) -> str:
        """Generate InSpec control snippet"""
        resource_name = describe['resource']
        resource_arg = describe.get('argument', '')
        
        lines = [
            f"control '{control['id']}' do",
            f"  impact {control.get('impact', 0.5)}",
            f"  title '{control.get('title', '')}'",
            f"  ",
            f"  describe {resource_name}('{resource_arg}') do"
        ]
        
        for test in describe['tests']:
            if test['type'] == 'its':
                prop = test['property']
                matcher = test['matcher']
                value = test['value']
                should = 'should_not' if test.get('negated') else 'should'
                lines.append(f"    its('{prop}') {{ {should} {matcher} '{value}' }}")
            elif test['type'] == 'it':
                matcher = test['matcher']
                should = 'should_not' if test.get('negated') else 'should'
                lines.append(f"    it {{ {should} {matcher} }}")
        
        lines.extend(["  end", "end"])
        return '\n'.join(lines)
    
    def _generate_tags(self, control: Dict) -> List[str]:
        """Generate Ansible tags from control metadata"""
        tags = ['compliance']
        
        impact = control.get('impact', 0.5)
        if impact >= 0.9:
            tags.append('critical')
        elif impact >= 0.7:
            tags.append('high')
        elif impact >= 0.4:
            tags.append('medium')
        else:
            tags.append('low')
        
        tags.extend(control.get('tags', []))
        return tags


class ProfileConverter:
    """
    Main converter class that orchestrates InSpec profile to Ansible collection conversion
    """
    
    def __init__(self, config: ConversionConfig):
        self.config = config
        self.task_generator = None
        self.result = ConversionResult(
            success=False,
            collection_path=""
        )
    
    def convert(self) -> ConversionResult:
        """Execute the conversion process"""
        try:
            if not self._validate_source_profile():
                self.result.errors.append(f"Invalid InSpec profile: {self.config.source_profile}")
                return self.result
            
            # Parse custom resources
            libraries_dir = os.path.join(self.config.source_profile, 'libraries')
            custom_resource_parser = CustomResourceParser(libraries_dir)
            custom_resources = custom_resource_parser.parse()
            
            if custom_resources:
                self.result.custom_resources_found = len(custom_resources)
                self.result.warnings.append(
                    f"Found {len(custom_resources)} custom resource(s) - using InSpec wrapper"
                )
            
            # Detect Windows profile
            is_windows = self._detect_windows_profile()
            
            # Initialize task generator
            self.task_generator = AnsibleTaskGenerator(custom_resources, is_windows_profile=is_windows)
            
            # Create collection structure
            collection_path = self._create_collection_structure()
            self.result.collection_path = collection_path
            
            # Copy custom resource files
            if custom_resources:
                self._copy_custom_resources(collection_path, libraries_dir)
            
            # Convert controls
            controls_dir = os.path.join(self.config.source_profile, 'controls')
            if os.path.exists(controls_dir):
                for control_file in Path(controls_dir).glob('*.rb'):
                    self._convert_control_file(control_file, collection_path)
            
            # Create collection metadata
            self._create_galaxy_yml(collection_path)
            
            # Create example playbooks
            if self.config.create_playbooks and self.result.roles_created:
                self._create_example_playbooks(collection_path)
            
            # Create documentation
            self._create_readme(collection_path, custom_resources)
            if custom_resources:
                self._create_custom_resource_docs(collection_path, custom_resources)
            
            self.result.success = True
            return self.result
            
        except Exception as e:
            import traceback
            self.result.errors.append(f"Conversion failed: {str(e)}")
            self.result.errors.append(traceback.format_exc())
            return self.result
    
    def _validate_source_profile(self) -> bool:
        """Validate that source is a valid InSpec profile"""
        if not os.path.exists(self.config.source_profile):
            return False
        
        inspec_yml = os.path.join(self.config.source_profile, 'inspec.yml')
        controls_dir = os.path.join(self.config.source_profile, 'controls')
        
        return os.path.exists(inspec_yml) or os.path.exists(controls_dir)
    
    def _detect_windows_profile(self) -> bool:
        """Detect if this is a Windows InSpec profile"""
        # Check inspec.yml for platform support
        inspec_yml = os.path.join(self.config.source_profile, 'inspec.yml')
        if os.path.exists(inspec_yml):
            with open(inspec_yml, 'r') as f:
                try:
                    metadata = yaml.safe_load(f)
                    if metadata and 'supports' in metadata:
                        supports = metadata['supports']
                        if isinstance(supports, list):
                            for platform in supports:
                                if isinstance(platform, dict) and 'platform-family' in platform:
                                    if platform['platform-family'] == 'windows':
                                        return True
                                elif isinstance(platform, dict) and 'os-family' in platform:
                                    if platform['os-family'] == 'windows':
                                        return True
                except yaml.YAMLError:
                    pass
        
        # Check for Windows-specific resources in controls
        controls_dir = os.path.join(self.config.source_profile, 'controls')
        if os.path.exists(controls_dir):
            windows_resources = {'registry_key', 'security_policy', 'windows_feature', 'iis_app_pool'}
            for control_file in Path(controls_dir).glob('*.rb'):
                with open(control_file, 'r') as f:
                    content = f.read()
                    for resource in windows_resources:
                        if f'describe {resource}' in content:
                            return True
        
        return False
    
    def _create_collection_structure(self) -> str:
        """Create Ansible collection directory structure"""
        collection_path = os.path.join(
            self.config.output_dir,
            'ansible_collections',
            self.config.namespace,
            self.config.collection_name
        )
        
        dirs = [
            collection_path,
            os.path.join(collection_path, 'roles'),
            os.path.join(collection_path, 'playbooks'),
            os.path.join(collection_path, 'docs'),
            os.path.join(collection_path, 'files'),
            os.path.join(collection_path, 'meta'),
            os.path.join(collection_path, 'plugins'),
            os.path.join(collection_path, 'plugins', 'callback'),
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        # Copy callback plugin for compliance reporting
        self._install_callback_plugin(collection_path)
        
        # Create ansible.cfg for auto-enabling callback
        self._create_ansible_cfg(collection_path)
        
        return collection_path
    
    def _copy_custom_resources(self, collection_path: str, libraries_dir: str):
        """Copy custom resource files to collection"""
        dest_libraries = os.path.join(collection_path, 'files', 'libraries')
        os.makedirs(dest_libraries, exist_ok=True)
        
        for rb_file in Path(libraries_dir).glob('*.rb'):
            shutil.copy2(rb_file, dest_libraries)
    
    def _convert_control_file(self, control_file: Path, collection_path: str):
        """Convert a single InSpec control file to Ansible role"""
        with open(control_file, 'r') as f:
            content = f.read()
        
        parser = InSpecControlParser(content)
        controls = parser.parse()
        
        if not controls:
            self.result.warnings.append(f"No controls found in {control_file.name}")
            return
        
        tasks = self.task_generator.generate_tasks(controls, self.config.use_native_modules)
        
        if self.config.create_roles:
            role_name = control_file.stem.replace('-', '_')
            self._create_role(collection_path, role_name, tasks, controls)
            self.result.roles_created.append(role_name)
        
        self.result.controls_converted += len(controls)
    
    def _create_role(self, collection_path: str, role_name: str, tasks: List[Dict], controls: List[Dict]):
        """Create an Ansible role from converted tasks"""
        role_path = os.path.join(collection_path, 'roles', role_name)
        
        os.makedirs(os.path.join(role_path, 'tasks'), exist_ok=True)
        os.makedirs(os.path.join(role_path, 'meta'), exist_ok=True)
        os.makedirs(os.path.join(role_path, 'defaults'), exist_ok=True)
        
        # Write tasks
        with open(os.path.join(role_path, 'tasks', 'main.yml'), 'w') as f:
            yaml.dump(tasks, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        # Write meta
        meta = {
            'galaxy_info': {
                'author': 'ansible-inspec',
                'description': f'Compliance checks from InSpec profile',
                'license': self.config.license,
                'min_ansible_version': '2.9',
                'platforms': [
                    {'name': 'EL', 'versions': ['all']},
                    {'name': 'Ubuntu', 'versions': ['all']},
                ],
                'galaxy_tags': ['compliance', 'security', 'inspec']
            }
        }
        
        with open(os.path.join(role_path, 'meta', 'main.yml'), 'w') as f:
            yaml.dump(meta, f, default_flow_style=False)
        
        # Write defaults
        with open(os.path.join(role_path, 'defaults', 'main.yml'), 'w') as f:
            yaml.dump({'compliance_check_mode': False}, f)
    
    def _create_galaxy_yml(self, collection_path: str):
        """Create galaxy.yml"""
        galaxy_data = {
            'namespace': self.config.namespace,
            'name': self.config.collection_name,
            'version': self.config.version,
            'readme': 'README.md',
            'authors': ['Htunn Thu Thu'],
            'description': 'Compliance testing collection converted from InSpec profiles',
            'license': [self.config.license],
            'tags': ['compliance', 'security', 'inspec', 'testing'],
            'repository': 'https://github.com/Htunn/ansible-inspec',
        }
        
        with open(os.path.join(collection_path, 'galaxy.yml'), 'w') as f:
            yaml.dump(galaxy_data, f, default_flow_style=False)
    
    def _create_example_playbooks(self, collection_path: str):
        """Create example playbooks"""
        playbook = [{
            'name': 'Compliance Testing',
            'hosts': 'all',
            'become': True,
            'roles': [
                f"{self.config.namespace}.{self.config.collection_name}.{role}"
                for role in self.result.roles_created
            ],
            'tags': ['compliance']
        }]
        
        with open(os.path.join(collection_path, 'playbooks', 'compliance_check.yml'), 'w') as f:
            yaml.dump(playbook, f, default_flow_style=False, sort_keys=False)
        
        self.result.playbooks_created.append('compliance_check.yml')
    
    def _create_readme(self, collection_path: str, custom_resources: Optional[Dict] = None):
        """Create README"""
        readme = f"""# {self.config.namespace}.{self.config.collection_name}

Ansible collection converted from InSpec compliance profiles.

## Installation

```bash
ansible-galaxy collection install {self.config.namespace}.{self.config.collection_name}
```
"""
        
        if custom_resources:
            readme += f"""
## Custom Resources

This collection includes {len(custom_resources)} custom InSpec resource(s):
"""
            for name in custom_resources.keys():
                readme += f"- `{name}`\n"
            
            readme += "\nSee [docs/CUSTOM_RESOURCES.md](docs/CUSTOM_RESOURCES.md) for details.\n"
        
        readme += f"""
## Roles

"""
        for role in self.result.roles_created:
            readme += f"- `{role}`\n"
        
        readme += f"""
## Usage

```yaml
- hosts: all
  become: true
  roles:
    - {self.config.namespace}.{self.config.collection_name}.{self.result.roles_created[0] if self.result.roles_created else 'example'}
```

Or use the pre-configured playbook:

```bash
cd {self.config.namespace}/{self.config.collection_name}
ansible-playbook playbooks/compliance_check.yml -i inventory.yml
```

## Compliance Reporting

This collection automatically generates InSpec-compatible compliance reports in `.compliance-reports/` directory.

Reports are generated in JSON format matching InSpec's schema, making them compatible with:
- Chef Automate
- CI/CD pipelines
- InSpec analysis tools

Configure reporting in `ansible.cfg`:

```ini
[defaults]
callbacks_enabled = compliance_reporter
callback_result_dir = .compliance-reports

[callback_compliance_reporter]
output_format = json  # or html, junit
```

## License

{self.config.license}

## Generated by ansible-inspec

https://github.com/Htunn/ansible-inspec
"""
        
        with open(os.path.join(collection_path, 'README.md'), 'w') as f:
            f.write(readme)
    
    def _create_custom_resource_docs(self, collection_path: str, custom_resources: Dict):
        """Create custom resource documentation"""
        doc = """# Custom InSpec Resources

This collection includes custom InSpec resources that require InSpec for execution.

## Resources

"""
        
        for name, info in custom_resources.items():
            doc += f"""
### {name}

- **Class**: `{info['class_name']}`
- **File**: `{info['file']}`
- **Description**: {info['description'] or 'N/A'}
- **Platform Support**: {', '.join(info['supports']) if info['supports'] else 'All'}
- **Methods**: {', '.join(info['methods']) if info['methods'] else 'N/A'}

"""
        
        doc += """
## Requirements

Install InSpec:
```bash
# macOS
brew install chef/chef/inspec

# Linux
curl https://omnitruck.chef.io/install.sh | sudo bash -s -- -P inspec
```
"""
        
        with open(os.path.join(collection_path, 'docs', 'CUSTOM_RESOURCES.md'), 'w') as f:
            f.write(doc)
    
    def _install_callback_plugin(self, collection_path: str):
        """Install compliance reporter callback plugin"""
        plugin_dir = os.path.join(collection_path, 'plugins', 'callback')
        os.makedirs(plugin_dir, exist_ok=True)
        
        # Get path to callback plugin source
        src_plugin = os.path.join(
            os.path.dirname(__file__),
            'ansible_plugins', 'callback', 'compliance_reporter.py'
        )
        
        # Copy plugin to collection
        dest_plugin = os.path.join(plugin_dir, 'compliance_reporter.py')
        shutil.copy2(src_plugin, dest_plugin)
    
    def _create_ansible_cfg(self, collection_path: str):
        """Create ansible.cfg with auto-enabled callback plugin"""
        ansible_cfg_content = """# Ansible Configuration for Compliance Reporting
# Auto-generated by ansible-inspec

[defaults]
# Enable compliance reporter callback plugin
callbacks_enabled = compliance_reporter

# Output directory for compliance reports
# Reports will be saved in InSpec JSON schema-compatible format
callback_result_dir = .compliance-reports

[callback_compliance_reporter]
# Compliance reporter configuration
output_dir = .compliance-reports
output_format = json
"""
        
        with open(os.path.join(collection_path, 'ansible.cfg'), 'w') as f:
            f.write(ansible_cfg_content)
