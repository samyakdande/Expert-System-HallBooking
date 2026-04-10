import sqlite3
from typing import Optional


def _row_to_dict(row) -> dict:
    """Convert a sqlite3.Row (or None) to a plain dict with booking keys."""
    if row is None:
        return None
    return {
        "id": row["id"],
        "hall": row["hall"],
        "day": row["day"],
        "start_time": row["start_time"],
        "end_time": row["end_time"],
        "booked_by": row["booked_by"],
        "purpose": row["purpose"],
    }


def create_booking(
    conn: sqlite3.Connection,
    hall: str,
    day: str,
    start_time: str,
    end_time: str,
    booked_by: str,
    purpose: str,
) -> int:
    """Insert a new booking row into the bookings table.

    Parameters
    ----------
    conn       : active SQLite connection (may be an in-memory DB for tests)
    hall       : hall name, e.g. "Hall A"
    day        : day of the week, e.g. "Monday"
    start_time : booking start, e.g. "08:30"
    end_time   : booking end,   e.g. "10:30"
    booked_by  : name of the person making the booking
    purpose    : reason for booking, e.g. "Team Meeting"

    Returns
    -------
    int  The auto-generated id of the newly inserted row.
    """
    cursor = conn.execute(
        """
        INSERT INTO bookings (hall, day, start_time, end_time, booked_by, purpose)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (hall, day, start_time, end_time, booked_by, purpose),
    )
    conn.commit()
    return cursor.lastrowid


def get_booking(
    conn: sqlite3.Connection,
    hall: str,
    day: str,
    start_time: str,
) -> Optional[dict]:
    """Return a single booking row matching hall + day + start_time, or None.

    Parameters
    ----------
    conn       : active SQLite connection
    hall       : hall name to look up
    day        : day of the week to look up
    start_time : slot start time to look up

    Returns
    -------
    dict with keys (id, hall, day, start_time, end_time, booked_by, purpose), or None
    if no matching booking exists.
    """
    row = conn.execute(
        """
        SELECT id, hall, day, start_time, end_time, booked_by, purpose
        FROM bookings
        WHERE hall = ? AND day = ? AND start_time = ?
        """,
        (hall, day, start_time),
    ).fetchone()
    return _row_to_dict(row)


def get_all_bookings(conn: sqlite3.Connection) -> list[dict]:
    """Return every booking row in the database as a list of dicts.

    Parameters
    ----------
    conn : active SQLite connection

    Returns
    -------
    List of dicts, each with keys: id, hall, day, start_time, end_time, booked_by, purpose.
    Returns an empty list when no bookings exist.
    """
    rows = conn.execute(
        "SELECT id, hall, day, start_time, end_time, booked_by, purpose FROM bookings"
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_bookings_by_hall(conn: sqlite3.Connection, hall: str) -> list[dict]:
    """Return all bookings for a specific hall.

    Parameters
    ----------
    conn : active SQLite connection
    hall : hall name to filter by, e.g. "Hall B"

    Returns
    -------
    List of dicts for every booking that belongs to the given hall.
    Returns an empty list if the hall has no bookings.
    """
    rows = conn.execute(
        """
        SELECT id, hall, day, start_time, end_time, booked_by, purpose
        FROM bookings
        WHERE hall = ?
        """,
        (hall,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_bookings_by_slot(
    conn: sqlite3.Connection,
    day: str,
    start_time: str,
) -> list[dict]:
    """Return all bookings for a given day and start-time slot.

    Parameters
    ----------
    conn       : active SQLite connection
    day        : day of the week to filter by, e.g. "Tuesday"
    start_time : slot start time to filter by, e.g. "10:30"

    Returns
    -------
    List of dicts for every booking that falls on the given day and slot.
    Returns an empty list if no halls are booked at that day/slot.
    """
    rows = conn.execute(
        """
        SELECT id, hall, day, start_time, end_time, booked_by, purpose
        FROM bookings
        WHERE day = ? AND start_time = ?
        """,
        (day, start_time),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]
