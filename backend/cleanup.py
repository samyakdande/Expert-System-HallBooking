"""Automatic cleanup of expired bookings."""
import sqlite3
from datetime import datetime, timedelta
from backend.database import get_connection

def cleanup_expired_bookings():
    """Remove bookings where the end time has passed."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current day and time
    now = datetime.now()
    current_day = now.strftime("%A")  # e.g., "Monday"
    current_time = now.strftime("%H:%M")  # e.g., "14:30"
    
    deleted_count = 0
    
    # For simplicity: Delete all bookings from today where end_time has passed
    cursor.execute(
        "DELETE FROM bookings WHERE day = ? AND end_time <= ?",
        (current_day, current_time)
    )
    deleted_count += cursor.rowcount
    
    # Also delete bookings from yesterday and earlier in the current week
    # This handles cases where bookings weren't cleaned up immediately
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    current_day_index = days_order.index(current_day)
    
    # If it's early in the week, also clean up from the end of last week
    if current_day_index <= 2:  # Monday, Tuesday, Wednesday
        # Clean up Friday, Saturday, Sunday from last week
        past_days = ["Friday", "Saturday", "Sunday"]
        if current_day == "Monday":
            past_days = ["Thursday", "Friday", "Saturday", "Sunday"]
        elif current_day == "Tuesday":
            past_days = ["Friday", "Saturday", "Sunday"]
        
        for day in past_days:
            if day != current_day:
                cursor.execute("DELETE FROM bookings WHERE day = ?", (day,))
                deleted_count += cursor.rowcount
    
    # Clean up earlier days in the current week
    for i in range(current_day_index):
        day = days_order[i]
        cursor.execute("DELETE FROM bookings WHERE day = ?", (day,))
        deleted_count += cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return deleted_count

if __name__ == "__main__":
    count = cleanup_expired_bookings()
    print(f"Cleaned up {count} expired booking(s)")
