#!/usr/bin/env python3
"""
Generate Fernet encryption key for ansible-inspec server.
"""
import os
import sys
from cryptography.fernet import Fernet


def generate_encryption_key():
    """Generate and print encryption key for environment variable"""
    key = Fernet.generate_key()
    
    print("=" * 70)
    print("Generated Fernet Encryption Key")
    print("=" * 70)
    print()
    print("Your new encryption key:")
    print(key.decode())
    print()
    print("Add this to your .env file:")
    print(f"ENCRYPTION_KEY={key.decode()}")
    print()
    print("=" * 70)
    print("IMPORTANT SECURITY NOTES:")
    print("=" * 70)
    print("1. Keep this key secret - anyone with this key can decrypt your data")
    print("2. Store it securely in environment variables or secrets manager")
    print("3. Never commit this key to version control")
    print("4. Back up this key in a secure location")
    print("5. If you lose this key, encrypted data cannot be recovered")
    print("=" * 70)
    print()
    
    # Optionally save to file with restricted permissions
    save_to_file = input("Save key to .encryption_key file? (y/N): ").strip().lower()
    if save_to_file == 'y':
        key_file = '.encryption_key'
        with open(key_file, 'wb') as f:
            f.write(key)
        
        # Set restrictive permissions (Unix/Linux/Mac only)
        if os.name != 'nt':  # Not Windows
            os.chmod(key_file, 0o600)  # Read/write owner only
            print(f"✓ Key saved to {key_file} with restricted permissions (0600)")
        else:
            print(f"✓ Key saved to {key_file}")
            print("⚠ On Windows, manually restrict file permissions")
        
        print()
        print("To use this key, set environment variable:")
        print(f"export ENCRYPTION_KEY=$(cat {key_file})")


if __name__ == "__main__":
    generate_encryption_key()
