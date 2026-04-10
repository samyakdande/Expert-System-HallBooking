import sqlite3

# Path to the SQLite database file used for all bookings
DB_PATH = "bookings.db"


def get_connection() -> sqlite3.Connection:
    """Return a connection to the bookings SQLite database.

    Sets row_factory to sqlite3.Row so that query results can be accessed
    by column name (e.g. row["hall"]) in addition to positional index.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the bookings table if it does not already exist.

    Safe to call multiple times — the IF NOT EXISTS clause makes it
    idempotent, so calling it on every app startup is fine.

    Table schema:
        id         INTEGER  PRIMARY KEY AUTOINCREMENT
        hall       TEXT     NOT NULL
        day        TEXT     NOT NULL
        start_time TEXT     NOT NULL
        end_time   TEXT     NOT NULL
        booked_by  TEXT     NOT NULL
        purpose    TEXT     NOT NULL
    """
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                hall       TEXT    NOT NULL,
                day        TEXT    NOT NULL,
                start_time TEXT    NOT NULL,
                end_time   TEXT    NOT NULL,
                booked_by  TEXT    NOT NULL,
                purpose    TEXT    NOT NULL
            )
            """
        )
        conn.commit()
