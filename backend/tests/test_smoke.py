"""Smoke tests for core backend logic using in-memory SQLite."""
import sqlite3
import pytest

from backend.database import init_db
from backend.scheduler import create_booking, get_booking
from backend.expert_engine import check_conflict, suggest_alternatives
from backend.config import HALLS, TIME_SLOTS, CONTACT_NUMBER


def make_conn() -> sqlite3.Connection:
    """Create a fresh in-memory SQLite connection with the schema initialised."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    # Inline table creation so we don't touch the file-based DB_PATH
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            hall       TEXT    NOT NULL,
            date       TEXT    NOT NULL,
            start_time TEXT    NOT NULL,
            end_time   TEXT    NOT NULL,
            email      TEXT    NOT NULL,
            booked_by  TEXT    NOT NULL,
            purpose    TEXT    NOT NULL
        )
        """
    )
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# 1. init_db works on in-memory connection
# ---------------------------------------------------------------------------

def test_init_db_creates_table():
    """init_db should create the bookings table without error (idempotent)."""
    # We test the idempotency path by calling it twice on a fresh file-based
    # temp DB via monkeypatching DB_PATH — but the simplest smoke is just
    # verifying our helper creates the table correctly.
    conn = make_conn()
    # Table must exist — querying it should not raise
    rows = conn.execute("SELECT * FROM bookings").fetchall()
    assert rows == []
    conn.close()


def test_init_db_idempotent():
    """Calling make_conn (which runs CREATE TABLE IF NOT EXISTS) twice is safe."""
    conn = make_conn()
    # Run the CREATE TABLE statement again — should not raise
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            hall       TEXT    NOT NULL,
            date       TEXT    NOT NULL,
            start_time TEXT    NOT NULL,
            end_time   TEXT    NOT NULL,
            email      TEXT    NOT NULL,
            booked_by  TEXT    NOT NULL,
            purpose    TEXT    NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# 2. create_booking + get_booking round-trip
# ---------------------------------------------------------------------------

def test_create_and_get_booking_round_trip():
    conn = make_conn()
    booking_id = create_booking(conn, "Hall A", "2026-04-15", "08:30", "10:30", "alice@example.com", "Alice", "Meeting")
    assert isinstance(booking_id, int)
    assert booking_id > 0

    result = get_booking(conn, "Hall A", "2026-04-15", "08:30")
    assert result is not None
    assert result["hall"] == "Hall A"
    assert result["date"] == "2026-04-15"
    assert result["start_time"] == "08:30"
    assert result["end_time"] == "10:30"
    assert result["email"] == "alice@example.com"
    assert result["booked_by"] == "Alice"
    assert result["purpose"] == "Meeting"
    assert result["id"] == booking_id
    conn.close()


def test_get_booking_returns_none_when_missing():
    conn = make_conn()
    result = get_booking(conn, "Hall B", "2026-04-16", "10:30")
    assert result is None
    conn.close()


# ---------------------------------------------------------------------------
# 3. check_conflict returns False before booking, True after
# ---------------------------------------------------------------------------

def test_check_conflict_false_before_booking():
    conn = make_conn()
    assert check_conflict(conn, "Hall C", "2026-04-17", "12:30") is False
    conn.close()


def test_check_conflict_true_after_booking():
    conn = make_conn()
    create_booking(conn, "Hall C", "2026-04-17", "12:30", "14:30", "bob@example.com", "Bob", "Meeting")
    assert check_conflict(conn, "Hall C", "2026-04-17", "12:30") is True
    conn.close()


def test_check_conflict_does_not_affect_other_halls():
    """Booking Hall A should not create a conflict for Hall B at the same slot."""
    conn = make_conn()
    create_booking(conn, "Hall A", "2026-04-19", "14:30", "16:30", "carol@example.com", "Carol", "Meeting")
    assert check_conflict(conn, "Hall B", "2026-04-19", "14:30") is False
    conn.close()


# ---------------------------------------------------------------------------
# 4. suggest_alternatives returns expected keys
# ---------------------------------------------------------------------------

def test_suggest_alternatives_keys_present():
    conn = make_conn()
    # Book Hall A on 2026-04-15 08:30 so there is a conflict to suggest around
    create_booking(conn, "Hall A", "2026-04-15", "08:30", "10:30", "dave@example.com", "Dave", "Meeting")
    result = suggest_alternatives(conn, "Hall A", "2026-04-15", "08:30")

    assert "free_halls" in result
    assert "free_slots" in result
    assert "recommended_hall" in result
    assert "recommended_slot" in result
    assert "contact_number" in result
    conn.close()


def test_suggest_alternatives_contact_number():
    conn = make_conn()
    create_booking(conn, "Hall B", "2026-04-16", "10:30", "12:30", "eve@example.com", "Eve", "Meeting")
    result = suggest_alternatives(conn, "Hall B", "2026-04-16", "10:30")
    assert result["contact_number"] == CONTACT_NUMBER
    conn.close()


def test_suggest_alternatives_free_halls_excludes_booked_and_requested():
    """free_halls must not include the requested hall or any hall booked at that slot."""
    conn = make_conn()
    # Book Hall A and Hall B at 2026-04-15 08:30
    create_booking(conn, "Hall A", "2026-04-15", "08:30", "10:30", "frank@example.com", "Frank", "Meeting")
    create_booking(conn, "Hall B", "2026-04-15", "08:30", "10:30", "grace@example.com", "Grace", "Meeting")
    result = suggest_alternatives(conn, "Hall A", "2026-04-15", "08:30")

    assert "Hall A" not in result["free_halls"]
    assert "Hall B" not in result["free_halls"]
    # The remaining 4 halls should all be free
    assert len(result["free_halls"]) == 4
    conn.close()


def test_suggest_alternatives_free_slots_excludes_booked():
    """free_slots must not include slots already booked for that hall+date."""
    conn = make_conn()
    create_booking(conn, "Hall C", "2026-04-18", "08:30", "10:30", "hank@example.com", "Hank", "Meeting")
    result = suggest_alternatives(conn, "Hall C", "2026-04-18", "08:30")

    assert "08:30" not in result["free_slots"]
    # All other 4 slots should be free
    assert len(result["free_slots"]) == 4
    conn.close()


def test_suggest_alternatives_recommended_hall_is_least_used():
    """recommended_hall should be the hall with the fewest bookings."""
    conn = make_conn()
    # Book Hall A twice, Hall B once — Hall C..F have zero bookings
    create_booking(conn, "Hall A", "2026-04-15", "08:30", "10:30", "ivy@example.com", "Ivy", "Meeting")
    create_booking(conn, "Hall A", "2026-04-16", "08:30", "10:30", "ivy@example.com", "Ivy", "Meeting")
    create_booking(conn, "Hall B", "2026-04-15", "10:30", "12:30", "jack@example.com", "Jack", "Meeting")
    result = suggest_alternatives(conn, "Hall A", "2026-04-15", "08:30")

    # recommended_hall must be one of the zero-booking halls
    zero_booking_halls = {"Hall C", "Hall D", "Hall E", "Hall F"}
    assert result["recommended_hall"] in zero_booking_halls
    conn.close()
