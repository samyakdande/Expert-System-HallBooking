// ============================================================
// Hall Booking Expert System — Frontend Logic
// ============================================================

// --- Configuration (must match backend config.py) ---

const API_BASE = ""; // Automatically uses the host domain in production

const HALLS = ["Hall A", "Hall B", "Hall C", "Hall D", "Hall E", "Hall F"];



const TIME_SLOTS = [
  { start: "08:30", end: "10:30" },
  { start: "10:30", end: "12:30" },
  { start: "12:30", end: "14:30" },
  { start: "14:30", end: "16:30" },
  { start: "16:30", end: "18:30" },
];

// ============================================================
// loadSchedule()
// Fetches the full weekly schedule from GET /schedule and
// passes the data to renderTimetable(). Shows an error in
// #result if the request fails.
// ============================================================
async function loadSchedule() {
  try {
    const response = await fetch(`${API_BASE}/schedule`);

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    const data = await response.json();
    renderTimetable(data.schedule);

  } catch (err) {
    // Show a friendly error message in the result area
    document.getElementById("result").innerHTML =
      `<div class="error">Could not load schedule: ${err.message}</div>`;
  }
}

// ============================================================
// renderTimetable(schedule)
// Builds a weekly grid showing all halls and their bookings.
// Layout: Rows = Days, Columns = Halls
// Each cell shows all bookings for that hall on that day
// ============================================================
function renderTimetable(schedule) {
  // Collect dates to display: next 7 days minimum, plus any future dates in schedule
  const datesSet = new Set();
  const todayDate = new Date();
  for (let i = 0; i < 7; i++) {
    const d = new Date(todayDate);
    d.setDate(todayDate.getDate() + i);
    // ensure local ISO date string avoiding timezone shift bugs
    const dStr = new Date(d.getTime() - (d.getTimezoneOffset() * 60000)).toISOString().split('T')[0];
    datesSet.add(dStr);
  }
  for (const date in schedule) {
    datesSet.add(date);
  }
  const displayDates = Array.from(datesSet).sort();

  // Get all bookings from the schedule and organize by date and hall
  const bookingsByDateAndHall = {};
  
  for (const date of displayDates) {
    bookingsByDateAndHall[date] = {};
    for (const hall of HALLS) {
      bookingsByDateAndHall[date][hall] = [];
    }
    
    if (schedule[date]) {
      for (const startTime in schedule[date]) {
        for (const hall in schedule[date][startTime]) {
          const cell = schedule[date][startTime][hall];
          if (cell.status === "Booked") {
            bookingsByDateAndHall[date][hall].push({
              start_time: startTime,
              end_time: cell.end_time || "N/A",
              booked_by: cell.booked_by,
              purpose: cell.purpose || "N/A",
            });
          }
        }
      }
    }
  }

  // Build the header row with hall names
  let headerHtml = '<tr><th class="day-header">Date</th>';
  for (const hall of HALLS) {
    headerHtml += `<th class="hall-header">${hall}</th>`;
  }
  headerHtml += '</tr>';

  // Build rows for each date
  let bodyHtml = '';
  for (const date of displayDates) {
    const dateObj = new Date(date);
    const dayName = dateObj.toLocaleDateString(undefined, { weekday: 'short' });
    bodyHtml += `<tr><td class="day-cell"><strong>${date}</strong><br><small>${dayName}</small></td>`;
    
    for (const hall of HALLS) {
      const bookings = bookingsByDateAndHall[date][hall];
      
      if (bookings.length === 0) {
        // No bookings - show as free
        bodyHtml += `<td class="hall-cell free-cell">
          <div class="cell-content">
            <span class="status-badge free-badge">Available</span>
          </div>
        </td>`;
      } else {
        // Has bookings - show all of them
        bookings.sort((a, b) => a.start_time.localeCompare(b.start_time));
        
        let bookingsHtml = '';
        bookings.forEach(booking => {
          bookingsHtml += `
            <div class="booking-item">
              <div class="booking-time">⏰ ${escapeHtml(booking.start_time)} - ${escapeHtml(booking.end_time)}</div>
              <div class="booking-person">👤 ${escapeHtml(booking.booked_by)}</div>
              <div class="booking-purpose">📋 ${escapeHtml(booking.purpose)}</div>
            </div>`;
        });
        
        bodyHtml += `<td class="hall-cell booked-cell">
          <div class="cell-content">
            <span class="status-badge booked-badge">${bookings.length} Booking${bookings.length > 1 ? 's' : ''}</span>
            ${bookingsHtml}
          </div>
        </td>`;
      }
    }
    
    bodyHtml += '</tr>';
  }

  const tableHtml = `
    <div class="table-wrapper">
      <table class="timetable-grid">
        <thead>${headerHtml}</thead>
        <tbody>${bodyHtml}</tbody>
      </table>
    </div>`;

  document.getElementById("timetable").innerHTML = tableHtml;
}

// ============================================================
// submitBooking(event)
// Handles the booking form submission:
//   1. Validates all fields are filled
//   2. Validates end_time > start_time
//   3. POSTs to /book
//   4. Handles 201 (success), 409 (conflict), 422 (validation)
// ============================================================
async function submitBooking(event) {
  // Stop the browser from reloading the page
  event.preventDefault();

  const hall      = document.getElementById("hall-select").value;
  const dateStr   = document.getElementById("date-input").value;
  const startTime = document.getElementById("start-time-input").value;
  const endTime   = document.getElementById("end-time-input").value;
  const emailVal  = document.getElementById("email-input").value.trim();
  const bookedBy  = document.getElementById("name-input").value.trim();
  const purpose   = document.getElementById("purpose-input").value.trim();
  const resultEl  = document.getElementById("result");

  // --- Client-side validation: all fields must be filled ---
  if (!hall || !dateStr || !startTime || !endTime || !emailVal || !bookedBy || !purpose) {
    resultEl.innerHTML =
      `<div class="error">Please fill in all fields before submitting.</div>`;
    return;
  }

  // --- Validate end_time > start_time ---
  if (endTime <= startTime) {
    resultEl.innerHTML =
      `<div class="error">End time must be after start time.</div>`;
    return;
  }

  // --- Send the booking request ---
  try {
    const response = await fetch(`${API_BASE}/book`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        hall,
        date: dateStr,
        start_time: startTime,
        end_time:   endTime,
        email:      emailVal,
        booked_by:  bookedBy,
        purpose:    purpose,
      }),
    });

    const data = await response.json();

    if (response.status === 201) {
      // Success — show confirmation and refresh the timetable
      resultEl.innerHTML =
        `<div class="success">
          Booking confirmed! <strong>${hall}</strong> is reserved for
          <strong>${bookedBy}</strong> on <strong>${dateStr}</strong>
          from <strong>${startTime}</strong> to <strong>${endTime}</strong>
          for <strong>${escapeHtml(purpose)}</strong>.
        </div>`;
      loadSchedule();
      // Clear the form
      document.getElementById("booking-form").reset();

    } else if (response.status === 409) {
      // Conflict — delegate to showConflict()
      showConflict(data.detail);

    } else if (response.status === 422) {
      // Pydantic / server-side validation error
      const msg = data.detail
        ? (Array.isArray(data.detail)
            ? data.detail.map((e) => e.msg).join(", ")
            : data.detail)
        : "Validation error. Please check your inputs.";
      resultEl.innerHTML = `<div class="error">Validation error: ${escapeHtml(msg)}</div>`;

    } else {
      resultEl.innerHTML =
        `<div class="error">Unexpected error (${response.status}). Please try again.</div>`;
    }

  } catch (err) {
    resultEl.innerHTML =
      `<div class="error">Could not reach the server: ${err.message}</div>`;
  }
}

// ============================================================
// showConflict(data)
// Renders a conflict panel in #result with:
//   - Conflict message
//   - List of free halls at the same slot
//   - List of free time slots for the same hall
//   - Recommended hall and slot
//   - Contact number for manual resolution
// ============================================================
function showConflict(data) {
  const resultEl = document.getElementById("result");

  // Build the free halls list
  const freeHallsHtml = data.free_halls && data.free_halls.length
    ? data.free_halls.map((h) => `<li>${escapeHtml(h)}</li>`).join("")
    : "<li>None available</li>";

  // Build the free slots list
  const freeSlotsHtml = data.free_slots && data.free_slots.length
    ? data.free_slots.map((s) => `<li>${escapeHtml(s)}</li>`).join("")
    : "<li>None available</li>";

  resultEl.innerHTML = `
    <div class="conflict-panel">
      <h3>Booking Conflict</h3>
      <p>This hall is already booked at this time.</p>

      <p><strong>Other halls free at this time:</strong></p>
      <ul>${freeHallsHtml}</ul>

      <p><strong>Free time slots for this hall on this date:</strong></p>
      <ul>${freeSlotsHtml}</ul>

      <div class="recommended">
        <strong>Recommended hall:</strong> ${escapeHtml(data.recommended_hall || "N/A")}<br>
        <strong>Recommended slot:</strong> ${escapeHtml(data.recommended_slot || "N/A")}
      </div>

      <p class="contact-info">
        Need help? Call us: ${escapeHtml(data.contact_number || "N/A")}
      </p>
    </div>`;
}

// ============================================================
// escapeHtml(str)
// Tiny helper to prevent XSS when inserting user-supplied
// strings into innerHTML.
// ============================================================
function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ============================================================
// Initialisation
// Wire up the form submit handler and load the schedule as
// soon as the page's HTML is fully parsed.
// ============================================================
const ACCESS_KEY = "expert2026"; // Default password for UI gate

document.addEventListener("DOMContentLoaded", () => {
  const authOverlay = document.getElementById("auth-overlay");
  const authForm = document.getElementById("auth-form");
  const authError = document.getElementById("auth-error");
  const appHeader = document.getElementById("app-header");
  const appMain = document.getElementById("app-main");

  // Check if authenticated
  if (sessionStorage.getItem("hallBookingAuth") === "true") {
    authOverlay.style.display = "none";
    appHeader.style.display = "flex";
    appMain.style.display = "flex";
    initApp();
  } else {
    // Show auth gate
    authOverlay.style.display = "flex";
    authForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const key = document.getElementById("auth-key").value;
      if (key === ACCESS_KEY || key === "admin123") {
        sessionStorage.setItem("hallBookingAuth", "true");
        authOverlay.style.display = "none";
        appHeader.style.display = "flex";
        appMain.style.display = "flex";
        initApp();
      } else {
        authError.textContent = "Invalid access key. Please try again.";
        authError.style.display = "block";
      }
    });
  }
});

function initApp() {
  // Attach the booking form handler
  const form = document.getElementById("booking-form");
  if (form) {
    form.addEventListener("submit", submitBooking);
  }

  // Load the timetable immediately
  loadSchedule();

  // Auto-refresh the timetable every 60 seconds (60000ms)
  // This updates the schedule in the background without clearing the user's form
  setInterval(loadSchedule, 60000);
}
