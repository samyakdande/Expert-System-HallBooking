"""Automatic cleanup of expired bookings."""
import sqlite3
from datetime import datetime, timedelta
from backend.database import get_connection

def cleanup_expired_bookings():
    """Remove bookings where the date is in the past, or date is today and end time has passed."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current date and time
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")  # e.g., "2026-04-15"
    current_time = now.strftime("%H:%M")  # e.g., "14:30"
    
    deleted_count = 0
    
    # Delete all bookings from past dates
    cursor.execute(
        "DELETE FROM bookings WHERE date < ?",
        (current_date,)
    )
    deleted_count += cursor.rowcount
    
    # Delete all bookings from today where end_time has passed
    cursor.execute(
        "DELETE FROM bookings WHERE date = ? AND end_time <= ?",
        (current_date, current_time)
    )
    deleted_count += cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return deleted_count

if __name__ == "__main__":
    count = cleanup_expired_bookings()
    print(f"Cleaned up {count} expired booking(s)")
