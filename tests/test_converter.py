"""Tests for InSpec profile to Ansible collection converter."""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

from ansible_inspec.converter import (
    CustomResourceParser,
    InSpecControlParser,
    AnsibleTaskGenerator,
    ProfileConverter,
    ConversionConfig,
    sanitize_variable_name,
)


class TestSanitizeVariableName:
    """Test sanitize_variable_name functionality."""
    
    def test_simple_alphanumeric(self):
        """Test sanitization of simple alphanumeric IDs."""
        assert sanitize_variable_name("test123") == "test123"
        assert sanitize_variable_name("abc_def") == "abc_def"
    
    def test_dots_in_version_numbers(self):
        """Test sanitization of version numbers with dots."""
        assert sanitize_variable_name("test-1.2.3") == "test_1_2_3"
        assert sanitize_variable_name("2.2.27") == "inspec_2_2_27"
    
    def test_spaces_and_special_chars(self):
        """Test sanitization of spaces and special characters."""
        assert sanitize_variable_name("2.2.27 (L1) Ensure Enable computer and user accounts") == "inspec_2_2_27_L1_Ensure_Enable_computer_and_user_accounts"
        assert sanitize_variable_name("test (with) parentheses") == "test_with_parentheses"
        assert sanitize_variable_name("test-with-dashes") == "test_with_dashes"
    
    def test_starts_with_digit(self):
        """Test sanitization when ID starts with a digit."""
        assert sanitize_variable_name("123test") == "inspec_123test"
        assert sanitize_variable_name("1.2.3.test") == "inspec_1_2_3_test"
    
    def test_consecutive_underscores(self):
        """Test removal of consecutive underscores."""
        assert sanitize_variable_name("test___multiple___underscores") == "test_multiple_underscores"
        assert sanitize_variable_name("test...dots") == "test_dots"
    
    def test_trailing_leading_underscores(self):
        """Test removal of trailing and leading underscores."""
        assert sanitize_variable_name("_test_") == "test"
        assert sanitize_variable_name("test...") == "test"
    
    def test_complex_cis_benchmark_ids(self):
        """Test sanitization of complex CIS benchmark control IDs."""
        # Real-world example from bug report
        control_id = "2.2.27 (L1) Ensure Enable computer and user accounts to be trusted for delegation is set to Administrators (DC only)"
        result = sanitize_variable_name(control_id)
        
        # Should be a valid Ansible variable name
        assert result.startswith("inspec_2_2_27_L1_")
        assert " " not in result
        assert "(" not in result
        assert ")" not in result
        assert "." not in result[10:]  # After "inspec_2_2_27"
        
        # Should start with letter or underscore
        assert result[0].isalpha() or result[0] == "_"
        
        # Should only contain alphanumeric and underscores
        assert all(c.isalnum() or c == "_" for c in result)
    
    def test_empty_or_invalid_input(self):
        """Test sanitization of empty or completely invalid input."""
        # Empty string should return default
        assert sanitize_variable_name("") == "inspec_control"
        
        # Only special characters should return default or sanitized version
        result = sanitize_variable_name("...")
        assert result != ""
        assert all(c.isalnum() or c == "_" for c in result)
    
    def test_preserves_existing_valid_names(self):
        """Test that already valid names are preserved."""
        assert sanitize_variable_name("valid_control_name") == "valid_control_name"
        assert sanitize_variable_name("Control123") == "Control123"


@pytest.fixture
def temp_profile_dir():
    """Create a temporary InSpec profile for testing."""
    temp_dir = tempfile.mkdtemp()
    profile_dir = Path(temp_dir) / "test-profile"
    profile_dir.mkdir()
    
    # Create inspec.yml
    (profile_dir / "inspec.yml").write_text("""
name: test-profile
title: Test Profile
version: 1.0.0
summary: Test InSpec Profile
    """)
    
    # Create controls directory
    controls_dir = profile_dir / "controls"
    controls_dir.mkdir()
    
    # Create sample control file
    (controls_dir / "example.rb").write_text("""
control 'test-1' do
  impact 1.0
  title 'Test Control'
  desc 'Test description'
  
  describe file('/etc/passwd') do
    it { should exist }
    its('mode') { should cmp '0644' }
  end
end
    """)
    
    # Create libraries directory
    libraries_dir = profile_dir / "libraries"
    libraries_dir.mkdir()
    
    # Create custom resource
    (libraries_dir / "custom_resource.rb").write_text("""
class CustomResource < Inspec.resource(1)
  name 'custom_resource'
  desc 'Custom resource for testing'
  
  def initialize(path)
    @path = path
  end
  
  def exists?
    inspec.file(@path).exist?
  end
end
    """)
    
    yield profile_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


class TestCustomResourceParser:
    """Test CustomResourceParser functionality."""
    
    def test_parse_custom_resource(self, temp_profile_dir):
        """Test parsing custom resource file."""
        libraries_dir = temp_profile_dir / "libraries"
        parser = CustomResourceParser(str(libraries_dir))
        
        resources = parser.parse()
        
        assert len(resources) >= 1
        # Check that custom_resource was found
        assert 'custom_resource' in resources or 'CustomResource' in resources
    
    def test_parse_libraries_directory(self, temp_profile_dir):
        """Test parsing entire libraries directory."""
        libraries_dir = temp_profile_dir / "libraries"
        parser = CustomResourceParser(str(libraries_dir))
        
        resources = parser.parse()
        
        assert len(resources) >= 1


class TestInSpecControlParser:
    """Test InSpecControlParser functionality."""
    
    def test_parse_simple_control(self):
        """Test parsing a simple control."""
        control_code = """
control 'test-1' do
  impact 1.0
  title 'Test Control'
  desc 'Test description'
  
  describe file('/etc/passwd') do
    it { should exist }
  end
end
        """
        parser = InSpecControlParser(control_code)
        
        controls = parser.parse()
        
        assert len(controls) == 1
        assert controls[0]['id'] == 'test-1'
        assert controls[0]['impact'] == 1.0
        assert controls[0]['title'] == 'Test Control'
        assert len(controls[0]['describes']) >= 1
    
    def test_parse_control_with_quotes_in_id(self):
        """Test parsing control IDs containing single quotes (Bug #1 regression test)."""
        # Real-world CIS benchmark control ID with embedded quotes
        control_code = '''
control "1.1.1 (L1) Ensure 'Enforce password history' is set to '7 password(s)'" do
  impact 1.0
  title "Enforce password history"
  desc "This setting determines the number of unique new passwords"
  
  describe file('/etc/security/pwquality.conf') do
    it { should exist }
  end
end
        '''
        parser = InSpecControlParser(control_code)
        
        controls = parser.parse()
        
        # Should successfully parse the control
        assert len(controls) == 1
        assert controls[0]['id'] == "1.1.1 (L1) Ensure 'Enforce password history' is set to '7 password(s)'"
        assert controls[0]['impact'] == 1.0
        assert controls[0]['title'] == 'Enforce password history'
    
    def test_parse_control_with_double_quotes_in_single_quoted_id(self):
        """Test parsing control IDs with double quotes inside single-quoted strings."""
        control_code = '''
control 'test-id-with-"double"-quotes' do
  impact 0.5
  title 'Test'
  
  describe file('/test') do
    it { should exist }
  end
end
        '''
        parser = InSpecControlParser(control_code)
        
        controls = parser.parse()
        
        assert len(controls) == 1
        assert controls[0]['id'] == 'test-id-with-"double"-quotes'
    
    def test_parse_multiple_controls_with_quotes(self):
        """Test parsing multiple controls with quotes in IDs."""
        control_code = '''
control "2.2.27 (L1) Ensure 'Enable computer' is set" do
  impact 1.0
  title "Test 1"
  
  describe file('/etc/test1') do
    it { should exist }
  end
end

control "2.2.61 Recovery console: Allow 'floppy copy'" do
  impact 0.8
  title "Test 2"
  
  describe file('/etc/test2') do
    it { should exist }
  end
end

control "simple-id" do
  impact 0.5
  title "Test 3"
  
  describe file('/etc/test3') do
    it { should exist }
  end
end
        '''
        parser = InSpecControlParser(control_code)
        
        controls = parser.parse()
        
        # All 3 controls should be parsed successfully
        assert len(controls) == 3
        assert controls[0]['id'] == "2.2.27 (L1) Ensure 'Enable computer' is set"
        assert controls[1]['id'] == "2.2.61 Recovery console: Allow 'floppy copy'"
        assert controls[2]['id'] == "simple-id"
    
    def test_parse_control_file(self, temp_profile_dir):
        """Test parsing control from file."""
        control_file = temp_profile_dir / "controls" / "example.rb"
        
        with open(control_file) as f:
            content = f.read()
        
        parser = InSpecControlParser(content)
        controls = parser.parse()
        
        assert len(controls) == 1
        assert controls[0]['id'] == 'test-1'


class TestAnsibleTaskGenerator:
    """Test AnsibleTaskGenerator functionality."""
    
    def test_generate_file_task(self):
        """Test generating Ansible task for file resource."""
        generator = AnsibleTaskGenerator({})
        control = {
            'id': 'test-1',
            'title': 'Test',
            'describes': [{
                'resource': 'file',
                'argument': '/etc/passwd',
                'tests': [
                    {'type': 'it', 'matcher': 'exist', 'negated': False},
                    {'type': 'its', 'property': 'mode', 'matcher': 'cmp', 'value': '0644', 'negated': False},
                ]
            }]
        }
        
        tasks = generator.generate_tasks([control], use_native=True)
        
        assert len(tasks) >= 1
        # Should generate some tasks
        assert isinstance(tasks, list)
    
    def test_generate_service_task(self):
        """Test generating Ansible task for service resource."""
        generator = AnsibleTaskGenerator({})
        control = {
            'id': 'test-1',
            'title': 'Test',
            'describes': [{
                'resource': 'service',
                'argument': 'sshd',
                'tests': [
                    {'type': 'it', 'matcher': 'be_running', 'negated': False},
                ]
            }]
        }
        
        tasks = generator.generate_tasks([control], use_native=True)
        
        assert len(tasks) >= 1
        assert isinstance(tasks, list)
    
    def test_generate_custom_resource_task(self):
        """Test generating InSpec wrapper for custom resource."""
        custom_resources = {'custom_resource': {'name': 'custom_resource'}}
        generator = AnsibleTaskGenerator(custom_resources)
        control = {
            'id': 'test-1',
            'title': 'Test',
            'describes': [{
                'resource': 'custom_resource',
                'argument': '/some/path',
                'tests': [
                    {'type': 'it', 'matcher': 'exist', 'negated': False},
                ]
            }]
        }
        
        tasks = generator.generate_tasks([control], use_native=False)
        
        assert len(tasks) >= 1
        assert isinstance(tasks, list)
    
    def test_windows_profile_uses_win_shell(self):
        """Test that Windows profiles use ansible.windows.win_shell module (Bug #2 fix)."""
        custom_resources = {'custom_resource': {'name': 'custom_resource'}}
        generator = AnsibleTaskGenerator(custom_resources, is_windows_profile=True)
        
        control = {
            'id': 'test-windows-1',
            'title': 'Windows Test',
            'describes': [{
                'resource': 'custom_resource',
                'argument': '/test/path',
                'tests': [
                    {'type': 'it', 'matcher': 'exist', 'negated': False},
                ]
            }]
        }
        
        tasks = generator.generate_tasks([control], use_native=False)
        
        assert len(tasks) >= 1
        task_block = tasks[0]
        assert 'block' in task_block
        
        # Check the actual task uses win_shell
        actual_task = task_block['block'][0]
        assert 'ansible.windows.win_shell' in actual_task
        assert 'ansible.builtin.shell' not in actual_task
    
    def test_linux_profile_uses_builtin_shell(self):
        """Test that Linux profiles use ansible.builtin.shell module."""
        custom_resources = {'custom_resource': {'name': 'custom_resource'}}
        generator = AnsibleTaskGenerator(custom_resources, is_windows_profile=False)
        
        control = {
            'id': 'test-linux-1',
            'title': 'Linux Test',
            'describes': [{
                'resource': 'custom_resource',
                'argument': '/test/path',
                'tests': [
                    {'type': 'it', 'matcher': 'exist', 'negated': False},
                ]
            }]
        }
        
        tasks = generator.generate_tasks([control], use_native=False)
        
        assert len(tasks) >= 1
        task_block = tasks[0]
        assert 'block' in task_block
        
        # Check the actual task uses builtin.shell
        actual_task = task_block['block'][0]
        assert 'ansible.builtin.shell' in actual_task
        assert 'ansible.windows.win_shell' not in actual_task
    
    def test_windows_fallback_task_uses_win_shell(self):
        """Test that Windows fallback tasks use win_shell for unsupported resources."""
        generator = AnsibleTaskGenerator({}, is_windows_profile=True)
        
        control = {
            'id': 'test-fallback-1',
            'title': 'Fallback Test',
            'describes': [{
                'resource': 'unsupported_resource',
                'argument': 'test',
                'tests': [
                    {'type': 'it', 'matcher': 'exist', 'negated': False},
                ]
            }]
        }
        
        tasks = generator.generate_tasks([control], use_native=False)
        
        assert len(tasks) >= 1
        task_block = tasks[0]
        actual_task = task_block['block'][0]
        
        # Verify win_shell is used for Windows
        assert 'ansible.windows.win_shell' in actual_task
    
    def test_windows_module_uses_freeform_syntax(self):
        """Test that Windows tasks use free-form syntax (Bug #3 fix)."""
        generator = AnsibleTaskGenerator({}, is_windows_profile=True)
        
        control = {
            'id': 'test-syntax-1',
            'title': 'Syntax Test',
            'describes': [{
                'resource': 'unsupported_resource',
                'argument': 'test',
                'tests': [
                    {'type': 'it', 'matcher': 'exist', 'negated': False},
                ]
            }]
        }
        
        tasks = generator.generate_tasks([control], use_native=False)
        
        assert len(tasks) >= 1
        task_block = tasks[0]
        actual_task = task_block['block'][0]
        
        # Verify win_shell uses free-form syntax (string value, not dict)
        assert 'ansible.windows.win_shell' in actual_task
        win_shell_value = actual_task['ansible.windows.win_shell']
        assert isinstance(win_shell_value, str), "win_shell must use free-form syntax (string)"
        assert win_shell_value.startswith('inspec exec'), "Command should start with inspec exec"
        
        # Verify stdin is in args block, not in module parameter
        assert 'args' in actual_task, "Windows module parameters must be in 'args' block"
        assert 'stdin' in actual_task['args'], "stdin must be in 'args' block for Windows"
    
    def test_linux_module_uses_structured_syntax(self):
        """Test that Linux tasks use structured syntax with cmd parameter."""
        generator = AnsibleTaskGenerator({}, is_windows_profile=False)
        
        control = {
            'id': 'test-linux-syntax-1',
            'title': 'Linux Syntax Test',
            'describes': [{
                'resource': 'unsupported_resource',
                'argument': 'test',
                'tests': [
                    {'type': 'it', 'matcher': 'exist', 'negated': False},
                ]
            }]
        }
        
        tasks = generator.generate_tasks([control], use_native=False)
        
        assert len(tasks) >= 1
        task_block = tasks[0]
        actual_task = task_block['block'][0]
        
        # Verify builtin.shell uses structured syntax (dict with cmd/stdin)
        assert 'ansible.builtin.shell' in actual_task
        shell_value = actual_task['ansible.builtin.shell']
        assert isinstance(shell_value, dict), "Linux shell can use structured syntax (dict)"
        assert 'cmd' in shell_value, "Structured syntax should have 'cmd' key"
        assert 'stdin' in shell_value, "Structured syntax should have 'stdin' key"
    
    def test_windows_control_id_quoting(self):
        """Test that Windows tasks quote control IDs with special characters (Bug #4 fix)."""
        generator = AnsibleTaskGenerator({}, is_windows_profile=True)
        
        # CIS benchmark control ID with spaces, parentheses, and quotes
        control = {
            'id': "1.1.2 (L1) Ensure 'Maximum password age' is set to '365 days'",
            'title': 'Password Age Test',
            'describes': [{
                'resource': 'security_policy',
                'argument': '',
                'tests': [
                    {'type': 'its', 'property': 'MaximumPasswordAge', 'matcher': 'cmp', 'value': '365', 'negated': False},
                ]
            }]
        }
        
        tasks = generator.generate_tasks([control], use_native=False)
        
        assert len(tasks) >= 1
        task_block = tasks[0]
        actual_task = task_block['block'][0]
        
        # Verify command quotes the control ID
        assert 'ansible.windows.win_shell' in actual_task
        cmd = actual_task['ansible.windows.win_shell']
        
        # Control ID should be wrapped in double quotes
        assert '--controls "' in cmd, "Control ID must be quoted for PowerShell"
        assert '1.1.2 (L1)' in cmd, "Control ID content should be in command"
        
        # Verify backtick escaping for any double quotes in the ID (if present)
        if '"' in control['id']:
            # If original ID has quotes, they should be escaped with backtick
            assert '`"' in cmd or control['id'].count('"') == 0
    
    def test_linux_control_id_quoting(self):
        """Test that Linux tasks quote control IDs with special characters."""
        generator = AnsibleTaskGenerator({}, is_windows_profile=False)
        
        # Control ID with special characters
        control = {
            'id': "test-1.2.3 (L1) Ensure 'setting' is configured",
            'title': 'Linux Test',
            'describes': [{
                'resource': 'file',
                'argument': '/etc/test',
                'tests': [
                    {'type': 'it', 'matcher': 'exist', 'negated': False},
                ]
            }]
        }
        
        tasks = generator.generate_tasks([control], use_native=False)
        
        assert len(tasks) >= 1
        task_block = tasks[0]
        actual_task = task_block['block'][0]
        
        # Verify command quotes the control ID
        assert 'ansible.builtin.shell' in actual_task
        shell_dict = actual_task['ansible.builtin.shell']
        cmd = shell_dict['cmd']
        
        # Control ID should be wrapped in double quotes
        assert '--controls "' in cmd, "Control ID must be quoted for shell safety"
        assert 'test-1.2.3 (L1)' in cmd, "Control ID content should be in command"
    
    def test_sanitize_variable_names_in_tasks(self):
        """Test that variable names are sanitized in generated tasks."""
        generator = AnsibleTaskGenerator({})
        
        # Control with special characters in ID (like from CIS benchmarks)
        control = {
            'id': '2.2.27 (L1) Ensure Enable computer',
            'title': 'Test Control',
            'describes': [{
                'resource': 'unknown_resource',  # Force fallback
                'argument': 'test',
                'tests': [
                    {'type': 'it', 'matcher': 'exist', 'negated': False},
                ]
            }]
        }
        
        tasks = generator.generate_tasks([control], use_native=False)
        
        assert len(tasks) >= 1
        assert isinstance(tasks, list)
    
    def test_sanitize_variable_names_in_tasks(self):
        """Test that variable names are sanitized in generated tasks."""
        generator = AnsibleTaskGenerator({})
        
        # Control with special characters in ID (like from CIS benchmarks)
        control = {
            'id': '2.2.27 (L1) Ensure Enable computer',
            'title': 'Test Control',
            'describes': [{
                'resource': 'unknown_resource',  # Force fallback
                'argument': 'test',
                'tests': [
                    {'type': 'it', 'matcher': 'exist', 'negated': False},
                ]
            }]
        }
        
        tasks = generator.generate_tasks([control], use_native=False)
        
        # Extract the actual task (should be inside a block)
        assert len(tasks) >= 1
        task_block = tasks[0]
        assert 'block' in task_block
        
        # Find the task with register
        actual_task = task_block['block'][0]
        
        # Verify the variable name is sanitized
        assert 'register' in actual_task
        var_name = actual_task['register']
        
        # Should be a valid Ansible variable name
        assert " " not in var_name
        assert "(" not in var_name
        assert ")" not in var_name
        assert "." not in var_name or var_name.startswith("inspec_")
        
        # Should match the expected sanitized format
        expected_var_name = "inspec_2_2_27_L1_Ensure_Enable_computer_result"
        assert var_name == expected_var_name
        
        # Verify failed_when also uses sanitized name
        assert 'failed_when' in actual_task
        assert expected_var_name in actual_task['failed_when']


class TestProfileConverter:
    """Test ProfileConverter functionality."""
    
    def test_detect_windows_profile_from_metadata(self, temp_output_dir):
        """Test Windows profile detection from inspec.yml metadata."""
        temp_dir = tempfile.mkdtemp()
        profile_dir = Path(temp_dir) / "windows-profile"
        profile_dir.mkdir()
        
        # Create Windows inspec.yml
        (profile_dir / "inspec.yml").write_text("""
name: windows-profile
title: Windows Profile
version: 1.0.0
supports:
  - platform-family: windows
    """)
        
        # Create controls directory
        controls_dir = profile_dir / "controls"
        controls_dir.mkdir()
        (controls_dir / "test.rb").write_text("""
control 'test-1' do
  describe file('C:\\test') do
    it { should exist }
  end
end
        """)
        
        config = ConversionConfig(
            source_profile=str(profile_dir),
            output_dir=str(temp_output_dir),
            namespace='test',
            collection_name='windows_test',
        )
        
        converter = ProfileConverter(config)
        is_windows = converter._detect_windows_profile()
        
        assert is_windows is True
        
        shutil.rmtree(temp_dir)
    
    def test_detect_windows_profile_from_registry_key(self, temp_output_dir):
        """Test Windows profile detection from registry_key resource usage."""
        temp_dir = tempfile.mkdtemp()
        profile_dir = Path(temp_dir) / "windows-profile"
        profile_dir.mkdir()
        
        # Create inspec.yml without platform
        (profile_dir / "inspec.yml").write_text("""
name: windows-profile
title: Windows Profile
version: 1.0.0
        """)
        
        # Create controls with Windows-specific resource
        controls_dir = profile_dir / "controls"
        controls_dir.mkdir()
        (controls_dir / "test.rb").write_text("""
control 'test-1' do
  describe registry_key('HKEY_LOCAL_MACHINE\\\\System') do
    it { should exist }
  end
end
        """)
        
        config = ConversionConfig(
            source_profile=str(profile_dir),
            output_dir=str(temp_output_dir),
            namespace='test',
            collection_name='windows_test',
        )
        
        converter = ProfileConverter(config)
        is_windows = converter._detect_windows_profile()
        
        assert is_windows is True
        
        shutil.rmtree(temp_dir)
    
    def test_detect_linux_profile(self, temp_profile_dir, temp_output_dir):
        """Test that Linux profiles are not detected as Windows."""
        config = ConversionConfig(
            source_profile=str(temp_profile_dir),
            output_dir=str(temp_output_dir),
            namespace='test',
            collection_name='linux_test',
        )
        
        converter = ProfileConverter(config)
        is_windows = converter._detect_windows_profile()
        
        assert is_windows is False
    
    def test_convert_simple_profile(self, temp_profile_dir, temp_output_dir):
        """Test converting a simple InSpec profile."""
        config = ConversionConfig(
            source_profile=str(temp_profile_dir),
            output_dir=str(temp_output_dir),
            namespace='test',
            collection_name='test_profile',
        )
        
        converter = ProfileConverter(config)
        result = converter.convert()
        
        assert result.success
        assert result.controls_converted >= 1
        assert len(result.roles_created) >= 1
        assert result.custom_resources_found >= 1
        
        # Check collection structure
        collection_path = temp_output_dir / "ansible_collections" / "test" / "test_profile"
        assert collection_path.exists()
        assert (collection_path / "galaxy.yml").exists()
        assert (collection_path / "roles").exists()
        assert (collection_path / "README.md").exists()
    
    def test_convert_with_custom_resources(self, temp_profile_dir, temp_output_dir):
        """Test converting profile with custom resources."""
        config = ConversionConfig(
            source_profile=str(temp_profile_dir),
            output_dir=str(temp_output_dir),
            namespace='test',
            collection_name='test_profile',
        )
        
        converter = ProfileConverter(config)
        result = converter.convert()
        
        assert result.success
        assert result.custom_resources_found >= 1
        
        # Check custom resources copied
        collection_path = temp_output_dir / "ansible_collections" / "test" / "test_profile"
        libraries_path = collection_path / "files" / "libraries"
        assert libraries_path.exists()
        assert (libraries_path / "custom_resource.rb").exists()
    
    def test_convert_creates_galaxy_yml(self, temp_profile_dir, temp_output_dir):
        """Test that galaxy.yml is created with correct metadata."""
        config = ConversionConfig(
            source_profile=str(temp_profile_dir),
            output_dir=str(temp_output_dir),
            namespace='test',
            collection_name='test_profile',
        )
        
        converter = ProfileConverter(config)
        converter.convert()
        
        collection_path = temp_output_dir / "ansible_collections" / "test" / "test_profile"
        galaxy_yml = collection_path / "galaxy.yml"
        
        assert galaxy_yml.exists()
        
        import yaml
        with open(galaxy_yml) as f:
            galaxy = yaml.safe_load(f)
        
        assert galaxy['namespace'] == 'test'
        assert galaxy['name'] == 'test_profile'
        assert galaxy['version'] == '1.0.0'
        assert 'description' in galaxy
    
    def test_convert_creates_roles(self, temp_profile_dir, temp_output_dir):
        """Test that roles are created from controls."""
        config = ConversionConfig(
            source_profile=str(temp_profile_dir),
            output_dir=str(temp_output_dir),
            namespace='test',
            collection_name='test_profile',
            create_roles=True,
        )
        
        converter = ProfileConverter(config)
        converter.convert()
        
        collection_path = temp_output_dir / "ansible_collections" / "test" / "test_profile"
        roles_path = collection_path / "roles"
        
        assert roles_path.exists()
        # Should have at least one role
        roles = list(roles_path.iterdir())
        assert len(roles) >= 1
        
        # Check role structure
        role_path = roles[0]
        assert (role_path / "tasks" / "main.yml").exists()
    
    def test_convert_creates_playbooks(self, temp_profile_dir, temp_output_dir):
        """Test that playbooks are created."""
        config = ConversionConfig(
            source_profile=str(temp_profile_dir),
            output_dir=str(temp_output_dir),
            namespace='test',
            collection_name='test_profile',
            create_playbooks=True,
        )
        
        converter = ProfileConverter(config)
        converter.convert()
        
        collection_path = temp_output_dir / "ansible_collections" / "test" / "test_profile"
        playbooks_path = collection_path / "playbooks"
        
        assert playbooks_path.exists()
        assert (playbooks_path / "compliance_check.yml").exists()
    
    def test_convert_native_only_mode(self, temp_profile_dir, temp_output_dir):
        """Test conversion in native-only mode."""
        config = ConversionConfig(
            source_profile=str(temp_profile_dir),
            output_dir=str(temp_output_dir),
            namespace='test',
            collection_name='test_profile',
            use_native_modules=True,
        )
        
        converter = ProfileConverter(config)
        result = converter.convert()
        
        assert result.success
        # Should have warnings about custom resources
        assert len(result.warnings) >= 1


def test_conversion_config_defaults():
    """Test ConversionConfig default values."""
    config = ConversionConfig(
        source_profile='/path/to/profile',
        output_dir='./collections'
    )
    
    assert config.output_dir == './collections'
    assert config.namespace == 'compliance'
    assert config.collection_name == 'inspec_profiles'
    assert config.use_native_modules is True
    assert config.create_roles is True
    assert config.create_playbooks is True


def test_conversion_config_validation():
    """Test ConversionConfig validation."""
    # Should not raise for valid path (even if doesn't exist, validation happens later)
    config = ConversionConfig(
        source_profile='/some/path',
        output_dir='./output'
    )
    assert config.source_profile == '/some/path'
    
    # Test namespace validation
    config = ConversionConfig(
        source_profile='/path',
        output_dir='./output',
        namespace='valid_namespace'
    )
    assert config.namespace == 'valid_namespace'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
