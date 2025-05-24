#!/usr/bin/env python3

import os
import sys
import time
import mgclient
from typing import Optional, Dict, Any


def get_external_ip() -> Optional[str]:
    import subprocess
    try:
        result = subprocess.run([
            "kubectl", "get", "service", "memgraph", 
            "-o", "jsonpath={.status.loadBalancer.ingress[0].ip}"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass
    return None


def get_service_status() -> Dict[str, Any]:
    import subprocess
    try:
        result = subprocess.run([
            "kubectl", "get", "service", "memgraph", 
            "-o", "json"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
    except Exception:
        pass
    return {}


def test_authentication_enforcement(host: str, port: int, username: str, password: str) -> bool:
    print("\n🔐 Testing authentication enforcement...")
    
    # Test 1: Valid credentials should work
    try:
        conn = mgclient.connect(
            host=host,
            port=port,
            username=username,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("RETURN 'Valid auth test' AS message")
        result = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"✅ Valid credentials accepted: {result}")
    except Exception as e:
        print(f"❌ Valid credentials failed: {e}")
        return False
    
    # Test 2: Invalid credentials should fail
    try:
        conn = mgclient.connect(
            host=host,
            port=port,
            username=username,
            password="wrong_password_12345"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("RETURN 'Should not work' AS message")
        cursor.close()
        conn.close()
        print("❌ Authentication not enforced - invalid credentials were accepted!")
        return False
    except Exception:
        print("✅ Authentication properly enforced - invalid credentials rejected")
    
    # Test 3: No credentials should fail
    try:
        conn = mgclient.connect(host=host, port=port)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("RETURN 'Should not work' AS message")
        cursor.close()
        conn.close()
        print("❌ Authentication not enforced - no credentials were accepted!")
        return False
    except Exception:
        print("✅ Authentication properly enforced - no credentials rejected")
    
    return True


def test_basic_operations(host: str, port: int, username: str, password: str) -> bool:
    print("\n🔧 Testing basic database operations...")
    
    try:
        conn = mgclient.connect(
            host=host,
            port=port,
            username=username,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("RETURN 'Connection successful!' AS message")
        result = cursor.fetchone()[0]
        print(f"✅ Basic query: {result}")
        
        # Test node creation and deletion
        test_node_name = f"test_node_{int(time.time())}"
        cursor.execute(f"CREATE (n:TestNode {{name: '{test_node_name}'}}) RETURN n.name")
        created_name = cursor.fetchone()[0]
        print(f"✅ Node creation: {created_name}")
        
        # Test node retrieval
        cursor.execute(f"MATCH (n:TestNode {{name: '{test_node_name}'}}) RETURN n.name")
        retrieved_name = cursor.fetchone()[0]
        print(f"✅ Node retrieval: {retrieved_name}")
        
        # Test node deletion
        cursor.execute(f"MATCH (n:TestNode {{name: '{test_node_name}'}}) DELETE n")
        print("✅ Node deletion completed")
        
        # Verify deletion
        cursor.execute(f"MATCH (n:TestNode {{name: '{test_node_name}'}}) RETURN count(n)")
        count = cursor.fetchone()[0]
        if count == 0:
            print("✅ Node deletion verified")
        else:
            print(f"❌ Node deletion failed - count: {count}")
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Basic operations failed: {e}")
        return False


def validate_memgraph_deployment(max_retries: int = 3, retry_delay: int = 10) -> bool:
    print("🚀 Starting Memgraph deployment validation...")
    
    # Get credentials from environment
    username = os.environ.get("DB_USERNAME") or os.environ.get("MEMGRAPH_USERNAME", "memgraph")
    password = os.environ.get("DB_PASSWORD") or os.environ.get("MEMGRAPH_PASSWORD", "memgraph")
    
    print(f"📝 Using username: {username}")
    print(f"🔑 Password configured: {'Yes' if password else 'No'}")
    
    # Validate credentials
    if not username or not password:
        print("❌ ERROR: Username and password must be provided")
        return False
    
    if len(password) < 8:
        print("❌ ERROR: Password must be at least 8 characters long")
        return False
    
    print("✅ Credentials validation passed")
    
    # Get external IP
    print("\n🌐 Getting external IP address...")
    external_ip = None
    
    for attempt in range(1, max_retries + 1):
        external_ip = get_external_ip()
        if external_ip:
            print(f"✅ External IP found: {external_ip}")
            break
        else:
            print(f"⏳ Attempt {attempt}/{max_retries}: Waiting for external IP...")
            if attempt < max_retries:
                time.sleep(retry_delay)
    
    if not external_ip:
        print("❌ ERROR: Could not get external IP address")
        service_status = get_service_status()
        if service_status:
            print("📋 Service status:", service_status.get("status", {}))
        return False
    
    # Test connection and authentication
    port = 7687
    
    print(f"\n🔌 Testing connection to {external_ip}:{port}")
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"⏳ Connection attempt {attempt}/{max_retries}...")
            
            # Test authentication enforcement
            if not test_authentication_enforcement(external_ip, port, username, password):
                if attempt < max_retries:
                    print(f"🔄 Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                return False
            
            # Test basic operations
            if not test_basic_operations(external_ip, port, username, password):
                if attempt < max_retries:
                    print(f"🔄 Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                return False
            
            print("\n🎉 All validation tests passed!")
            print("\n📊 Connection Summary:")
            print(f"  🔗 Bolt Protocol: {external_ip}:7687")
            print(f"  🌐 HTTP API: {external_ip}:7444")
            print(f"  🖥️  Memgraph Lab UI: {external_ip}:3000")
            print(f"  👤 Username: {username}")
            print(f"  🔒 Authentication: Enforced")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(f"🔄 Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("💥 All connection attempts failed")
                return False
    
    return False


if __name__ == "__main__":
    print("🔍 DEBUG: Script started")
    try:
        success = validate_memgraph_deployment()
        if success:
            print("\n✅ Memgraph deployment validation PASSED")
            sys.exit(0)
        else:
            print("\n❌ Memgraph deployment validation FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"💥 Script error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
