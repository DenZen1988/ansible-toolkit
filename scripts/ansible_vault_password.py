#!/usr/bin/env python3
"""
Fetch the Ansible Vault password from HashiCorp Vault.
2026-04-27 -- walther_denis@gmx.de
"""
import os
import sys
import subprocess

BACKEND_PATH = "path/to/secrets/ansible_vault"
DESIRED_VAULT = "https://live-vault.example.com"

def check_environment():
    """Ensure VAULT_ADDR is set and pointing to the correct Vault instance."""
    vault_addr = os.environ.get("VAULT_ADDR")

    if not vault_addr:
        print("Error: VAULT_ADDR environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    if vault_addr != DESIRED_VAULT:
        print(f"Error: VAULT_ADDR is set to {vault_addr}, but expected {DESIRED_VAULT}.", file=sys.stderr)
        sys.exit(1)

def check_vault_login():
    """Check if the user is logged into Vault."""
    try:
        subprocess.run(["vault", "token", "lookup"], capture_output=True, check=True)

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Not logged in into vault. Please login manually using 'vault login' command.", file=sys.stderr)
        sys.exit(1)

def fetch_vault_password():
    """Fetch the Ansible Vault password."""
    try:
        result = subprocess.run(
            ["vault", "kv", "get", "-field=password", BACKEND_PATH],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout.strip())

    except subprocess.CalledProcessError:
        print("Error fetching the Ansible Vault password from Vault.", file=sys.stderr)
        sys.exit(1)

def main():
    """Main function to orchestrate the password retrieval."""
    check_environment()
    check_vault_login()
    fetch_vault_password()

if __name__ == "__main__":
    main()
