from core.db.connection_pool import get_connection_pool

def process_user_request(user_id: str, query: str) -> dict:
    """Example of using connection pool in request processing"""
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        # Execute database operations within the connection context
        db._execute(
            "MATCH (u:User {id: $user_id}) RETURN u", 
            {"user_id": user_id}
        )
        
        result = db._cur.fetchone()
        
        if result:
            # Process user query
            db._execute(
                "CREATE (q:Query {text: $text, user_id: $user_id, timestamp: datetime()})",
                {"text": query, "user_id": user_id}
            )
            
            return {"status": "success", "user": result[0].properties}
        else:
            return {"status": "error", "message": "User not found"}


async def batch_processing_example():
    """Example of using connection pool for batch operations"""
    pool = get_connection_pool()
    
    batch_data = [
        {"id": "1", "name": "Document 1"},
        {"id": "2", "name": "Document 2"},
        {"id": "3", "name": "Document 3"},
    ]
    
    with pool.get_connection() as db:
        for item in batch_data:
            db._execute(
                "CREATE (d:Document {id: $id, name: $name})",
                item
            )


def application_cleanup():
    """Call this when shutting down your application"""
    from core.db.connection_pool import close_connection_pool
    close_connection_pool()
