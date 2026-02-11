#!/usr/bin/env python3
"""
Pre-publication validation script for ansible-inspec server.

Performs comprehensive checks to ensure the server is ready for publication.
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import List, Tuple

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


class PublicationChecker:
    """Validates ansible-inspec server readiness for publication."""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
        self.passed = []
        
    def print_header(self, text: str):
        """Print section header."""
        print(f"\n{BLUE}{'=' * 70}")
        print(f"  {text}")
        print(f"{'=' * 70}{NC}\n")
    
    def print_success(self, text: str):
        """Print success message."""
        print(f"{GREEN}✓{NC} {text}")
        self.passed.append(text)
    
    def print_error(self, text: str):
        """Print error message."""
        print(f"{RED}✗{NC} {text}")
        self.errors.append(text)
    
    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{YELLOW}⚠{NC} {text}")
        self.warnings.append(text)
    
    def check_file_exists(self, filepath: str, description: str) -> bool:
        """Check if a file exists."""
        path = self.root_dir / filepath
        if path.exists():
            self.print_success(f"{description}: {filepath}")
            return True
        else:
            self.print_error(f"{description} missing: {filepath}")
            return False
    
    def check_no_hardcoded_secrets(self) -> bool:
        """Check for hardcoded secrets in code."""
        self.print_header("Checking for Hardcoded Secrets")
        
        patterns = [
            ("password", "hardcoded passwords"),
            ("secret", "hardcoded secrets"),
            ("AKIAIO", "AWS keys"),
            ("sk_live", "Stripe keys"),
        ]
        
        problematic_files = []
        
        # Check Python files (exclude .venv and test files)
        for py_file in self.root_dir.rglob("*.py"):
            # Skip test files, __pycache__, and .venv
            if any(x in str(py_file) for x in ["test", "__pycache__", ".venv", "venv"]):
                continue
                
            try:
                content = py_file.read_text()
                for pattern, desc in patterns:
                    if pattern in content.lower():
                        # Check if it's in a comment or docstring
                        if not any(x in content for x in ["# example", "# TODO", '"""', "'''"]):
                            problematic_files.append((py_file.relative_to(self.root_dir), desc))
            except:
                pass
        
        if problematic_files:
            for file, desc in set(problematic_files):
                self.print_warning(f"Possible {desc} in: {file}")
            return True
        else:
            self.print_success("No obvious hardcoded secrets found")
            return True
    
    def check_documentation(self) -> bool:
        """Check that required documentation exists."""
        self.print_header("Checking Documentation")
        
        docs = [
            ("README.md", "README"),
            ("CHANGELOG.md", "Changelog"),
            ("LICENSE", "License file"),
            ("TESTING.md", "Testing guide"),
            ("docs/SERVER.md", "Server documentation"),
        ]
        
        all_exist = True
        for filepath, desc in docs:
            if not self.check_file_exists(filepath, desc):
                all_exist = False
        
        return all_exist
    
    def check_version_consistency(self) -> bool:
        """Check version numbers are consistent."""
        self.print_header("Checking Version Consistency")
        
        versions = {}
        
        # Check pyproject.toml
        pyproject = self.root_dir / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            for line in content.splitlines():
                if line.startswith("version ="):
                    try:
                        versions['pyproject.toml'] = line.split('"')[1]
                    except IndexError:
                        versions['pyproject.toml'] = line.split("'")[1]
                    break
        
        # Check __init__.py
        init_file = self.root_dir / "lib" / "ansible_inspec" / "__init__.py"
        if init_file.exists():
            content = init_file.read_text()
            for line in content.splitlines():
                if "__version__" in line and "=" in line:
                    try:
                        versions['__init__.py'] = line.split('"')[1]
                    except IndexError:
                        try:
                            versions['__init__.py'] = line.split("'")[1]
                        except IndexError:
                            pass
                    break
        
        # Check api.py
        api_file = self.root_dir / "lib" / "ansible_inspec" / "server" / "api.py"
        if api_file.exists():
            content = api_file.read_text()
            for line in content.splitlines():
                if 'version=' in line and 'FastAPI' not in line:
                    try:
                        versions['api.py'] = line.split('"')[1]
                    except IndexError:
                        try:
                            versions['api.py'] = line.split("'")[1]
                        except IndexError:
                            pass
                    break
        
        if not versions:
            self.print_error("No version information found")
            return False
        
        if len(set(versions.values())) == 1:
            version = list(versions.values())[0]
            self.print_success(f"Version consistent across files: {version}")
            return True
        else:
            self.print_error("Version mismatch:")
            for file, ver in versions.items():
                print(f"  {file}: {ver}")
            return False
    
    def check_docker_files(self) -> bool:
        """Check Docker configuration."""
        self.print_header("Checking Docker Configuration")
        
        files = [
            ("Dockerfile", "Main Dockerfile"),
            ("docker-compose.yml", "Docker Compose config"),
            (".dockerignore", "Docker ignore file"),
        ]
        
        all_exist = True
        for filepath, desc in files:
            if not self.check_file_exists(filepath, desc):
                all_exist = False
        
        return all_exist
    
    def check_test_coverage(self) -> bool:
        """Check that tests exist and can run."""
        self.print_header("Checking Test Coverage")
        
        test_files = list((self.root_dir / "tests").glob("test_*.py"))
        
        if len(test_files) < 5:
            self.print_warning(f"Only {len(test_files)} test files found")
        else:
            self.print_success(f"Found {len(test_files)} test files")
        
        # Check for server tests
        server_tests = [
            "test_server_api.py",
            "test_server_models.py", 
            "test_server_integration.py"
        ]
        
        all_exist = True
        for test_file in server_tests:
            if not self.check_file_exists(f"tests/{test_file}", f"Server test: {test_file}"):
                all_exist = False
        
        return all_exist
    
    def check_dependencies(self) -> bool:
        """Check dependencies are specified."""
        self.print_header("Checking Dependencies")
        
        pyproject = self.root_dir / "pyproject.toml"
        if not pyproject.exists():
            self.print_error("pyproject.toml not found")
            return False
        
        content = pyproject.read_text()
        
        required_deps = [
            "fastapi",
            "uvicorn",
            "prisma",
            "pydantic",
        ]
        
        all_found = True
        for dep in required_deps:
            if dep in content:
                self.print_success(f"Dependency specified: {dep}")
            else:
                self.print_error(f"Missing dependency: {dep}")
                all_found = False
        
        return all_found
    
    def check_ci_cd(self) -> bool:
        """Check CI/CD configuration."""
        self.print_header("Checking CI/CD Configuration")
        
        if self.check_file_exists(".github/workflows/tests.yml", "GitHub Actions workflow"):
            return True
        else:
            self.print_warning("No CI/CD configuration found")
            return False
    
    def print_summary(self):
        """Print validation summary."""
        self.print_header("Validation Summary")
        
        print(f"{GREEN}Passed:{NC} {len(self.passed)} checks")
        print(f"{YELLOW}Warnings:{NC} {len(self.warnings)} issues")
        print(f"{RED}Errors:{NC} {len(self.errors)} critical issues")
        
        if self.errors:
            print(f"\n{RED}CRITICAL ISSUES - Must fix before publication:{NC}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n{YELLOW}WARNINGS - Should address:{NC}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print()
        
        if self.errors:
            print(f"{RED}❌ NOT READY FOR PUBLICATION{NC}")
            return False
        elif self.warnings:
            print(f"{YELLOW}⚠️  READY WITH WARNINGS{NC}")
            return True
        else:
            print(f"{GREEN}✅ READY FOR PUBLICATION{NC}")
            return True
    
    def run_all_checks(self) -> bool:
        """Run all validation checks."""
        print(f"{BLUE}")
        print("=" * 70)
        print("  Ansible-InSpec Server - Pre-Publication Validation")
        print("=" * 70)
        print(f"{NC}")
        
        checks = [
            self.check_documentation,
            self.check_version_consistency,
            self.check_docker_files,
            self.check_test_coverage,
            self.check_dependencies,
            self.check_no_hardcoded_secrets,
            self.check_ci_cd,
        ]
        
        for check in checks:
            check()
        
        return self.print_summary()


def main():
    """Main entry point."""
    checker = PublicationChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
