#!/usr/bin/env python3
"""
Script to generate a nested Hiera-style inventory from a host list fetched via HTTP/HTTPS.
- Fetches hostnames from a specified URL (e.g., Management Host API).
- Parses hostnames to extract environment, group, and location information.
- Builds a nested dictionary structure suitable for Ansible inventory.
- Saves the final inventory to inventory/hosts.yml in YAML format.
2026-04-29 -- walther_denis@gmx.de"""
import json
import os
import sys

def load_config():
    """Load and validate the configuration file."""
    path = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    if not os.path.exists(path):
        print(f"Error: Config '{path}' not found.")
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    # Required keys check
    if not all(k in cfg for k in ['source_file', 'output_file']):
        print("Error: 'source_file' and 'output_file' are required in config.")
        sys.exit(1)
    return cfg

def parse_server_list(source):
    """Read the text file and return a grouped dictionary."""
    if not os.path.exists(source):
        print(f"Error: Source '{source}' not found.")
        sys.exit(1)

    data = {}
    with open(source, 'r', encoding='utf-8') as f:
        for line in f:
            clean_line = line.strip()
            if not clean_line or clean_line.startswith('#'):
                continue
            parts = clean_line.replace(':', ' ').split()
            host = parts[0]
            group = parts[1] if len(parts) > 1 else 'ungrouped'
            data.setdefault(group, []).append(host)
    return data

def build_yaml_structure(conn, inventory_data):
    """Construct the YAML lines from data blocks."""
    lines = ["---", "all:"]
    if conn:
        lines.append("  vars:")
        for key, val in conn.items():
            if isinstance(val, list):
                lines.append(f"    {key}:")
                lines.extend([f"      - {i}" for i in val])
            else:
                lines.append(f"    {key}: {val}")

    lines.append("  children:")
    for group, hosts in inventory_data.items():
        lines.append(f"    {group}:")
        lines.append("      hosts:")
        lines.extend([f"        {h}:" for h in hosts])
    return lines

def main():
    """Main execution"""
    cfg = load_config()
    # Extract keys
    src, out = cfg['source_file'], cfg['output_file']
    conn = cfg.get('connection_settings', cfg.get('connection_Settings', {}))
    # Process
    inv_data = parse_server_list(src)
    yaml_output = build_yaml_structure(conn, inv_data)
    # Write
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write("\n".join(yaml_output) + "\n")
    print(f"Inventory written to: {out}")

if __name__ == "__main__":
    main()
