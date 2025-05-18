#!/usr/bin/env python3
"""
Utility script to get Memgraph connection information for the Azure deployment.
This script generates configuration for connecting to the deployed Memgraph database
using the stable DNS name instead of IP address.

Usage:
    python scripts/get_memgraph_connection.py [environment]

Arguments:
    environment - Optional. The deployment environment (default: dev)

Example:
    python scripts/get_memgraph_connection.py
    python scripts/get_memgraph_connection.py dev
    python scripts/get_memgraph_connection.py prod
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Optional


def get_connection_info(env: str = "dev") -> Dict[str, str]:
    """Get Memgraph connection information for the given environment."""
    location = os.environ.get("AZURE_LOCATION", "germanywestcentral")
    
    # Construct the DNS name based on Azure naming conventions
    dns_name = f"memgraph-aiagent-{env}.{location}.cloudapp.azure.com"
    
    return {
        "MEMGRAPH_URI": dns_name,
        "MEMGRAPH_PORT": "7687",
        "MEMGRAPH_USERNAME": os.environ.get("MEMGRAPH_USERNAME", "memgraph"),
        "MEMGRAPH_PASSWORD": os.environ.get("MEMGRAPH_PASSWORD", ""),
        "MEMGRAPH_BOLT_URL": f"bolt://{dns_name}:7687",
        "MEMGRAPH_HTTP_URL": f"http://{dns_name}:7444",
        "MEMGRAPH_LAB_URL": f"http://{dns_name}:3000"
    }


def update_env_file(connection_info: Dict[str, str], env_file: Optional[Path] = None) -> None:
    """Update .env file with Memgraph connection information."""
    if env_file is None:
        env_file = Path(".env")
    
    # Read existing .env file
    if env_file.exists():
        with open(env_file, "r") as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Update or add Memgraph connection variables
    updated_vars = set()
    for i, line in enumerate(lines):
        for key in connection_info:
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={connection_info[key]}\n"
                updated_vars.add(key)
    
    # Add missing variables
    for key, value in connection_info.items():
        if key not in updated_vars:
            lines.append(f"{key}={value}\n")
    
    # Write updated .env file
    with open(env_file, "w") as f:
        f.writelines(lines)
    
    print(f"Updated {env_file} with Memgraph connection information.")


def print_connection_info(connection_info: Dict[str, str]) -> None:
    """Print Memgraph connection information in a user-friendly format."""
    print("\nMemgraph Connection Information:")
    print("=" * 40)
    print(f"DNS Name: {connection_info['MEMGRAPH_URI']}")
    print(f"Port: {connection_info['MEMGRAPH_PORT']}")
    print(f"Username: {connection_info['MEMGRAPH_USERNAME']}")
    print(f"Password: {'*' * 8 if connection_info['MEMGRAPH_PASSWORD'] else '(not set)'}")
    print("\nConnection URLs:")
    print(f"Bolt URL: {connection_info['MEMGRAPH_BOLT_URL']}")
    print(f"HTTP API: {connection_info['MEMGRAPH_HTTP_URL']}")
    print(f"Lab UI: {connection_info['MEMGRAPH_LAB_URL']}")
    print("\nPython Connection Example:")
    print("```python")
    print("from dotenv import load_dotenv")
    print("load_dotenv()")
    print("from core.rag.dbhandler.memgraph import MemGraphClient")
    print("import os")
    print("")
    print("# Connect to remote Memgraph database using DNS name")
    print("db = MemGraphClient(")
    print("    host=os.environ.get('MEMGRAPH_URI'),")
    print("    port=int(os.environ.get('MEMGRAPH_PORT', 7687)),")
    print("    username=os.environ.get('MEMGRAPH_USERNAME'),")
    print("    password=os.environ.get('MEMGRAPH_PASSWORD'),")
    print(")")
    print("```")
    print("\nTo save these settings to your .env file:")
    print(f"python {sys.argv[0]} {args.environment} --update-env")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get Memgraph connection information")
    parser.add_argument("environment", nargs="?", default="dev", help="Deployment environment (default: dev)")
    parser.add_argument("--update-env", action="store_true", help="Update .env file with connection information")
    
    args = parser.parse_args()
    connection_info = get_connection_info(args.environment)
    
    if args.update_env:
        update_env_file(connection_info)
    else:
        print_connection_info(connection_info)
