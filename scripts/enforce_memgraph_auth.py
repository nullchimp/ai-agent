#!/usr/bin/env python3
"""
Authentication enforcement validator for Memgraph.
This script verifies that Memgraph properly rejects invalid credentials
and ensures the database is correctly configured for production security.
"""
import os
import sys
import time
from typing import Tuple, Optional
import mgclient
from dotenv import load_dotenv


class MemgraphConnectionError(Exception):
    """Raised when there are connection issues with Memgraph"""
    pass


class MemgraphAuthError(Exception):
    """Raised when authentication validation fails"""
    pass


def validate_credentials_format(username: str, password: str) -> None:
    """Validate that credentials meet security requirements"""
    if not username or not username.strip():
        raise MemgraphAuthError("Username cannot be empty")
    
    if not password or len(password) < 8:
        raise MemgraphAuthError("Password must be at least 8 characters long")
    
    if username.strip() == "memgraph" and password == "memgraph":
        print("⚠️  WARNING: Using default credentials - not recommended for production")


def wait_for_service(host: str, port: int, timeout: int = 300) -> bool:
    """Wait for Memgraph service to become available"""
    print(f"Waiting for Memgraph service at {host}:{port} (timeout: {timeout}s)...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✅ Service is accessible at {host}:{port}")
                return True
                
        except Exception as e:
            print(f"Service check failed: {e}")
            
        print(f"⏳ Service not ready, waiting... ({int(time.time() - start_time)}s elapsed)")
        time.sleep(10)
    
    print(f"❌ Service did not become available within {timeout}s")
    return False

def try_connection(host: str, port: int, username: str, password: str, 
                  expect_success: bool = True, timeout: int = 10) -> Tuple[bool, Optional[str]]:
    """Attempt connection with given credentials and verify expected outcome"""
    try:
        conn = mgclient.connect(
            host=host, 
            port=port, 
            username=username, 
            password=password,
            lazy=False  # Force immediate connection
        )
        
        if not expect_success:
            try:
                conn.close()
            except:
                pass
            return False, "Connection succeeded but should have failed with invalid credentials"
            
        # Test the connection with a simple query
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("RETURN 'Connection successful!' AS message")
        result = cursor.fetchone()
        message = result[0] if result else "Connection successful"
        cursor.close()
        conn.close()
        return True, message
        
    except mgclient.DatabaseError as e:
        error_msg = str(e).lower()
        if expect_success:
            if "authentication failed" in error_msg or "access denied" in error_msg:
                return False, f"Authentication failed unexpectedly: {str(e)}"
            elif "connection" in error_msg or "timeout" in error_msg:
                raise MemgraphConnectionError(f"Connection issue: {str(e)}")
            else:
                return False, f"Database error: {str(e)}"
        else:
            # For invalid credentials, we expect authentication failures
            if "authentication failed" in error_msg or "access denied" in error_msg:
                return True, f"Connection properly rejected: {str(e)}"
            else:
                return False, f"Unexpected error for invalid credentials: {str(e)}"
                
    except Exception as e:
        error_msg = str(e).lower()
        if expect_success:
            if "connection" in error_msg or "timeout" in error_msg:
                raise MemgraphConnectionError(f"Connection issue: {str(e)}")
            else:
                return False, f"Unexpected error: {str(e)}"
        else:
            # For invalid credentials, any connection failure is acceptable
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
    
    try:
        validate_credentials_format(username, password)
    except MemgraphAuthError as e:
        print(f"❌ FAIL: Credential validation failed: {e}")
        return False
    
    # Wait for service to be available
    if not wait_for_service(host, port):
        print("❌ FAIL: Service is not accessible")
        return False
    
    # Additional wait for Memgraph to fully initialize
    print("⏳ Waiting for Memgraph to fully initialize...")
    time.sleep(30)
    
    try:
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
            print("❌ FAIL: Authentication is not enforced! Connection with wrong password succeeded.")
            return False
        print(f"✅ PASS: {message}")
        
        # Test 3: Connect with wrong username (should fail)
        print("\nTest 3: Connecting with wrong username...")
        success, message = try_connection(host, port, "wrong_user", password, expect_success=False)
        if not success:
            print("❌ FAIL: Authentication is not enforced! Connection with wrong username succeeded.")
            return False
        print(f"✅ PASS: {message}")
        
        # Test 4: Connect with empty credentials (should fail)
        print("\nTest 4: Connecting with empty credentials...")
        success, message = try_connection(host, port, "", "", expect_success=False)
        if not success:
            print("❌ FAIL: Authentication is not enforced! Connection with empty credentials succeeded.")
            return False
        print(f"✅ PASS: {message}")
        
        # Test 5: Connect with weak password (should fail if using production config)
        print("\nTest 5: Connecting with weak password...")
        success, message = try_connection(host, port, username, "123", expect_success=False)
        if not success:
            print("❌ FAIL: Authentication is not enforced! Connection with weak password succeeded.")
            return False
        print(f"✅ PASS: {message}")
        
        print("\n✅ SUCCESS: Memgraph authentication is properly enforced!")
        return True
        
    except MemgraphConnectionError as e:
        print(f"❌ FAIL: Connection issue: {e}")
        print("This might indicate the service is not properly deployed or accessible.")
        return False
    except Exception as e:
        print(f"❌ FAIL: Unexpected error during testing: {e}")
        return False

if __name__ == "__main__":
    if validate_auth_enforcement():
        sys.exit(0)
    else:
        print("\n❌ AUTHENTICATION NOT ENFORCED: Memgraph is accepting invalid credentials!")
        sys.exit(1)
