#!/usr/bin/env python3
"""
Integration test for InSpec profile to Ansible collection conversion.

This script demonstrates the complete conversion workflow:
1. Create a sample InSpec profile with custom resources
2. Convert it to an Ansible collection
3. Verify the collection structure
4. Build the collection with ansible-galaxy
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from ansible_inspec.converter import ProfileConverter, ConversionConfig


def create_sample_profile(base_dir: Path) -> Path:
    """Create a sample InSpec profile for testing."""
    print("📝 Creating sample InSpec profile...")
    
    profile_dir = base_dir / "sample-profile"
    profile_dir.mkdir()
    
    # Create inspec.yml
    (profile_dir / "inspec.yml").write_text("""name: sample-profile
title: Sample Compliance Profile
version: 1.0.0
maintainer: Ansible InSpec Team
copyright: Ansible InSpec Team
license: Apache-2.0
summary: Sample profile demonstrating conversion to Ansible collection
supports:
  - platform: linux
""")
    
    # Create controls directory
    controls_dir = profile_dir / "controls"
    controls_dir.mkdir()
    
    # Create system controls
    (controls_dir / "system.rb").write_text("""control 'system-1' do
  impact 1.0
  title 'Ensure required packages are installed'
  desc 'System must have essential packages'
  
  describe package('openssh-server') do
    it { should be_installed }
  end
  
  describe service('sshd') do
    it { should be_running }
    it { should be_enabled }
  end
end

control 'system-2' do
  impact 0.8
  title 'Ensure critical files have correct permissions'
  desc 'System files must be properly secured'
  
  describe file('/etc/passwd') do
    it { should exist }
    its('mode') { should cmp '0644' }
    its('owner') { should eq 'root' }
  end
  
  describe file('/etc/shadow') do
    it { should exist }
    its('mode') { should cmp '0000' }
    its('owner') { should eq 'root' }
  end
end
""")
    
    # Create libraries directory
    libraries_dir = profile_dir / "libraries"
    libraries_dir.mkdir()
    
    # Create custom resource
    (libraries_dir / "app_config.rb").write_text("""# Custom resource for application configuration
class AppConfig < Inspec.resource(1)
  name 'app_config'
  desc 'Checks application configuration files'
  example <<~EXAMPLE
    describe app_config('/etc/myapp/config.yml') do
      its('setting.timeout') { should cmp >= 30 }
    end
  EXAMPLE
  
  supports platform: 'linux'
  
  def initialize(path)
    @path = path
    @config = read_config
  end
  
  def setting(key)
    @config.dig(*key.split('.'))
  end
  
  def exists?
    inspec.file(@path).exist?
  end
  
  def valid?
    exists? && !@config.nil?
  end
  
  private
  
  def read_config
    return nil unless inspec.file(@path).exist?
    
    content = inspec.file(@path).content
    require 'yaml'
    YAML.load(content) rescue nil
  end
end
""")
    
    # Create control using custom resource
    (controls_dir / "application.rb").write_text("""control 'app-1' do
  impact 0.8
  title 'Ensure application is configured correctly'
  desc 'Application configuration must meet requirements'
  
  describe app_config('/etc/myapp/config.yml') do
    it { should exist }
    it { should be_valid }
    its('setting.timeout') { should cmp >= 30 }
    its('setting.debug') { should eq false }
    its('setting.log_level') { should eq 'info' }
  end
end
""")
    
    print(f"  ✓ Created profile at: {profile_dir}")
    print(f"  ✓ Controls: system.rb, application.rb")
    print(f"  ✓ Custom resources: app_config.rb")
    print()
    
    return profile_dir


def convert_profile(profile_dir: Path, output_dir: Path):
    """Convert InSpec profile to Ansible collection."""
    print("🔄 Converting InSpec profile to Ansible collection...")
    
    config = ConversionConfig(
        source_profile=str(profile_dir),
        output_dir=str(output_dir),
        namespace='example',
        collection_name='sample_compliance',
    )
    
    converter = ProfileConverter(config)
    result = converter.convert()
    
    if not result.success:
        print("  ❌ Conversion failed!")
        for error in result.errors:
            print(f"     Error: {error}")
        return None
    
    print(f"  ✓ Conversion successful!")
    print(f"  ✓ Controls converted: {result.controls_converted}")
    print(f"  ✓ Roles created: {result.roles_created}")
    print(f"  ✓ Custom resources: {result.custom_resources_found}")
    
    if result.warnings:
        print("\n  ⚠️  Warnings:")
        for warning in result.warnings:
            print(f"     - {warning}")
    
    print()
    return result


def verify_collection_structure(output_dir: Path):
    """Verify the generated collection structure."""
    print("🔍 Verifying collection structure...")
    
    collection_path = output_dir / "ansible_collections" / "example" / "sample_compliance"
    
    checks = [
        ("galaxy.yml", collection_path / "galaxy.yml"),
        ("README.md", collection_path / "README.md"),
        ("roles/", collection_path / "roles"),
        ("playbooks/", collection_path / "playbooks"),
        ("files/libraries/", collection_path / "files" / "libraries"),
        ("docs/", collection_path / "docs"),
    ]
    
    all_passed = True
    for name, path in checks:
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {name}")
        if not exists:
            all_passed = False
    
    print()
    
    if all_passed:
        print("  ✓ All structure checks passed!")
    else:
        print("  ✗ Some structure checks failed!")
    
    print()
    return all_passed, collection_path


def show_collection_contents(collection_path: Path):
    """Show key contents of the generated collection."""
    print("📄 Collection contents:")
    print()
    
    # Show roles
    roles_dir = collection_path / "roles"
    if roles_dir.exists():
        print("  Roles:")
        for role in sorted(roles_dir.iterdir()):
            if role.is_dir():
                tasks_file = role / "tasks" / "main.yml"
                if tasks_file.exists():
                    with open(tasks_file) as f:
                        task_count = f.read().count('- name:')
                    print(f"    - {role.name} ({task_count} tasks)")
        print()
    
    # Show playbooks
    playbooks_dir = collection_path / "playbooks"
    if playbooks_dir.exists():
        print("  Playbooks:")
        for playbook in sorted(playbooks_dir.glob("*.yml")):
            print(f"    - {playbook.name}")
        print()
    
    # Show custom resources
    libraries_dir = collection_path / "files" / "libraries"
    if libraries_dir.exists() and list(libraries_dir.iterdir()):
        print("  Custom Resources:")
        for resource in sorted(libraries_dir.glob("*.rb")):
            print(f"    - {resource.name}")
        print()
    
    # Show galaxy.yml
    galaxy_file = collection_path / "galaxy.yml"
    if galaxy_file.exists():
        print("  Galaxy Metadata:")
        import yaml
        with open(galaxy_file) as f:
            galaxy = yaml.safe_load(f)
        print(f"    Namespace: {galaxy.get('namespace')}")
        print(f"    Name: {galaxy.get('name')}")
        print(f"    Version: {galaxy.get('version')}")
        print(f"    Description: {galaxy.get('description', '')[:60]}...")
        print()


def build_collection(collection_path: Path):
    """Build the collection tarball."""
    print("📦 Building collection tarball...")
    
    import subprocess
    
    try:
        result = subprocess.run(
            ['ansible-galaxy', 'collection', 'build'],
            cwd=str(collection_path),
            capture_output=True,
            text=True,
            check=True
        )
        
        # Find the built tarball
        tarballs = list(collection_path.glob("*.tar.gz"))
        if tarballs:
            tarball = tarballs[0]
            size = tarball.stat().st_size
            print(f"  ✓ Collection built successfully!")
            print(f"  ✓ File: {tarball.name}")
            print(f"  ✓ Size: {size:,} bytes")
            print()
            return tarball
        else:
            print("  ✗ No tarball found after build")
            return None
    
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Build failed: {e.stderr}")
        return None
    except FileNotFoundError:
        print("  ⚠️  ansible-galaxy not found - skipping build")
        print("     Install with: pip install ansible")
        return None


def show_usage_instructions(collection_path: Path, tarball: Path = None):
    """Show instructions for using the collection."""
    print("📖 Usage Instructions:")
    print()
    
    if tarball:
        print("  1. Install the collection:")
        print(f"     ansible-galaxy collection install {tarball}")
        print()
    
    print("  2. Use in a playbook:")
    print("     ```yaml")
    print("     - name: Run compliance checks")
    print("       hosts: all")
    print("       become: true")
    print("       roles:")
    print("         - example.sample_compliance.system")
    print("         - example.sample_compliance.application")
    print("     ```")
    print()
    
    print("  3. Or use the included playbook:")
    print("     ansible-playbook example.sample_compliance.compliance_check -i inventory.yml")
    print()
    
    print("  4. List installed collections:")
    print("     ansible-galaxy collection list | grep example")
    print()


def main():
    """Run the integration test."""
    print()
    print("=" * 70)
    print("InSpec Profile to Ansible Collection - Integration Test")
    print("=" * 70)
    print()
    
    # Create temporary directories
    temp_dir = Path(tempfile.mkdtemp())
    output_dir = temp_dir / "output"
    output_dir.mkdir()
    
    try:
        # Create sample profile
        profile_dir = create_sample_profile(temp_dir)
        
        # Convert profile
        result = convert_profile(profile_dir, output_dir)
        if not result:
            return 1
        
        # Verify structure
        verified, collection_path = verify_collection_structure(output_dir)
        if not verified:
            return 1
        
        # Show contents
        show_collection_contents(collection_path)
        
        # Build collection
        tarball = build_collection(collection_path)
        
        # Show usage
        show_usage_instructions(collection_path, tarball)
        
        print("=" * 70)
        print("✅ Integration test completed successfully!")
        print("=" * 70)
        print()
        print(f"Collection location: {collection_path}")
        if tarball:
            print(f"Collection tarball: {tarball}")
        print()
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup
        if temp_dir.exists():
            print(f"Cleaning up: {temp_dir}")
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    sys.exit(main())
