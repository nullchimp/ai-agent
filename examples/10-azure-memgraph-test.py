from dotenv import load_dotenv
load_dotenv(override=True)

import os
import mgclient
import sys
import time

def test_memgraph_connection(max_retries=3, retry_delay=5) -> bool:
    host = os.environ.get("MEMGRAPH_URI", "127.0.0.1")
    port = int(os.environ.get("MEMGRAPH_PORT", "7687"))
    username = os.environ.get("MEMGRAPH_USERNAME", "memgraph")
    password = os.environ.get("MEMGRAPH_PASSWORD", "memgraph")
    
    print(f"Testing connection to Memgraph at {host}:{port} with username: {username}")

    # Convert localhost to IP if needed
    if host == "localhost":
        host = "127.0.0.1"
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries}: Connecting to Memgraph at {host}:{port}")
            conn = mgclient.connect(
                host=host, 
                port=port,
                username=username,
                password=password
            )
            
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Test a basic query
            cursor.execute("RETURN 'Connection successful!' AS message")
            result = cursor.fetchone()[0]
            print(f"Success: {result}")
            
            # Additional test query to verify data manipulation works
            print("Testing data manipulation...")
            cursor.execute("CREATE (n:TestNode {name: 'connection_test'}) RETURN n")
            cursor.execute("MATCH (n:TestNode {name: 'connection_test'}) DELETE n")
            print("Data manipulation successful")
            
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Connection attempt {attempt} failed: {str(e)}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("All connection attempts failed")
                return False

if __name__ == "__main__":
    success = test_memgraph_connection()
    if not success:
        print("Failed to connect to Memgraph")
        sys.exit(1)
    print("Successfully connected to Memgraph")
    sys.exit(0)