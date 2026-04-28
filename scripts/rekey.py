#!/usr/bin/env python3
"""
Rotate Ansible Vault passwords and rekey vaulted files.
2026-04-28 -- walther_denis@gmx.de
"""
import argparse
import os
import secrets
import string
import subprocess
import sys
from pathlib import Path
import yaml
# Use hvac for push/pull passwords
import hvac
from hvac import exceptions

# Start by loading user configuration
def load_user_config():
    """Load user configuration from ~/.vault_rekey_config.yaml."""
    config_path = Path.home() / ".vault_rekey_config.yaml"

    if not config_path.exists():
        print(f"Error: Configuration file {config_path} not found. Please create it based on the template in the README.", file=sys.stderr)
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # If the data is not a dict (e.g., empty file), use an empty dict to avoid errors later
    config = data if isinstance(data, dict) else {}

    required = ["vault_instance", "backend_path", "iac_directory"]
    for key in required:
        if key not in config:
            print(f"Error: Missing required configuration '{key}' in {config_path}.", file=sys.stderr)
            sys.exit(1)

    config['iac_directory'] = str(Path(config['iac_directory']).expanduser())
    return config

CONFIG = load_user_config()

class VaultRekeyer:
    """Class to handle vault password rotation and rekeying of vaulted files."""
    def __init__(self):
        self.current_pass = None
        self.new_pass = None
        self.tmp_dir = Path("/tmp")
        self.pass_old_file = self.tmp_dir / ".current_vault_pass.txt"
        self.pass_new_file = self.tmp_dir / ".new_vault_pass.txt"

    def check_git_status(self, stage="before"):
        """Verify git status to prevent mess-ups."""
        os.chdir(CONFIG["iac_directory"])
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, check=True, text=True)
        changes = result.stdout.strip()

        if stage == "before" and changes:
            print("Error: Uncommitted changes detected. Please commit or stash them before rekeying.", file=sys.stderr)
            sys.exit(1)
        elif stage == "after" and not changes:
            print("Error: No changes detected after rekeying. Something went wrong.", file=sys.stderr)
            sys.exit(1)

    def connect_vault(self):
        """Connect to vault and verify login."""
        client = hvac.Client(url=CONFIG["vault_instance"])
        if not client.is_authenticated():
            print(f"Error: Not logged in into {CONFIG['vault_instance']}. Please login first.", file=sys.stderr)
            sys.exit(1)
        return client

    def generate_password(self, length=64):
        """Generate a random password (64 characters)."""
        alphabet = string.ascii_letters + string.digits
        self.new_pass = ''.join(secrets.choice(alphabet) for _ in range(length))
        self.pass_new_file.write_text(self.new_pass)
        print(f"Generated new vault password and saved to {self.pass_new_file}")

    def fetch_current_password(self, client):
        """Fetch the current password from HashiCorp Vault."""
        try:
            response = client.secrets.kv.v2.read_secret_version(path=CONFIG["backend_path"])
            self.current_pass = response['data']['data']['password']
            self.pass_old_file.write_text(self.current_pass)
            print(f"Fetched current vault password and saved to {self.pass_old_file}")
        except exceptions.InvalidPath as e:
            print(f"Error: Could not fetch current password from Vault: {e}", file=sys.stderr)
            sys.exit(1)
        except exceptions.VaultError as e:
            print(f"Vault error: {e}", file=sys.stderr)
            sys.exit(1)

    def rekey_files(self):
        """Rekey all vaulted files using ansible-vault."""
        repo_path = Path(CONFIG["iac_directory"]) / "inventory"
        extensions = ['*.yml', '*.yaml', '*.ini']
        vault_files = []
        for ext in extensions:
            for p in repo_path.rglob(ext):
                if "$ANSIBLE_VAULT" in p.read_text(errors='ignore'):
                    vault_files.append(p)

        if not vault_files:
            print("No vaulted files found to rekey.")
            return

        print(f"Found {len(vault_files)} vaulted files.")
        confirm = input("Proceed with rekeying? (y/n): ")
        if confirm.lower() != 'y':
            print("Rekeying aborted by user.")
            sys.exit(0)

        for vfile in vault_files:
            print(f"Rekeying {vfile.name}...")
            cmd = [
                "ansible-vault", "rekey",
                f"--vault-id=default@{self.pass_old_file}",
                f"--vault-id=default@{self.pass_new_file}",
                str(vfile)
            ]
            subprocess.run(cmd, check=True)

    def push_to_vault(self, client):
        """Push the new password to HashiCorp Vault."""
        if not self.new_pass:
            print("Error: New password not generated. Cannot push to vault.", file=sys.stderr)
            sys.exit(1)

        client.secrets.kv.v2.create_or_update_secret(
            path=CONFIG["backend_path"],
            secret={"password": self.new_pass}
        )
        print(f"New vault password pushed to {CONFIG['vault_instance']} at {CONFIG['backend_path']}")

    def cleanup(self):
        """Securely remove temporary password files."""
        for f in [self.pass_old_file, self.pass_new_file]:
            if f.exists():
                f.unlink()
            print(f"Removed temporary file {f}")

def main():
    """Main function to handle command-line arguments and orchestrate the rekeying process."""
    parser = argparse.ArgumentParser(description="Ansible Vault Rekey Tool")
    parser.add_argument("-r", "--rotate", action="store_true", help="Rotate vault passwords and rekey files")
    parser.add_argument("-p", "--push", action="store_true", help="Push new password to HashiCorp Vault")
    parser.add_argument("-c", "--cleanup", action="store_true", help="Cleanup temporary password files")

    args = parser.parse_args()
    rekeyer = VaultRekeyer()

    if args.cleanup:
        rekeyer.cleanup()
        return

    client = rekeyer.connect_vault()

    if args.rotate:
        rekeyer.check_git_status(stage="before")
        rekeyer.fetch_current_password(client)
        rekeyer.generate_password()
        rekeyer.rekey_files()
        rekeyer.check_git_status(stage="after")
        print("\nREKEY SUCCESSFUL. Run with --push to update the password in Vault.")

    if args.push:
        if not rekeyer.new_pass and rekeyer.pass_new_file.exists():
            rekeyer.new_pass = rekeyer.pass_new_file.read_text().strip()

        rekeyer.push_to_vault(client)
        rekeyer.cleanup()

if __name__ == "__main__":
    main()
