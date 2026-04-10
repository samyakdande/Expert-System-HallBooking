"""Database migration script to add the purpose column to existing databases."""
import sqlite3
import os

DB_PATH = "bookings.db"

def migrate():
    """Add purpose column to existing bookings table if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        print("No existing database found. Will be created on first run.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if purpose column exists
    cursor.execute("PRAGMA table_info(bookings)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'purpose' not in columns:
        print("Adding 'purpose' column to bookings table...")
        try:
            cursor.execute("ALTER TABLE bookings ADD COLUMN purpose TEXT DEFAULT 'Not specified'")
            conn.commit()
            print("✓ Migration successful! Purpose column added.")
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            conn.rollback()
    else:
        print("✓ Database already has purpose column. No migration needed.")
    
    conn.close()

if __name__ == "__main__":
    migrate()
