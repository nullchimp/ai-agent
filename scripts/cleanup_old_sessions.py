#!/usr/bin/env python3
"""
Cleanup script for inactive sessions.
Deletes sessions that have been inactive for more than 30 days.
Run this script periodically (e.g., daily cron job) to maintain database health.
"""

from dotenv import load_dotenv
load_dotenv(override=True)

from datetime import datetime, timedelta, timezone
from core.db import get_connection_pool
from core.db.session import get_session_by_id, delete_session


def cleanup_old_sessions(days_inactive=30, dry_run=True):
    """
    Delete sessions inactive for more than specified days (T084).
    
    Args:
        days_inactive: Number of days of inactivity before deletion
        dry_run: If True, only report what would be deleted without actually deleting
    """
    pool = get_connection_pool()
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_inactive)
    
    print("=" * 60)
    print("SESSION CLEANUP SCRIPT")
    print("=" * 60)
    print(f"Mode: {'DRY RUN (no deletions)' if dry_run else 'LIVE (will delete)'}")
    print(f"Cutoff date: {cutoff_date.isoformat()}")
    print(f"Deleting sessions inactive since: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    try:
        with pool.get_connection() as db:
            # Find sessions inactive for more than specified days
            query = """
                MATCH (s:SESSION)
                WHERE s.last_activity < $cutoff_date AND s.is_active = true
                RETURN s.session_id, s.title, s.last_activity, s.conversation_count
                ORDER BY s.last_activity ASC
            """
            db._cur.execute(query, {"cutoff_date": cutoff_date.isoformat()})
            inactive_sessions = db._cur.fetchall()
            
            if not inactive_sessions:
                print("✅ No inactive sessions found. Database is clean!")
                return 0
            
            print(f"Found {len(inactive_sessions)} inactive sessions:")
            print()
            
            deleted_count = 0
            for session_id, title, last_activity, conv_count in inactive_sessions:
                days_ago = (datetime.now(timezone.utc) - datetime.fromisoformat(last_activity)).days
                print(f"  - {session_id[:16]}... | {title[:30]:<30} | {conv_count:>3} msgs | {days_ago} days ago")
                
                if not dry_run:
                    try:
                        delete_session(session_id)
                        deleted_count += 1
                    except Exception as e:
                        print(f"    ❌ Error deleting session {session_id}: {e}")
            
            print()
            if dry_run:
                print(f"DRY RUN: Would delete {len(inactive_sessions)} sessions")
                print("Run with --live flag to actually delete these sessions")
            else:
                print(f"✅ Successfully deleted {deleted_count}/{len(inactive_sessions)} sessions")
                if deleted_count < len(inactive_sessions):
                    print(f"⚠️  Failed to delete {len(inactive_sessions) - deleted_count} sessions")
            
            return len(inactive_sessions)
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return 0
    finally:
        print("=" * 60)


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    dry_run = True
    days_inactive = 30
    
    if "--live" in sys.argv:
        dry_run = False
        print("⚠️  LIVE MODE: Sessions will be permanently deleted!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Aborted.")
            sys.exit(0)
    
    if "--days" in sys.argv:
        try:
            days_idx = sys.argv.index("--days")
            days_inactive = int(sys.argv[days_idx + 1])
        except (ValueError, IndexError):
            print("Error: --days requires an integer argument")
            sys.exit(1)
    
    cleanup_old_sessions(days_inactive=days_inactive, dry_run=dry_run)
