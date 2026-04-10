# Requirements Document

## Introduction

An AI-powered Hall Booking Expert System that manages reservations for 6 halls (Hall A through Hall F) across fixed weekly time slots. The system provides a full-stack web application with a FastAPI backend, SQLite storage, and a vanilla HTML/CSS/JavaScript frontend. It includes rule-based conflict detection, alternative suggestions, and a weekly timetable dashboard.

## Glossary

- **System**: The Hall Booking Expert System web application
- **Hall**: One of six bookable rooms: Hall A, Hall B, Hall C, Hall D, Hall E, Hall F
- **Time_Slot**: A fixed, non-overlapping period within a day (e.g., 08:30–10:30, 10:30–12:30, 12:30–14:30, 14:30–16:30, 16:30–18:30)
- **Booking**: A confirmed reservation associating a Hall, Day, Time_Slot, and a booker's name
- **Conflict**: A situation where a Hall is already booked for a given Day and Time_Slot
- **Scheduler**: The backend component responsible for storing and querying bookings
- **Expert_Engine**: The rule-based component that detects conflicts and generates suggestions
- **Timetable**: The weekly grid view showing all halls and time slots from Monday to Sunday
- **Contact_Number**: A static value displayed to users for manual booking resolution

## Requirements

### Requirement 1: Hall and Time Slot Management

**User Story:** As a system administrator, I want the system to manage a fixed set of halls and time slots, so that bookings are constrained to valid options only.

#### Acceptance Criteria

1. THE System SHALL support exactly six halls: Hall A, Hall B, Hall C, Hall D, Hall E, and Hall F.
2. THE System SHALL support exactly five fixed daily time slots: 08:30–10:30, 10:30–12:30, 12:30–14:30, 14:30–16:30, and 16:30–18:30.
3. THE System SHALL support bookings for each day of the week: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, and Sunday.
4. WHEN a booking request references a hall not in the defined list, THE System SHALL reject the request with a descriptive validation error.
5. WHEN a booking request references a time slot not in the defined list, THE System SHALL reject the request with a descriptive validation error.
6. WHEN a booking request references a day not in the defined list, THE System SHALL reject the request with a descriptive validation error.

---

### Requirement 2: Booking Creation

**User Story:** As a user, I want to book a hall for a specific day and time slot, so that I can reserve a space for my event.

#### Acceptance Criteria

1. WHEN a user submits a booking with a valid hall, day, time slot, and booker name, THE Scheduler SHALL persist the booking to the SQLite database.
2. WHEN a booking is successfully created, THE System SHALL return a confirmation response containing the booking details.
3. THE Scheduler SHALL store each booking with the fields: hall, day, start_time, end_time, and booked_by.
4. WHEN a user submits a booking with an empty or whitespace-only booker name, THE System SHALL reject the request with a validation error.

---

### Requirement 3: Conflict Detection

**User Story:** As a user, I want the system to prevent double-bookings, so that two events cannot occupy the same hall at the same time.

#### Acceptance Criteria

1. WHEN a booking request is received for a hall, day, and time slot that is already booked, THE Expert_Engine SHALL reject the booking and return the message "This hall is already booked at this time".
2. WHILE a hall is booked for a given day and time slot, THE Scheduler SHALL allow other halls to be booked for the same day and time slot.
3. THE Expert_Engine SHALL detect conflicts before any write operation is performed on the database.

---

### Requirement 4: Alternative Suggestions

**User Story:** As a user, I want the system to suggest alternatives when my preferred booking conflicts, so that I can quickly find another available option.

#### Acceptance Criteria

1. WHEN a conflict is detected, THE Expert_Engine SHALL return a list of all other halls that are free at the same day and time slot.
2. WHEN a conflict is detected, THE Expert_Engine SHALL return a list of all free time slots for the same hall on the same day.
3. WHEN a conflict is detected, THE Expert_Engine SHALL include the static Contact_Number in the response for manual resolution.
4. THE Expert_Engine SHALL recommend the least-used hall across all bookings as a preferred alternative.
5. THE Expert_Engine SHALL recommend the time slot with the highest availability across all halls and days as the best time slot.

---

### Requirement 5: Weekly Schedule Retrieval

**User Story:** As a user, I want to view the full weekly timetable, so that I can see which halls are free or booked at a glance.

#### Acceptance Criteria

1. WHEN a GET /schedule request is received, THE Scheduler SHALL return the booking status for every combination of hall, day, and time slot.
2. THE System SHALL represent each cell in the schedule as either "Free" or "Booked", along with the booker's name when booked.
3. WHEN no bookings exist, THE Scheduler SHALL return a schedule where all cells are marked "Free".

---

### Requirement 6: Timetable Dashboard UI

**User Story:** As a user, I want a visual weekly timetable dashboard, so that I can see availability at a glance without reading raw data.

#### Acceptance Criteria

1. THE System SHALL display a weekly timetable grid where rows represent time slots and columns represent days (Monday to Sunday).
2. WHEN a cell represents a free slot, THE System SHALL render it with a green background.
3. WHEN a cell represents a booked slot, THE System SHALL render it with a red background and display the hall name and booker's name.
4. THE System SHALL refresh the timetable display after every successful booking or page load.

---

### Requirement 7: Booking Form UI

**User Story:** As a user, I want a booking form with dropdowns, so that I can submit a booking without typing raw values.

#### Acceptance Criteria

1. THE System SHALL provide a booking form containing dropdown selectors for Hall, Day, and Time Slot, plus a text input for the booker's name and a Submit button.
2. WHEN a user submits the form with all fields filled, THE System SHALL send a POST /book request to the backend.
3. WHEN the booking succeeds, THE System SHALL display a success message and refresh the timetable.
4. WHEN the booking fails due to a conflict, THE System SHALL display the conflict message, the list of alternative halls, the list of alternative time slots, and the Contact_Number.
5. WHEN a user submits the form with any field empty, THE System SHALL prevent submission and display a validation message.

---

### Requirement 8: API Endpoints

**User Story:** As a developer, I want well-defined REST API endpoints, so that the frontend and any future clients can interact with the system reliably.

#### Acceptance Criteria

1. THE System SHALL expose a POST /book endpoint that accepts a JSON body with fields: hall, day, start_time, end_time, and booked_by.
2. THE System SHALL expose a GET /schedule endpoint that returns the full weekly schedule.
3. WHEN the POST /book endpoint receives an invalid or incomplete request body, THE System SHALL return an HTTP 422 response with a descriptive error message.
4. WHEN the POST /book endpoint detects a conflict, THE System SHALL return an HTTP 409 response with conflict details and suggestions.
5. WHEN the GET /schedule endpoint is called, THE System SHALL return an HTTP 200 response.

---

### Requirement 9: Data Persistence

**User Story:** As a user, I want my bookings to be saved persistently, so that they are not lost when the server restarts.

#### Acceptance Criteria

1. THE System SHALL use an SQLite database file to persist all bookings.
2. WHEN the application starts, THE System SHALL create the bookings table if it does not already exist.
3. WHEN a booking is deleted or the database is cleared, THE System SHALL reflect the updated state in subsequent GET /schedule responses.

---

### Requirement 10: Contact Information for Manual Resolution

**User Story:** As a user, I want to see a contact number when a conflict cannot be resolved automatically, so that I can reach a human administrator.

#### Acceptance Criteria

1. THE System SHALL store the administrator contact number as a static configuration value.
2. WHEN a conflict response is returned, THE System SHALL include the static Contact_Number in both the API response and the UI display.
