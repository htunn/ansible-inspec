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
)


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


class TestProfileConverter:
    """Test ProfileConverter functionality."""
    
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
