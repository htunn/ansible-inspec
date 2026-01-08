#!/usr/bin/env python3
"""
Demo script showing Chef Supermarket integration with ansible-inspec

This demonstrates how to use Chef Supermarket compliance profiles
programmatically with the Python API.
"""

from ansible_inspec.inspec_adapter import InSpecProfile, InSpecRunner

def demo_supermarket_profiles():
    """Demonstrate various Chef Supermarket profiles"""
    
    print("=" * 70)
    print("Chef Supermarket Integration Demo")
    print("=" * 70)
    print()
    
    # Example 1: Linux Baseline
    print("1. DevSec Linux Baseline Profile")
    print("-" * 70)
    try:
        profile = InSpecProfile.from_supermarket('dev-sec/linux-baseline')
        print(f"✓ Loaded profile: {profile.get_name()}")
        print(f"  Source: {profile.metadata.get('source')}")
        print(f"  Path: {profile.profile_path}")
        print()
    except Exception as e:
        print(f"✗ Error loading profile: {e}")
        print()
    
    # Example 2: SSH Baseline
    print("2. DevSec SSH Baseline Profile")
    print("-" * 70)
    try:
        profile = InSpecProfile.from_supermarket('dev-sec/ssh-baseline')
        print(f"✓ Loaded profile: {profile.get_name()}")
        print(f"  Source: {profile.metadata.get('source')}")
        print(f"  Path: {profile.profile_path}")
        print()
    except Exception as e:
        print(f"✗ Error loading profile: {e}")
        print()
    
    # Example 3: CIS Docker Benchmark
    print("3. CIS Docker Benchmark Profile")
    print("-" * 70)
    try:
        profile = InSpecProfile.from_supermarket('cis-docker-benchmark')
        print(f"✓ Loaded profile: {profile.get_name()}")
        print(f"  Source: {profile.metadata.get('source')}")
        print(f"  Path: {profile.profile_path}")
        print()
    except Exception as e:
        print(f"✗ Error loading profile: {e}")
        print()
    
    # Example 4: Running a profile (requires InSpec installed)
    print("4. Example: Running SSH Baseline (local)")
    print("-" * 70)
    print("To run a Supermarket profile:")
    print()
    print("  # Using CLI:")
    print("  ansible-inspec exec dev-sec/ssh-baseline --supermarket -t ssh://user@host")
    print()
    print("  # Using Python API:")
    print("  profile = InSpecProfile.from_supermarket('dev-sec/ssh-baseline')")
    print("  runner = InSpecRunner(profile, target='ssh://user@host')")
    print("  result = runner.execute()")
    print("  print(result.summary())")
    print()
    
    # Show popular profiles
    print("5. Popular Chef Supermarket Profiles")
    print("-" * 70)
    popular_profiles = [
        ("dev-sec/linux-baseline", "OS hardening - 56 controls"),
        ("dev-sec/ssh-baseline", "SSH security - 28 controls"),
        ("dev-sec/apache-baseline", "Apache hardening - 15 controls"),
        ("dev-sec/mysql-baseline", "MySQL/MariaDB security - 20+ controls"),
        ("dev-sec/nginx-baseline", "Nginx hardening - 12 controls"),
        ("dev-sec/postgres-baseline", "PostgreSQL security - 25+ controls"),
        ("cis-docker-benchmark", "CIS Docker 1.3.0 - 100+ controls"),
        ("cis-kubernetes-benchmark", "Kubernetes security"),
    ]
    
    for profile_name, description in popular_profiles:
        print(f"  • {profile_name:30s} - {description}")
    print()
    
    print("=" * 70)
    print("For more information:")
    print("  • Chef Supermarket: https://supermarket.chef.io")
    print("  • Documentation: docs/CHEF-SUPERMARKET.md")
    print("  • Repository: https://github.com/Htunn/ansible-inspec")
    print("=" * 70)

if __name__ == '__main__':
    demo_supermarket_profiles()
