# Implementation Plan: Hall Booking Expert System

## Overview

Incremental implementation starting with the backend core (config → DB → scheduler → expert engine → API), then the frontend, then tests. Each step wires into the previous so there is no orphaned code.

## Tasks

- [x] 1. Set up project structure and configuration
  - Create `backend/` and `frontend/` directories
  - Create `backend/config.py` with HALLS (6 halls), DAYS (7 days), TIME_SLOTS (5 slots), and CONTACT_NUMBER
  - Create `backend/requirements.txt` with fastapi, uvicorn, pydantic, hypothesis, pytest, httpx
  - _Requirements: 1.1, 1.2, 1.3, 10.1_

- [x] 2. Implement database layer
  - [x] 2.1 Create `backend/database.py` with `get_connection()` and `init_db()`
    - Use SQLite with the bookings table schema (id, hall, day, start_time, end_time, booked_by)
    - Call `init_db()` on app startup
    - _Requirements: 9.1, 9.2_

  - [ ]* 2.2 Write unit test for database initialization
    - Verify table is created on first call and is idempotent on repeated calls
    - _Requirements: 9.2_

- [x] 3. Implement scheduler (data access layer)
  - [x] 3.1 Create `backend/scheduler.py` with `create_booking()`, `get_booking()`, `get_all_bookings()`, `get_bookings_by_hall()`, `get_bookings_by_slot()`
    - All functions accept a `conn` parameter for testability with in-memory DB
    - _Requirements: 2.1, 2.3, 5.1_

  - [ ]* 3.2 Write property test for booking round-trip
    - **Property 7: Booking round-trip**
    - For any valid (hall, day, start_time, end_time, booked_by), after `create_booking`, `get_booking` must return the same values
    - Use in-memory SQLite (`:memory:`)
    - **Validates: Requirements 2.1, 2.2, 2.3, 5.2**
    - Tag: `Feature: hall-booking-expert-system, Property 7`

- [x] 4. Implement Expert Engine
  - [x] 4.1 Create `backend/expert_engine.py` with `check_conflict()` and `suggest_alternatives()`
    - `check_conflict(conn, hall, day, start_time)` → bool
    - `suggest_alternatives(conn, hall, day, start_time)` → dict with free_halls, free_slots, recommended_hall, recommended_slot, contact_number
    - Least-used hall: count bookings per hall, pick minimum
    - Best slot: count bookings per slot across all halls/days, pick minimum
    - _Requirements: 3.1, 3.3, 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 4.2 Write property test for no double-booking invariant
    - **Property 1: No double-booking invariant**
    - For any valid booking, after creation, `check_conflict` must return True for the same hall/day/slot
    - **Validates: Requirements 3.1, 3.3**
    - Tag: `Feature: hall-booking-expert-system, Property 1`

  - [ ]* 4.3 Write property test for cross-hall independence
    - **Property 2: Cross-hall independence**
    - For any two distinct halls H1 and H2, booking H1 at (day, slot) must not cause `check_conflict` to return True for H2 at the same (day, slot)
    - **Validates: Requirements 3.2**
    - Tag: `Feature: hall-booking-expert-system, Property 2`

  - [ ]* 4.4 Write property test for conflict suggestions completeness (free halls)
    - **Property 3: Conflict suggestions completeness**
    - For any conflict scenario, `free_halls` must contain exactly the halls with no booking at that day/slot, excluding the requested hall; contact_number must equal CONTACT_NUMBER
    - **Validates: Requirements 4.1, 4.3, 10.2**
    - Tag: `Feature: hall-booking-expert-system, Property 3`

  - [ ]* 4.5 Write property test for free slots completeness
    - **Property 4: Free slots completeness**
    - For any conflict scenario, `free_slots` must contain exactly the slots on that day where the hall has no booking
    - **Validates: Requirements 4.2**
    - Tag: `Feature: hall-booking-expert-system, Property 4`

  - [ ]* 4.6 Write property test for least-used hall recommendation
    - **Property 5: Least-used hall and best slot recommendation**
    - For any set of bookings, `recommended_hall` must be the hall with the fewest total bookings; `recommended_slot` must be the slot with the most free cells
    - **Validates: Requirements 4.4, 4.5**
    - Tag: `Feature: hall-booking-expert-system, Property 5`

- [x] 5. Checkpoint — Ensure all backend logic tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement Pydantic models and FastAPI routes
  - [x] 6.1 Create `backend/models.py` with `BookingRequest`, `BookingResponse`, `ConflictResponse`
    - Add validator on `booked_by` to reject empty/whitespace-only strings
    - Add validators on hall, day, start_time to check against config lists
    - _Requirements: 1.4, 1.5, 1.6, 2.4, 8.1, 8.3_

  - [x] 6.2 Create `backend/main.py` with FastAPI app, `POST /book`, and `GET /schedule`
    - `POST /book`: validate → check_conflict → if conflict return 409 ConflictResponse → else create_booking return 201
    - `GET /schedule`: get_all_bookings → build full 7×5×6 grid → return 200
    - Mount CORS middleware to allow frontend requests
    - Call `init_db()` in startup event
    - _Requirements: 2.1, 2.2, 3.1, 4.1–4.5, 5.1, 5.2, 5.3, 8.1, 8.2, 8.4, 8.5_

  - [ ]* 6.3 Write property test for schedule completeness
    - **Property 6: Schedule completeness**
    - For any DB state, GET /schedule must return exactly 210 cells (7 days × 5 slots × 6 halls)
    - Use TestClient with in-memory DB
    - **Validates: Requirements 5.1, 5.3**
    - Tag: `Feature: hall-booking-expert-system, Property 6`

  - [ ]* 6.4 Write property test for input validation rejects invalid enums
    - **Property 8: Input validation rejects invalid enums and whitespace names**
    - For any string not in HALLS/DAYS/TIME_SLOTS, POST /book must return 422 and DB must remain unchanged
    - For any whitespace-only booked_by, POST /book must return 422
    - **Validates: Requirements 1.4, 1.5, 1.6, 2.4, 8.3**
    - Tag: `Feature: hall-booking-expert-system, Property 8`

  - [ ]* 6.5 Write unit tests for API endpoints
    - Test 201 on valid booking
    - Test 409 on conflict with suggestions in response body
    - Test 200 on GET /schedule with correct shape
    - Test contact number present in 409 response
    - _Requirements: 8.1, 8.2, 8.4, 8.5, 10.2_

- [x] 7. Checkpoint — Ensure all API tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement frontend
  - [x] 8.1 Create `frontend/index.html` with booking form (Hall, Day, Time Slot dropdowns + booked_by input + Submit) and timetable grid container
    - Populate dropdowns from hardcoded config matching backend values
    - _Requirements: 6.1, 7.1_

  - [x] 8.2 Create `frontend/style.css` with green cells for free slots, red cells for booked slots, and responsive table layout
    - _Requirements: 6.2, 6.3_

  - [x] 8.3 Create `frontend/app.js` with `loadSchedule()`, `renderTimetable()`, `submitBooking()`, and `showConflict()`
    - `loadSchedule()`: fetch GET /schedule → call `renderTimetable()`
    - `renderTimetable(data)`: build HTML table rows=time slots, cols=days, each cell shows hall status per hall
    - `submitBooking(event)`: fetch POST /book → on 201 show success + reload schedule → on 409 call `showConflict()`
    - `showConflict(data)`: display conflict message, free_halls list, free_slots list, recommended_hall, recommended_slot, contact_number
    - Validate all form fields non-empty before submit
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 9. Final checkpoint — Ensure all tests pass and app is wired end-to-end
  - Ensure all tests pass, ask the user if questions arise.
  - Verify frontend fetches from correct backend URL (http://localhost:8000)
  - Verify timetable renders on page load

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- All property tests use Hypothesis with minimum 100 iterations and in-memory SQLite
- Run backend tests with: `pytest backend/tests/ -v`
- Start backend with: `uvicorn backend.main:app --reload`
- Open `frontend/index.html` directly in a browser (or serve with any static file server)
