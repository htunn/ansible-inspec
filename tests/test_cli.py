"""
Test suite for ansible-inspec CLI

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import pytest
from ansible_inspec.cli import create_parser, main
from ansible_inspec import __version__


def test_version():
    """Test version string is defined"""
    assert __version__ is not None
    assert isinstance(__version__, str)


def test_parser_creation():
    """Test CLI parser can be created"""
    parser = create_parser()
    assert parser is not None


def test_version_flag():
    """Test --version flag"""
    parser = create_parser()
    args = parser.parse_args(['--version'])
    assert args.version is True


def test_exec_command():
    """Test exec command parsing"""
    parser = create_parser()
    args = parser.parse_args(['exec', 'profile.rb'])
    assert args.command == 'exec'
    assert args.profile == 'profile.rb'


def test_init_command():
    """Test init command parsing"""
    parser = create_parser()
    args = parser.parse_args(['init', 'profile', 'my-profile'])
    assert args.command == 'init'
    assert args.type == 'profile'
    assert args.name == 'my-profile'


# TODO: Add more comprehensive tests
# TODO: Add integration tests
# TODO: Add mocking for external dependencies
