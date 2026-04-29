# ansible-toolkit

[![Pipelines](https://github.com/DenZen1988/ansible-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/DenZen1988/ansible-toolkit/actions/workflows/ci.yml)

Stop wrestling with complex bash wrappers and manual vault rotations. This toolkit provides a type-safe, API-driven workflow for managing
scaled ansible deployments.

## Table Of Content

* [Requirements](#requirements)
  * [Install Requirements](#install-requirements)
* [Use the toolkit in ansible](#use-the-toolkit-in-ansible)
  * [Setup via git submodules](#setup-via-git-submodules)
  * [Update the toolkit](#update-the-toolkit)
* [Available Tools](#available-tools)
  * [scripts/ansible_vault_password.py](#scriptsansible_vault_passwordpy)
  * [scripts/generate_inventory.py](#scriptsgenerate_inventorypy)
  * [scripts/rekey.py](#scriptsrekeypy)
  * [run.py](#runpy)
  * [setup.py](#setuppy)
* [License](#license)
* [Author](#author)
* [Contribution](#contribution)

## Requirements

* [python3](https://www.python.org/downloads/)
* [bash](https://www.gnu.org/software/bash/)
* [pyyaml](https://pypi.org/project/PyYAML/)
* [hvac](https://pypi.org/project/hvac/)

### Install Requirements

For the scripts to work out of the box you need to install some "global" packages with `pip`. If you do not want to do that you need to call
the scripts from your virtual environment!

Installation on Mac OS X:

> [!NOTE]
> The option `--user` installs the packages into your local user library (`~/Library/Python/3.x/`) which does not mess with the OS system files.
> The option `--break-system-packages` is required on modern MacOS/Debian versions to allow global pip installations.
> It will not actually "break" anything - it just acknowledges the installation outside of an environment.

```bash
python3 -m pip install hvac pyyaml --user --break-system-packages
```

Installation on Linux:

```bash
pip3 install hvac pyyaml
```

## Use the toolkit in ansible

There are multiple ways to integrate this toolkit into your ansible repository:

* Via *git submodule* with *git sparse checkout* (recommended with some overhead)
* Via `requirements.yml` (not recommended since it will live below `roles/`)
* Via Symlinks (not recommended)

### Setup via git submodules

> [!WARNING]
> When you setup the toolkit via `git submodule` and you clone your ansible repository you have to also run `git submodule init --recursive`
> to ensure the toolkit submodule repo is initialized as well!

The recommended setup via `git submodule` is like this:

```bash
# Initialize the submodule
git submodule add https://github.com/DenZen1988/ansible-toolkit.git .toolkit
# Pin the desired version
git -C .toolkit_src checkout tags/0.0.1
# Add the metadata to your repo
git add .toolkit_src && git commit -m "chore: add toolkit at version 0.0.1"
```

Next create symlinks to the runtime scripts which should be in your ansible project root folder:

```bash
ln -s .toolkit/run.py ./run.py
ln -s .toolkit/setup.py ./setup.py
ls -s .toolkit/scripts ./scripts
```

#### Update the toolkit

Simply run `git submodule update` like this:

```bash
git submodule update --remote
# Pin the desired version
git -C .toolkit_src checkout tags/0.0.x
# Add the metadata to your repo
git add .toolkit_src && git commit -m "chore: add toolkit at version 0.0.x"
```

## Available Tools

### scripts/ansible_vault_password\.py

> [!NOTE]
> `ansible_vault_password.py` does not need to be run manually. It is safe to keep it in a subfolder of your ansible repository.

This script will fetch a password from HashiCorp Vault for files encrypted with `ansible-vault`. Simply set it up in your `ansible.cfg` like
this:

```ini
ansible_vault_password = /path/to/ansible_vault_password.py
```

After that you will never have to enter a password for vaulted files ever again.

### scripts/generate_inventory\.py

> [!NOTE]
> This script only works for **static** inventories. If you have a dynamic inventory the scripts logic will be way more complicated!
> See [generate_dynamic_inventory.py](./scripts/generate_dynamic_inventory.py) for that.

This script will create a static inventory file out of `servers.txt`. Here is the example, based on the `examples/servers.txt.example` and
the `examples/config.json.example`:

The `examples/servers.txt.example`:

```text
# My Servers (Comments will be ignored by script)
host1 group1
host2 group1
host3 group1
# Next group starts here
host4 group2
host5 group2
host6 group2
```

The `examples/config.json.example`:

```json
{
    "source_file": "./servers.txt",
    "output_file": "./inventory/all.yml",
    "connection_settings": {
        "ansible_user": "ansible_user",
        "ansible_ssh_private_key_file": "~/.ssh/id_rsa",
        "ansible_ports": [2424]
    }
}
```

Running the script:

```bash
$:> ./generate_inventory.py 
Inventory written to: ./inventory/all.yml
```

How the inventory looks then:

```yaml
---
all:
  vars:
    ansible_user: ansible_user
    ansible_ssh_private_key_file: ~/.ssh/id_rsa
    ansible_ports:
      - 2424
  children:
    group1:
      hosts:
        host1:
        host2:
        host3:
    group2:
      hosts:
        host4:
        host5:
        host6:
```

### scripts/generate_dynamic_inventory\.py

This script highly depends on your naming convention! For now it works with hostnames like this:

* fooicingafeqa-bs01 - *it will be split like this:* foo - icingafe - qa - bs (product/platform + software/platform - environment - location)
* fooicingafeqa001-bs-kae-de - *it will be split like this in the same style:* (product/platform + software/platform - environment - location)

There is no example since this is only used for bigger inventories (mainly companies). So I cannot provide a proper example here.

### scripts/rekey\.py

> [!WARNING]
> `rekey.py` should not be located in your ansible root directory! This will avoid running it on accident. Always keep it outside or in a subfolder!

This script will remove the pain of manually rekeying any ansible vaulted files. It works like this:

* Fetch the correct password and store it in a temporary file
* Generate a new secure password (64 characters)
* Rekey all the vaulted files in your repository
* Push the new password only **after** the rekeying was successful to HashiCorp Vault
* Cleanup the temporary files afterwards

1. Copy the example config to your home:

    ```bash
    cp examples/vault_rekey_config.yml.example ~/.vault_rekey_config.yml
    ```

2. Adjust the values to your local environment
3. Run the script in this order:
    * `./rekey.py -h` - verify that the help is displayed and the script can run
    * `./rekey.py -r` - rotate the password locally and rekey all vaulted files
    * Verify that your changes are correct and worked like intended - view a vaulted file like this with the new password:

        ```bash
        ansible-vault view path/to/vaulted/file --ask-vault-pass
        ```

    * `./rekey.py -p` - push the new password to your HashiCorp Vault
    * `./rekey.py -c` - cleanup the temporary files (just in case)

#### Security Features

* Git integrity - *The script refuses to run if there are uncommitted changes before you start*
* Atomic Rotation - *The new password is pushed to vault only **after** user confirmation*
* Path validation - *Automatic tilde expansion and directory checks*

### run\.py

This is basically the all in one runner for running ansible within a virtual environment. I got tired of always having to call the binaries
from the virtual environment like this:

```bash
.venv/bin/ansible-playbook -i inventory/ playbooks/site.yml --tags=foobar --limit=example.com --check
```

So I decided to build me a runner script that can handle every binary from the virtual environmeent. This is just a quality of life script but
I prefer typing less in general. The help should be pretty self-explaining:

```bash
Usage: ./run.py [OPTIONS] [ANSIBLE_ARGS]

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
    ./run.py -p playbooks/site.yml --tags=base --check
```

### setup\.py

As mentioned above I do not like typing too much and setting up a virtual environment by hand is already too much typing. That's why I came
up with the idea of having a setup script to take care of that. The help function should be self-explaining as well here:

```bash
usage: setup.py [-h] [-c] [-d] [-i] [-r] [-u] [-U]

Setup Virtual Environment with all requirements

options:
  -h, --help            show this help message and exit
  -c, --create          Create the virtual environment and install requirements
  -d, --destroy         Destroy the existing virtual environment
  -i, --generate-inventory
                        Generate inventory file by calling another script (THIS IS NOT IMPLEMENTED, YET!)
  -r, --recreate        Destroy and recreate the virtual environment
  -u, --update          Update the virtual environment with the latest requirements
  -U, --update-roles    Update Ansible roles using ansible-galaxy
```

## License

[MIT](./LICENSE)

## Author

Denis Walther — [GitHub](https://github.com/DenZen1988)

## Versioning

The versioning follows the simple pattern of counting up from 0.0.1. Nothing fancy here.

## Contribution

You are more than welcome to create pull requests for new features and functions:

1. Create a new branch
2. Adjust or add the code desired
3. Ensure the pipelines are green
4. Create a PR
