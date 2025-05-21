#!/usr/bin/env python3
"""
Authentication enforcement validator for Memgraph.
This script verifies that Memgraph properly rejects invalid credentials.
"""
import os
import sys
import time
from typing import Tuple, Optional
import mgclient
from dotenv import load_dotenv

def try_connection(host: str, port: int, username: str, password: str, 
                  expect_success: bool = True) -> Tuple[bool, Optional[str]]:
    """Attempt connection with given credentials and verify expected outcome"""
    try:
        conn = mgclient.connect(host=host, port=port, username=username, password=password)
        
        if not expect_success:
            conn.close()
            return False, "Connection succeeded but should have failed with invalid credentials"
            
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("RETURN 'Connection successful!' AS message")
        message = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, message
    except Exception as e:
        if expect_success:
            return False, f"Connection failed but should have succeeded: {str(e)}"
        return True, f"Connection properly rejected: {str(e)}"

def validate_auth_enforcement() -> bool:
    """Validate that Memgraph authentication is properly enforced"""
    load_dotenv(override=True)
    
    host = os.environ.get("MEMGRAPH_URI", "127.0.0.1")
    port = int(os.environ.get("MEMGRAPH_PORT", "7687"))
    username = os.environ.get("MEMGRAPH_USERNAME", "memgraph")
    password = os.environ.get("MEMGRAPH_PASSWORD", "memgraph")
    
    if host == "localhost":
        host = "127.0.0.1"
        
    print(f"\n==== Authentication Enforcement Test ====")
    print(f"Testing Memgraph at {host}:{port}")
    
    # Test 1: Connect with correct credentials (should succeed)
    print("\nTest 1: Connecting with correct credentials...")
    success, message = try_connection(host, port, username, password, expect_success=True)
    if not success:
        print(f"❌ FAIL: {message}")
        return False
    print(f"✅ PASS: {message}")
    
    # Test 2: Connect with wrong password (should fail)
    print("\nTest 2: Connecting with wrong password...")
    success, message = try_connection(host, port, username, "wrong_password", expect_success=False)
    if not success:
        print(f"❌ FAIL: Authentication is not enforced! Connection with wrong password succeeded.")
        return False
    print(f"✅ PASS: {message}")
    
    # Test 3: Connect with wrong username (should fail)
    print("\nTest 3: Connecting with wrong username...")
    success, message = try_connection(host, port, "wrong_user", password, expect_success=False)
    if not success:
        print(f"❌ FAIL: Authentication is not enforced! Connection with wrong username succeeded.")
        return False
    print(f"✅ PASS: {message}")
    
    # Test 4: Connect with empty credentials (should fail)
    print("\nTest 4: Connecting with empty credentials...")
    success, message = try_connection(host, port, "", "", expect_success=False)
    if not success:
        print(f"❌ FAIL: Authentication is not enforced! Connection with empty credentials succeeded.")
        return False
    print(f"✅ PASS: {message}")
    
    print("\n✅ SUCCESS: Memgraph authentication is properly enforced!")
    return True

if __name__ == "__main__":
    if validate_auth_enforcement():
        sys.exit(0)
    else:
        print("\n❌ AUTHENTICATION NOT ENFORCED: Memgraph is accepting invalid credentials!")
        sys.exit(1)
