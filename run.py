#!/usr/bin/env python3
"""
A simple wrapper script to run Ansible commands from a virtual environment.
This script checks for the existence of a virtual environment in the current directory,
and then runs the specified Ansible command with any additional arguments passed to it.
"""
import sys
import subprocess
from pathlib import Path

COMMAND_MAP = {
    "-a": "ansible", "ansible": "ansible",
    "-p": "ansible-playbook", "playbook": "ansible-playbook",
    "-c": "ansible-console", "console": "ansible-console",
    "-g": "ansible-galaxy", "galaxy": "ansible-galaxy",
    "-i": "ansible-inventory", "inventory": "ansible-inventory",
    "-l": "ansible-lint", "lint": "ansible-lint",
    "-pu": "ansible-pull", "pull": "ansible-pull",
    "-t": "ansible-test", "test": "ansible-test",
    "-v": "ansible-vault", "vault": "ansible-vault",
    "-h": "help", "--help": "help", "help": "help",
}

def check_venv():
    """Fail if the virtual environment does not exist."""
    if not Path(".venv").exists():
        print("Virtual environment not found. Please run 'python3 -m venv .venv' to create it.")
        sys.exit(1)

def print_usage():
    """Print usage instructions."""
    usage_text = f'''
Usage: {sys.argv[0]} [OPTIONS] [ANSIBLE_ARGS]

Options:
    -a, ansible           Run the 'ansible' command
    -p, playbook          Run the 'ansible-playbook' command
    -c, console           Run the 'ansible-console' command
    -g, galaxy            Run the 'ansible-galaxy' command
    -i, inventory         Run the 'ansible-inventory' command
    -l, lint              Run the 'ansible-lint' command
    -pu, pull             Run the 'ansible-pull' command
    -t, test              Run the 'ansible-test' command
    -v, vault             Run the 'ansible-vault' command
    -h, --help, help      Show this help message and exit

Example:
    {sys.argv[0]} -p playbooks/site.yml --tags=base --check
'''
    print(usage_text)


def main():
    """Main entry point of the script."""
    if len(sys.argv) < 2:
        print_usage()
        return

    command_key = sys.argv[1]

    if command_key in ["-h", "--help", "help"]:
        print_usage()
        return

    if command_key not in COMMAND_MAP:
        print(f"ERROR: Unknown option: {command_key}")
        print_usage()
        return

    check_venv()
    binary_name = COMMAND_MAP[command_key]
    binary_path = f".venv/bin/{binary_name}"
    full_command = [binary_path] + sys.argv[2:]

    try:
        subprocess.run(full_command, check=True)
    except subprocess.CalledProcessError:
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
