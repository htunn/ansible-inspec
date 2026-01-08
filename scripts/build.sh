#!/bin/bash
# Build script for ansible-inspec binary distribution
# Copyright (C) 2026 ansible-inspec project contributors
# Licensed under GPL-3.0

set -e

echo "Building ansible-inspec distribution..."

# Clean previous builds
rm -rf build/ dist/ *.egg-info

# Build wheel
python -m pip install --upgrade pip build
python -m build

echo ""
echo "Build complete! Distribution files in dist/"
echo ""
echo "To install locally:"
echo "  pip install dist/ansible_inspec-*.whl"
echo ""
echo "To create binary with PyInstaller (install first):"
echo "  pip install pyinstaller"
echo "  pyinstaller --onefile --name ansible-inspec bin/ansible-inspec"
