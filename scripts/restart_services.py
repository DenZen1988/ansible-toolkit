#!/usr/bin/env python3
"""
Script to automate restarting systemd services based on needrestart output, with protections for critical
services defined by wildcard patterns.

2026-06-11 -- denis.walther@ionos.com
"""
import argparse
import subprocess
import sys
import fnmatch

# Define CRITICAL services here using shell-style wildcards
CRITICAL_SERVICES = [
    'frr',
    'elasticsearch*',
    'nginx*',
]

def is_critical(service_name):
    """Checks if a service matches any of the critical wildcard patterns."""
    for pattern in CRITICAL_SERVICES:
        if fnmatch.fnmatch(service_name, pattern):
            return True
    return False

def get_pending_services():
    """Queries needrestart for services that require a restart."""
    try:
        result = subprocess.run(
            ['needrestart', '-b'],
            check=True,
            capture_output=True,
            text=True
        )

        pending = []
        for line in result.stdout.splitlines():
            if line.startswith('NEEDRESTART-SVC:'):
                svc = line.split(':', 1)[1].strip()
                if svc.endswith('.service'):
                    svc = svc[:-8]
                pending.append(svc)
        return pending

    except FileNotFoundError:
        print("[ERROR] 'needrestart' is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 'needrestart' command failed: {e}", file=sys.stderr)
        sys.exit(1)

def restart_service(service_name, noop):
    """Restarts a systemd service or prints the action if noop is True."""
    if noop:
        print(f"[NOOP] Would restart service: {service_name}")
        return True

    print(f"Restarting service: {service_name}...")
    try:
        subprocess.run(
            ['systemctl', 'restart', service_name],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"[SUCCESS] Restarted {service_name}")
        return True
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.strip()

        # If the unit simply doesn't exist, log a warning but don't fail the script
        if "not found" in err_msg.lower():
            print(f"[WARNING] {service_name} not found by systemctl. Skipping.")
            return True

        # For all other genuine errors (like bad config files), fail normally
        print(f"[ERROR] Failed to restart {service_name}. Error: {err_msg}", file=sys.stderr)
        return False

def main():
    """Main function to parse arguments and orchestrate service restarts."""
    parser = argparse.ArgumentParser(description="Automate systemd service restarts using needrestart and wildcards.")

    parser.add_argument('--services', nargs='*', default=[],
                        help="Explicit list of services to restart (overrides critical protections).")
    parser.add_argument('--auto', action='store_true',
                        help="Fetch pending services from needrestart and restart non-critical ones.")
    parser.add_argument('--noop', '--dry-run', action='store_true',
                        help="Print out what would be done without making actual changes.")

    args = parser.parse_args()

    services_to_restart = set(args.services)

    if args.auto:
        pending_services = get_pending_services()

        if not pending_services:
            print("needrestart reports no services require restarting.")
        else:
            for svc in pending_services:
                if is_critical(svc):
                    print(f"[SKIPPED] {svc} requires a restart but matched a CRITICAL pattern.")
                else:
                    services_to_restart.add(svc)

    if not services_to_restart:
        print("No actionable services to restart. Exiting.")
        sys.exit(0)

    if args.noop:
        print("--- RUNNING IN NOOP (DRY-RUN) MODE ---")

    print(f"Target services to restart: {', '.join(services_to_restart)}")
    print("-" * 40)

    all_successful = True
    for service in services_to_restart:
        success = restart_service(service, args.noop)
        if not success:
            all_successful = False

    if not all_successful and not args.noop:
        sys.exit(1)

if __name__ == '__main__':
    main()
