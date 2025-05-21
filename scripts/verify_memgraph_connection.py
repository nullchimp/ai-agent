from dotenv import load_dotenv
import os
import mgclient
import sys
import time
from typing import Tuple, Optional

def verify_memgraph_connection(max_retries: int = 5, retry_delay: int = 5) -> Tuple[bool, Optional[str]]:
    host = os.environ.get("MEMGRAPH_URI", "127.0.0.1")
    port = int(os.environ.get("MEMGRAPH_PORT", "7687"))
    username = "test" or os.environ.get("MEMGRAPH_USERNAME", "memgraph")
    password = os.environ.get("MEMGRAPH_PASSWORD", "memgraph")
    
    print(f"Verifying connection to Memgraph at {host}:{port}")

    if host == "localhost":
        host = "127.0.0.1"
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries}: Connecting to Memgraph")
            conn = mgclient.connect(
                host=host, 
                port=port,
                username=username,
                password=password
            )
            
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Basic connectivity check
            cursor.execute("RETURN 'Connection successful!' AS message")
            result = cursor.fetchone()[0]
            print(f"Success: {result}")
            
            # Validate authentication works
            cursor.execute("CREATE (n:TestNode {name: 'connection_test'}) RETURN n")
            cursor.execute("MATCH (n:TestNode {name: 'connection_test'}) DELETE n")
            print("Authentication validation successful")
            
            cursor.close()
            conn.close()
            return True, None
        except Exception as e:
            error_message = f"Connection attempt {attempt} failed: {str(e)}"
            print(error_message)
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                return False, error_message

if __name__ == "__main__":
    load_dotenv(override=True)
    success, error = verify_memgraph_connection()
    
    if not success:
        print(f"Failed to connect to Memgraph: {error}")
        sys.exit(1)
        
    print("Successfully connected to and validated Memgraph")
    sys.exit(0)
