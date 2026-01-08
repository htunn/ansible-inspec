"""
Test configuration

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import sys
import os

# Add lib directory to path for testing
lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
sys.path.insert(0, lib_path)
