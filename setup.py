#!/usr/bin/env python3
"""
Setup script for Ansible development virtual environment.
2026-04-17 -- walther_denis@gmx.de
"""
import sys
import subprocess
import shutil
from pathlib import Path
import argparse

VENV_PATH = Path(".venv")
VENV_PYTHON = VENV_PATH / "bin" / "python3"

def run_in_venv(command_list):
    """Run a command in the virtual environment."""
    if command_list[0] == "pip":
        full_cmd = [str(VENV_PYTHON), "-m"] + command_list
    else:
        binary = VENV_PATH / "bin" / command_list[0]
        full_cmd = [str(binary)] + command_list[1:]
    subprocess.run(full_cmd, check=True)

def destroy_environment():
    """Remove the virtual environment."""
    if VENV_PATH.is_dir():
        print(f"Destroying virtual environment at {VENV_PATH}...")
        shutil.rmtree(VENV_PATH)
        print("Virtual environment destroyed.")
    else:
        print("No virtual environment found. Nothing to do.")

def create_environment():
    """Create the virtual environment and install Requirements."""
    if VENV_PATH.is_dir():
        print(f"Virtual environment already exists at {VENV_PATH}.")
        return
    try:
        print(f"Creating virtual environment at {VENV_PATH}...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_PATH)], check=True)

        print("Virtual environment created.")
        print("Installing Ansible in the virtual environment...")
        run_in_venv(["pip", "install", "--upgrade", "pip"])
        run_in_venv(["pip", "install", "-r", "requirements.txt"])

        print("Ansible installed in the virtual environment.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while creating the virtual environment: {e}")
        sys.exit(1)

def update_environment():
    """Update the virtual environment with the latest requirements."""
    if not VENV_PATH.is_dir():
        print("Virtual environment not found. Please create it first using the -c option.")
        sys.exit(1)
    try:
        print("Updating virtual environment with the latest requirements...")
        run_in_venv(["pip", "install", "--upgrade", "-r", "requirements.txt"])
        print("Virtual environment updated.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while updating the virtual environment: {e}")
        sys.exit(1)

def update_roles():
    """Update Ansible roles using ansible-galaxy."""
    if not VENV_PATH.is_dir():
        print("Virtual environment not found. Please create it first using the -c option.")
        sys.exit(1)
    try:
        print("Updating Ansible roles using ansible-galaxy...")
        run_in_venv(["ansible-galaxy", "install", "-r", "requirements.yml", "-p", "roles/", "--force"])
        print("Ansible roles updated.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while updating Ansible roles: {e}")
        sys.exit(1)

def generate_inventory():
    """Generate inventory file calling another script."""
    if not VENV_PATH.is_dir():
        print("Virtual environment not found. Please create it first using the -c option.")
        sys.exit(1)
    try:
        print("Generating inventory file...")
        run_in_venv(["python3", "generate_inventory.py"])
        print("Inventory file generated.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while generating the inventory file: {e}")
        sys.exit(1)

def main():
    """Main entry point of the script."""
    parser = argparse.ArgumentParser(description="Setup Virtual Environment with all requirements")

    parser.add_argument("-c", "--create", action="store_true", help="Create the virtual environment and install requirements")
    parser.add_argument("-d", "--destroy", action="store_true", help="Destroy the existing virtual environment")
    parser.add_argument("-i", "--generate-inventory", action="store_true", help="Generate inventory file by calling another script \
                        (THIS IS NOT IMPLEMENTED, YET!)")
    parser.add_argument("-r", "--recreate", action="store_true", help="Destroy and recreate the virtual environment")
    parser.add_argument("-u", "--update", action="store_true", help="Update the virtual environment with the latest requirements")
    parser.add_argument("-U", "--update-roles", action="store_true", help="Update Ansible roles using ansible-galaxy")

    args = parser.parse_args()

    if args.destroy or args.recreate:
        destroy_environment()
    if args.create or args.recreate:
        create_environment()
    if args.update:
        update_environment()
    if args.update_roles:
        update_roles()
    if args.generate_inventory:
        generate_inventory()
    if not any(vars(args).values()):
        parser.print_help()

if __name__ == "__main__":
    main()
