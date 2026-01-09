#!/usr/bin/env python3
"""
Debug script to test InSpec execution and JSON parsing
"""

import subprocess
import json
import sys

# Test InSpec execution directly
profile = "supermarket://dev-sec/ssh-baseline"
target = "ssh://htunn-malaysia"

print("=" * 60)
print("Testing InSpec Direct Execution")
print("=" * 60)
print(f"Profile: {profile}")
print(f"Target: {target}")
print()

# Run InSpec directly
cmd = ['inspec', 'exec', profile, '-t', target, '--reporter', 'json']
print(f"Command: {' '.join(cmd)}")
print()

result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

print(f"Return code: {result.returncode}")
print(f"Stdout length: {len(result.stdout)} chars")
print(f"Stderr length: {len(result.stderr)} chars")
print()

if result.stderr:
    print("STDERR:")
    print(result.stderr[:500])
    print()

# Try to parse JSON
try:
    data = json.loads(result.stdout)
    print("✅ JSON parsing successful")
    print()
    
    # Analyze structure
    print("JSON Structure:")
    print(f"  version: {data.get('version')}")
    print(f"  platform: {data.get('platform', {})}")
    print(f"  profiles: {len(data.get('profiles', []))} profile(s)")
    print()
    
    if data.get('profiles'):
        profile_data = data['profiles'][0]
        print(f"Profile 0:")
        print(f"  name: {profile_data.get('name')}")
        print(f"  version: {profile_data.get('version')}")
        print(f"  title: {profile_data.get('title')}")
        print(f"  controls: {len(profile_data.get('controls', []))} control(s)")
        print()
        
        if profile_data.get('controls'):
            control = profile_data['controls'][0]
            print(f"First control:")
            print(f"  id: {control.get('id')}")
            print(f"  title: {control.get('title')}")
            print(f"  results: {len(control.get('results', []))} result(s)")
            if control.get('results'):
                result_item = control['results'][0]
                print(f"  first result status: {result_item.get('status')}")
        else:
            print("⚠️  No controls in profile!")
            print()
            print("Full profile data keys:", list(profile_data.keys()))
    else:
        print("⚠️  No profiles in output!")
        print()
        print("Full data keys:", list(data.keys()))
        
    # Save full output for inspection
    with open('/tmp/inspec-debug-output.json', 'w') as f:
        json.dump(data, f, indent=2)
    print()
    print("Full output saved to: /tmp/inspec-debug-output.json")
    
except json.JSONDecodeError as e:
    print(f"❌ JSON parsing failed: {e}")
    print()
    print("First 1000 chars of stdout:")
    print(result.stdout[:1000])

print()
print("=" * 60)
