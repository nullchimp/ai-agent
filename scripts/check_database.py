from dotenv import load_dotenv
load_dotenv(override=True)

import os
from core.db.handler.memgraph import MemGraphClient

db = MemGraphClient(
    host=os.environ.get("MEMGRAPH_URI", "localhost"),
    port=int(os.environ.get("MEMGRAPH_PORT", 7687)),
    username=os.environ.get("MEMGRAPH_USERNAME", "nullchimp"),
    password=os.environ.get("MEMGRAPH_PASSWORD", "nullchimp"),
).connect()

print("=" * 60)
print("DATABASE INSPECTION")
print("=" * 60)

print("\n1. Total nodes:")
db._cur.execute("MATCH (n) RETURN count(n) as total")
result = db._cur.fetchone()
print(f"   Total nodes: {result[0]}")

print("\n2. Node labels and counts:")
db._cur.execute("MATCH (n) RETURN labels(n) as labels, count(*) as count ORDER BY count DESC")
for row in db._cur.fetchall():
    labels = row[0] if row[0] else ['(no label)']
    print(f"   {labels}: {row[1]}")

print("\n3. Sample nodes (first 5):")
db._cur.execute("MATCH (n) RETURN n LIMIT 5")
for i, row in enumerate(db._cur.fetchall(), 1):
    node = row[0]
    print(f"\n   Node {i}:")
    print(f"   Labels: {node.labels}")
    print(f"   Properties: {dict(node.properties)}")

print("\n4. All property keys:")
db._cur.execute("MATCH (n) UNWIND keys(n) as key RETURN DISTINCT key ORDER BY key")
keys = [row[0] for row in db._cur.fetchall()]
print(f"   {', '.join(keys)}")

print("\n5. Relationships:")
db._cur.execute("MATCH ()-[r]->() RETURN DISTINCT type(r) as rel_type, count(*) as count ORDER BY count DESC")
rels = db._cur.fetchall()
if rels:
    for row in rels:
        print(f"   {row[0]}: {row[1]}")
else:
    print("   No relationships found")

db.close()
print("\n" + "=" * 60)
