#!/usr/bin/env python3
"""
Create database indexes for session storage feature.
Run this script once to set up the necessary indexes for optimal query performance.
"""

import os

try:
    import pymgclient
except ImportError:
    print("❌ Error: pymgclient not installed. Please install it with: pip install pymgclient")
    exit(1)

def create_indexes():
    """Create indexes for SESSION and DEBUG_EVENT nodes"""
    
    # Connect to database
    host = os.environ.get("MEMGRAPH_URI", "localhost")
    port = int(os.environ.get("MEMGRAPH_PORT", 7687))
    
    try:
        conn = pymgclient.connect(host=host, port=port, lazy=False)
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Failed to connect to Memgraph at {host}:{port}")
        print(f"   Error: {e}")
        print("   Make sure Memgraph is running: docker-compose -f docker/docker-compose.yml up -d memgraph")
        exit(1)
    
    print("=" * 60)
    print("CREATING DATABASE INDEXES")
    print("=" * 60)
    
    # Define indexes to create
    indexes = [
        # SESSION indexes
        ("SESSION", "session_id", "Session lookups by ID (most common query)"),
        ("SESSION", "user_id", "Session filtering by user (multi-user isolation)"),
        ("SESSION", "is_active", "Session filtering by active status"),
        ("SESSION", "last_activity", "Session cleanup by last activity"),
        
        # DEBUG_EVENT indexes
        ("DEBUG_EVENT", "event_id", "Debug event lookups by ID"),
        ("DEBUG_EVENT", "session_id", "Debug event lookups by session"),
        ("DEBUG_EVENT", "event_type", "Debug event filtering by type"),
        ("DEBUG_EVENT", "timestamp", "Debug event ordering by time"),
    ]
    
    created_count = 0
    skipped_count = 0
    
    for label, property_name, description in indexes:
        try:
            query = f"CREATE INDEX ON :{label}({property_name});"
            cursor.execute(query)
            conn.commit()
            print(f"✅ Created index on :{label}({property_name})")
            print(f"   Purpose: {description}")
            created_count += 1
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"⏭️  Index on :{label}({property_name}) already exists")
                skipped_count += 1
            else:
                print(f"❌ Failed to create index on :{label}({property_name}): {e}")
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: {created_count} created, {skipped_count} skipped")
    print("=" * 60)
    
    # Verify indexes
    print("\nVerifying indexes...")
    try:
        cursor.execute("SHOW INDEX INFO;")
        indexes_result = cursor.fetchall()
        print(f"\nTotal indexes in database: {len(indexes_result)}")
        for idx_info in indexes_result:
            print(f"  - {idx_info}")
    except Exception as e:
        print(f"Note: Could not verify indexes (command may not be supported): {e}")
    
    conn.close()
    print("\n✅ Database indexes setup complete!\n")

if __name__ == "__main__":
    create_indexes()
