"""
CLI module for ansible-inspec

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import argparse
import sys
import os
from ansible_inspec import __version__, UPSTREAM_PROJECTS


def print_version():
    """Print version and license information"""
    print(f"ansible-inspec version {__version__}")
    print(f"Licensed under GPL-3.0")
    print()
    print("Built with components from:")
    for project, info in UPSTREAM_PROJECTS.items():
        print(f"  - {project}: {info['url']}")
        print(f"    License: {info['license']}")
        print(f"    Copyright: {info['copyright']}")


def print_license_info():
    """Print detailed license information"""
    print("ansible-inspec License Information")
    print("=" * 60)
    print()
    print("This project is licensed under GPL-3.0")
    print()
    print("This project combines components from:")
    print("  1. Ansible (GPL-3.0)")
    print("  2. InSpec (Apache-2.0)")
    print()
    print("The combined work is distributed under GPL-3.0 as it is")
    print("the more restrictive license. Apache-2.0 is compatible")
    print("with GPL-3.0, allowing this combination.")
    print()
    print("See LICENSE and NOTICE files for full details.")


def create_parser():
    """Create the argument parser"""
    parser = argparse.ArgumentParser(
        description='Compliance testing with Ansible and InSpec integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  ansible-inspec exec profile.rb -i inventory.yml
  ansible-inspec init profile my-compliance
  ansible-inspec version --license
  
For more information, visit: https://github.com/htunn/ansible-inspec
        '''
    )
    
    parser.add_argument(
        '--version', '-v',
        action='store_true',
        help='Show version information'
    )
    
    parser.add_argument(
        '--license',
        action='store_true',
        help='Show license information'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # exec command
    exec_parser = subparsers.add_parser(
        'exec',
        help='Execute InSpec profiles against infrastructure'
    )
    exec_parser.add_argument(
        'profile',
        help='Path to InSpec profile, test file, or Chef Supermarket profile name'
    )
    exec_parser.add_argument(
        '-i', '--inventory',
        help='Ansible inventory file'
    )
    exec_parser.add_argument(
        '-t', '--target',
        help='Target to test (ssh://user@host, docker://container, etc.)'
    )
    exec_parser.add_argument(
        '--supermarket',
        action='store_true',
        help='Load profile from Chef Supermarket (e.g., dev-sec/linux-baseline)'
    )
    exec_parser.add_argument(
        '--reporter', '-r',
        default='cli',
        help='Reporter format: cli, json, yaml, html, junit, etc. '
             'Supports multiple: "cli json:/path/file.json"'
    )
    exec_parser.add_argument(
        '--output', '-o',
        help='Output file path (default: .compliance-reports/<timestamp>-<format>)'
    )
    
    # init command
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize a new InSpec profile'
    )
    init_parser.add_argument(
        'type',
        choices=['profile', 'plugin'],
        help='Type of component to initialize'
    )
    init_parser.add_argument(
        'name',
        help='Name of the component'
    )
    
    # convert command
    convert_parser = subparsers.add_parser(
        'convert',
        help='Convert InSpec profile to Ansible collection'
    )
    convert_parser.add_argument(
        'profile',
        help='Path to InSpec profile directory'
    )
    convert_parser.add_argument(
        '-o', '--output-dir',
        default='./collections',
        help='Output directory for Ansible collection (default: ./collections)'
    )
    convert_parser.add_argument(
        '--namespace',
        default='compliance',
        help='Ansible Galaxy namespace (default: compliance)'
    )
    convert_parser.add_argument(
        '--collection-name',
        default='inspec_profiles',
        help='Collection name (default: inspec_profiles)'
    )
    convert_parser.add_argument(
        '--native-only',
        action='store_true',
        help='Only use native Ansible modules (skip InSpec wrapper)'
    )
    convert_parser.add_argument(
        '--no-roles',
        action='store_true',
        help='Do not create roles'
    )
    convert_parser.add_argument(
        '--no-playbooks',
        action='store_true',
        help='Do not create example playbooks'
    )
    
    # version command
    version_parser = subparsers.add_parser(
        'version',
        help='Show version information'
    )
    version_parser.add_argument(
        '--license',
        action='store_true',
        help='Show license information'
    )
    
    return parser


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle top-level flags
    if args.version:
        print_version()
        return 0
    
    if args.license:
        print_license_info()
        return 0
    
    # Handle commands
    if args.command == 'version':
        print_version()
        if hasattr(args, 'license') and args.license:
            print()
            print_license_info()
        return 0
    
    elif args.command == 'exec':
        # Import here to avoid circular dependencies
        from ansible_inspec.core import Runner, ExecutionConfig
        from ansible_inspec.inspec_adapter import InSpecProfile
        
        try:
            # Handle Chef Supermarket profiles
            is_supermarket = hasattr(args, 'supermarket') and args.supermarket
            if is_supermarket:
                # Create supermarket profile
                profile = InSpecProfile.from_supermarket(args.profile)
                print(f"Loading Chef Supermarket profile: {args.profile}")
            else:
                # Regular local profile
                profile = None
                print(f"Executing profile: {args.profile}")
            
            # Create execution config
            exec_config = ExecutionConfig(
                profile_path=args.profile if not profile else profile.profile_path,
                inventory_path=args.inventory,
                target=args.target,
                reporter=args.reporter,
                output_path=args.output,
                is_supermarket=is_supermarket
            )
            
            # Create and run
            runner = Runner()
            if args.inventory:
                print(f"Using inventory: {args.inventory}")
            if args.target:
                print(f"Target: {args.target}")
            print()
            
            result = runner.run(exec_config)
            
            # Save results to file if output specified or multi-reporter format
            from ansible_inspec.reporters import parse_reporter_string, get_default_output_path
            
            reporters = parse_reporter_string(args.reporter)
            for reporter_config in reporters:
                reporter_format = reporter_config['format']
                output_path = reporter_config['path']
                
                # Skip CLI reporter for file output
                if reporter_format.lower() == 'cli':
                    continue
                
                # Use specified path or generate default
                if not output_path:
                    if args.output:
                        output_path = args.output
                    else:
                        profile_name = os.path.basename(exec_config.profile_path)
                        output_path = get_default_output_path(reporter_format, profile_name)
                
                # Map reporter format to save method
                format_map = {
                    'json': 'json',
                    'json-min': 'json',
                    'json-rspec': 'json',
                    'json-automate': 'json',
                    'junit': 'junit',
                    'junit2': 'junit',
                    'html': 'html',
                    'html2': 'html',
                }
                
                save_format = format_map.get(reporter_format.lower())
                if save_format:
                    try:
                        result.save(output_path, save_format)
                        print(f"Report saved: {output_path}")
                    except Exception as e:
                        print(f"Warning: Failed to save {reporter_format} report: {e}", file=sys.stderr)
            
            # Display results (if CLI reporter included or only reporter)
            if any(r['format'].lower() == 'cli' for r in reporters):
                print()
                print("=" * 60)
                print("EXECUTION SUMMARY")
                print("=" * 60)
                print(result.summary())
                print(f"Total hosts: {result.total_hosts}")
                print(f"Successful: {result.successful_hosts}")
                print(f"Failed: {result.failed_hosts}")
                
                if result.errors:
                    print()
                    print("ERRORS:")
                    for host, error in result.errors.items():
                        print(f"  {host}: {error}")
                
                print()
            
            # Return appropriate exit code
            return 0 if result.success else 1
            
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1
    
    elif args.command == 'init':
        import os
        import yaml
        
        profile_name = args.name
        profile_dir = os.path.join(os.getcwd(), profile_name)
        
        if os.path.exists(profile_dir):
            print(f"Error: Directory {profile_dir} already exists", file=sys.stderr)
            return 1
        
        try:
            # Create profile structure
            os.makedirs(profile_dir)
            os.makedirs(os.path.join(profile_dir, 'controls'))
            
            # Create inspec.yml
            inspec_yml = {
                'name': profile_name,
                'title': f'{profile_name} Profile',
                'maintainer': 'Your Name',
                'copyright': 'Your Organization',
                'license': 'GPL-3.0',
                'summary': f'Compliance profile for {profile_name}',
                'version': '0.1.0'
            }
            
            with open(os.path.join(profile_dir, 'inspec.yml'), 'w') as f:
                yaml.dump(inspec_yml, f)
            
            # Create example control
            example_control = f"""# Example control for {profile_name}

control '{profile_name}-01' do
  impact 1.0
  title 'Sample Control'
  desc 'An example control to get you started'
  
  describe file('/etc/passwd') do
    it {{ should exist }}
    it {{ should be_file }}
  end
end
"""
            
            with open(os.path.join(profile_dir, 'controls', 'example.rb'), 'w') as f:
                f.write(example_control)
            
            # Create README
            readme = f"""# {profile_name} Profile

Compliance profile created with ansible-inspec.

## Usage

```bash
ansible-inspec exec {profile_name}/
```

## License

GPL-3.0
"""
            
            with open(os.path.join(profile_dir, 'README.md'), 'w') as f:
                f.write(readme)
            
            print(f"✓ Profile '{profile_name}' created successfully!")
            print(f"  Location: {profile_dir}")
            print()
            print("Next steps:")
            print(f"  1. cd {profile_name}")
            print(f"  2. Edit controls/example.rb")
            print(f"  3. Run: ansible-inspec exec .")
            
            return 0
            
        except Exception as e:
            print(f"Error creating profile: {e}", file=sys.stderr)
            return 1
    
    elif args.command == 'convert':
        from ansible_inspec.converter import ProfileConverter, ConversionConfig
        
        try:
            # Create conversion config
            config = ConversionConfig(
                source_profile=args.profile,
                output_dir=args.output_dir,
                namespace=args.namespace,
                collection_name=args.collection_name,
                create_roles=not args.no_roles,
                create_playbooks=not args.no_playbooks,
                use_native_modules=not args.native_only
            )
            
            # Execute conversion
            converter = ProfileConverter(config)
            print(f"Converting InSpec profile: {args.profile}")
            print(f"Output directory: {args.output_dir}")
            print()
            
            result = converter.convert()
            
            if result.success:
                print("✓ Conversion successful!")
                print()
                print(f"Collection created: {result.collection_path}")
                print(f"  Namespace: {config.namespace}")
                print(f"  Name: {config.collection_name}")
                print()
                print(f"Controls converted: {result.controls_converted}")
                print(f"Roles created: {len(result.roles_created)}")
                
                if result.custom_resources_found > 0:
                    print(f"Custom resources: {result.custom_resources_found}")
                
                if result.playbooks_created:
                    print(f"Playbooks created: {len(result.playbooks_created)}")
                
                if result.warnings:
                    print()
                    print("Warnings:")
                    for warning in result.warnings:
                        print(f"  ⚠ {warning}")
                
                print()
                print("Next steps:")
                print(f"  1. cd {result.collection_path}")
                print(f"  2. ansible-galaxy collection build")
                print(f"  3. ansible-galaxy collection install {config.namespace}-{config.collection_name}-*.tar.gz")
                print()
                
                return 0
            else:
                print("✗ Conversion failed!", file=sys.stderr)
                print()
                for error in result.errors:
                    print(f"Error: {error}", file=sys.stderr)
                return 1
                
        except Exception as e:
            print(f"Conversion error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1
    
    elif args.command is None:
        parser.print_help()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
