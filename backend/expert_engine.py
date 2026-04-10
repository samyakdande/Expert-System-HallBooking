import sqlite3
from backend.config import HALLS, TIME_SLOTS, CONTACT_NUMBER
from backend import scheduler


def check_conflict(conn: sqlite3.Connection, hall: str, day: str, start_time: str) -> bool:
    """Return True if a booking already exists for hall+day+start_time."""
    return scheduler.get_booking(conn, hall, day, start_time) is not None


def suggest_alternatives(conn: sqlite3.Connection, hall: str, day: str, start_time: str) -> dict:
    """Return alternative suggestions when a conflict is detected.

    Returns a dict with:
        free_halls       - halls (excluding `hall`) with no booking at day+start_time
        free_slots       - start_times for which `hall` has no booking on `day`
        recommended_hall - hall with fewest total bookings (ties: any)
        recommended_slot - start_time with fewest total bookings (highest availability)
        contact_number   - CONTACT_NUMBER from config
    """
    # Free halls: halls at same day+slot that are not booked, excluding requested hall
    booked_at_slot = {b["hall"] for b in scheduler.get_bookings_by_slot(conn, day, start_time)}
    free_halls = [h for h in HALLS if h != hall and h not in booked_at_slot]

    # Free slots: start_times on that day where the hall has no booking
    booked_for_hall = {b["start_time"] for b in scheduler.get_bookings_by_hall(conn, hall) if b["day"] == day}
    free_slots = [s for s, _ in TIME_SLOTS if s not in booked_for_hall]

    # Recommended hall: hall with fewest total bookings across all days/slots
    all_bookings = scheduler.get_all_bookings(conn)
    hall_counts = {h: 0 for h in HALLS}
    for b in all_bookings:
        if b["hall"] in hall_counts:
            hall_counts[b["hall"]] += 1
    recommended_hall = min(hall_counts, key=lambda h: hall_counts[h])

    # Recommended slot: start_time with fewest total bookings across all halls/days
    slot_counts = {s: 0 for s, _ in TIME_SLOTS}
    for b in all_bookings:
        if b["start_time"] in slot_counts:
            slot_counts[b["start_time"]] += 1
    recommended_slot = min(slot_counts, key=lambda s: slot_counts[s])

    return {
        "free_halls": free_halls,
        "free_slots": free_slots,
        "recommended_hall": recommended_hall,
        "recommended_slot": recommended_slot,
        "contact_number": CONTACT_NUMBER,
    }
