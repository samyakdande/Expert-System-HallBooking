"""API integration tests for the Hall Booking Expert System.

Uses FastAPI TestClient with an in-memory SQLite database via monkeypatching
so no file-based DB is touched during tests.
"""
import sqlite3
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import DAYS, TIME_SLOTS, HALLS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_BOOKING = {
    "hall": "Hall A",
    "day": "Monday",
    "start_time": "08:30",
    "end_time": "10:30",
    "booked_by": "Alice",
}


class _NoCloseConn:
    """Thin proxy around sqlite3.Connection that makes close() a no-op.

    main.py calls conn.close() in a finally block after every request.
    For an in-memory DB that would destroy all data between requests, so we
    intercept close() while forwarding every other attribute to the real conn.
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # Delegate everything to the real connection …
    def __getattr__(self, name):
        return getattr(self._conn, name)

    # … except close(), which we silence.
    def close(self):
        pass  # intentional no-op

    def real_close(self):
        """Actually close the underlying connection (called after the test)."""
        self._conn.close()


def make_mem_conn() -> _NoCloseConn:
    """Return a fresh in-memory SQLite connection (wrapped) with the bookings schema."""
    raw = sqlite3.connect(":memory:", check_same_thread=False)
    raw.row_factory = sqlite3.Row
    raw.execute(
        """CREATE TABLE IF NOT EXISTS bookings (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            hall       TEXT NOT NULL,
            day        TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time   TEXT NOT NULL,
            booked_by  TEXT NOT NULL
        )"""
    )
    raw.commit()
    return _NoCloseConn(raw)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def client(monkeypatch):
    """TestClient backed by a fresh in-memory SQLite DB for each test."""
    mem_conn = make_mem_conn()

    monkeypatch.setattr("backend.main.get_connection", lambda: mem_conn)
    monkeypatch.setattr("backend.main.init_db", lambda: None)

    yield TestClient(app)

    mem_conn.real_close()


# ---------------------------------------------------------------------------
# POST /book — success (201)
# ---------------------------------------------------------------------------

def test_book_valid_returns_201(client):
    """A valid booking request must return HTTP 201."""
    response = client.post("/book", json=VALID_BOOKING)
    assert response.status_code == 201


def test_book_valid_response_body(client):
    """A successful booking response must contain a confirmation message and booking details."""
    response = client.post("/book", json=VALID_BOOKING)
    body = response.json()
    assert body["message"] == "Booking confirmed"
    assert body["booking"]["hall"] == VALID_BOOKING["hall"]
    assert body["booking"]["day"] == VALID_BOOKING["day"]
    assert body["booking"]["start_time"] == VALID_BOOKING["start_time"]
    assert body["booking"]["booked_by"] == VALID_BOOKING["booked_by"]
    assert "id" in body["booking"]


# ---------------------------------------------------------------------------
# POST /book — conflict (409)
# ---------------------------------------------------------------------------

def test_book_conflict_returns_409(client):
    """A duplicate booking for the same hall/day/slot must return HTTP 409."""
    client.post("/book", json=VALID_BOOKING)  # first booking succeeds
    response = client.post("/book", json=VALID_BOOKING)  # second is a conflict
    assert response.status_code == 409


def test_book_conflict_response_has_free_halls(client):
    """409 response detail must include a free_halls list."""
    client.post("/book", json=VALID_BOOKING)
    response = client.post("/book", json=VALID_BOOKING)
    detail = response.json()["detail"]
    assert "free_halls" in detail
    assert isinstance(detail["free_halls"], list)


def test_book_conflict_response_has_free_slots(client):
    """409 response detail must include a free_slots list."""
    client.post("/book", json=VALID_BOOKING)
    response = client.post("/book", json=VALID_BOOKING)
    detail = response.json()["detail"]
    assert "free_slots" in detail
    assert isinstance(detail["free_slots"], list)


def test_book_conflict_response_has_contact_number(client):
    """409 response detail must include the contact_number field."""
    client.post("/book", json=VALID_BOOKING)
    response = client.post("/book", json=VALID_BOOKING)
    detail = response.json()["detail"]
    assert "contact_number" in detail
    assert detail["contact_number"]  # must be non-empty


def test_book_conflict_response_has_conflict_message(client):
    """409 response detail must include the expected conflict message."""
    client.post("/book", json=VALID_BOOKING)
    response = client.post("/book", json=VALID_BOOKING)
    detail = response.json()["detail"]
    assert detail["message"] == "This hall is already booked at this time"


# ---------------------------------------------------------------------------
# GET /schedule — shape (200)
# ---------------------------------------------------------------------------

def test_schedule_returns_200(client):
    """GET /schedule must return HTTP 200."""
    response = client.get("/schedule")
    assert response.status_code == 200


def test_schedule_has_schedule_key(client):
    """GET /schedule response must have a top-level 'schedule' key."""
    response = client.get("/schedule")
    assert "schedule" in response.json()


def test_schedule_has_7_days(client):
    """Schedule must contain exactly 7 days."""
    schedule = client.get("/schedule").json()["schedule"]
    assert len(schedule) == 7
    for day in DAYS:
        assert day in schedule


def test_schedule_has_5_slots_per_day(client):
    """Each day in the schedule must have exactly 5 time slots."""
    schedule = client.get("/schedule").json()["schedule"]
    for day in DAYS:
        assert len(schedule[day]) == 5
        for start_time, _ in TIME_SLOTS:
            assert start_time in schedule[day]


def test_schedule_has_6_halls_per_slot(client):
    """Each time slot must have exactly 6 hall entries."""
    schedule = client.get("/schedule").json()["schedule"]
    for day in DAYS:
        for start_time, _ in TIME_SLOTS:
            slot = schedule[day][start_time]
            assert len(slot) == 6
            for hall in HALLS:
                assert hall in slot


def test_schedule_total_210_cells(client):
    """Schedule must contain exactly 210 cells (7 days × 5 slots × 6 halls)."""
    schedule = client.get("/schedule").json()["schedule"]
    total = sum(
        len(schedule[day][slot])
        for day in schedule
        for slot in schedule[day]
    )
    assert total == 210


def test_schedule_empty_db_all_free(client):
    """With no bookings, every cell must have status 'Free'."""
    schedule = client.get("/schedule").json()["schedule"]
    for day in DAYS:
        for start_time, _ in TIME_SLOTS:
            for hall in HALLS:
                cell = schedule[day][start_time][hall]
                assert cell["status"] == "Free"
                assert cell["booked_by"] is None


def test_schedule_reflects_booking(client):
    """After a successful booking, GET /schedule must show that cell as Booked."""
    client.post("/book", json=VALID_BOOKING)
    schedule = client.get("/schedule").json()["schedule"]
    cell = schedule[VALID_BOOKING["day"]][VALID_BOOKING["start_time"]][VALID_BOOKING["hall"]]
    assert cell["status"] == "Booked"
    assert cell["booked_by"] == VALID_BOOKING["booked_by"]


# ---------------------------------------------------------------------------
# POST /book — validation errors (422)
# ---------------------------------------------------------------------------

def test_book_invalid_hall_returns_422(client):
    """A booking with an invalid hall name must return HTTP 422."""
    payload = {**VALID_BOOKING, "hall": "Hall Z"}
    response = client.post("/book", json=payload)
    assert response.status_code == 422


def test_book_invalid_day_returns_422(client):
    """A booking with an invalid day must return HTTP 422."""
    payload = {**VALID_BOOKING, "day": "Funday"}
    response = client.post("/book", json=payload)
    assert response.status_code == 422


def test_book_invalid_start_time_returns_422(client):
    """A booking with an invalid start_time must return HTTP 422."""
    payload = {**VALID_BOOKING, "start_time": "99:99"}
    response = client.post("/book", json=payload)
    assert response.status_code == 422


def test_book_empty_booked_by_returns_422(client):
    """A booking with an empty booked_by must return HTTP 422."""
    payload = {**VALID_BOOKING, "booked_by": ""}
    response = client.post("/book", json=payload)
    assert response.status_code == 422


def test_book_whitespace_booked_by_returns_422(client):
    """A booking with a whitespace-only booked_by must return HTTP 422."""
    payload = {**VALID_BOOKING, "booked_by": "   "}
    response = client.post("/book", json=payload)
    assert response.status_code == 422


def test_book_missing_field_returns_422(client):
    """A booking request missing a required field must return HTTP 422."""
    payload = {k: v for k, v in VALID_BOOKING.items() if k != "booked_by"}
    response = client.post("/book", json=payload)
    assert response.status_code == 422
