from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio

from backend.config import DAYS, TIME_SLOTS, HALLS
from backend.database import get_connection, init_db
from backend.expert_engine import check_conflict, suggest_alternatives
from backend.models import BookingRequest, BookingResponse, ConflictResponse
from backend.scheduler import create_booking, get_all_bookings
from backend.cleanup import cleanup_expired_bookings


# Background task for periodic cleanup
async def periodic_cleanup():
    """Run cleanup every 5 minutes."""
    while True:
        try:
            count = cleanup_expired_bookings()
            if count > 0:
                print(f"🧹 Cleaned up {count} expired booking(s)")
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
        await asyncio.sleep(300)  # 5 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    # Startup
    init_db()
    cleanup_expired_bookings()  # Clean up on startup
    print("✓ Database initialized and cleaned")
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Hall Booking Expert System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/book", status_code=201, response_model=BookingResponse)
def book_hall(request: BookingRequest):
    conn = get_connection()
    try:
        # Check for time overlap conflicts (not just exact start_time match)
        if has_time_overlap(conn, request.hall, request.day, request.start_time, request.end_time):
            suggestions = suggest_alternatives(conn, request.hall, request.day, request.start_time)
            raise HTTPException(
                status_code=409,
                detail=ConflictResponse(
                    message="This hall is already booked during this time period",
                    **suggestions,
                ).model_dump(),
            )
        booking_id = create_booking(
            conn,
            request.hall,
            request.day,
            request.start_time,
            request.end_time,
            request.booked_by,
            request.purpose,
        )
        return BookingResponse(
            message="Booking confirmed",
            booking={
                "id": booking_id,
                "hall": request.hall,
                "day": request.day,
                "start_time": request.start_time,
                "end_time": request.end_time,
                "booked_by": request.booked_by,
                "purpose": request.purpose,
            },
        )
    finally:
        conn.close()


def has_time_overlap(conn, hall: str, day: str, start_time: str, end_time: str) -> bool:
    """Check if the requested time range overlaps with any existing booking for this hall on this day."""
    existing = conn.execute(
        """
        SELECT start_time, end_time FROM bookings
        WHERE hall = ? AND day = ?
        """,
        (hall, day),
    ).fetchall()
    
    for booking in existing:
        existing_start = booking["start_time"]
        existing_end = booking["end_time"]
        
        # Check if time ranges overlap
        # Overlap occurs if: new_start < existing_end AND new_end > existing_start
        if start_time < existing_end and end_time > existing_start:
            return True
    
    return False


@app.get("/schedule", status_code=200)
def get_schedule():
    conn = get_connection()
    try:
        all_bookings = get_all_bookings(conn)
    finally:
        conn.close()

    # Build schedule with ALL bookings (not just fixed time slots)
    # Group by day and start_time dynamically
    schedule = {}
    for day in DAYS:
        schedule[day] = {}
    
    # Add all actual bookings to the schedule
    for booking in all_bookings:
        day = booking["day"]
        start_time = booking["start_time"]
        hall = booking["hall"]
        
        # Create the time slot if it doesn't exist
        if start_time not in schedule[day]:
            schedule[day][start_time] = {}
        
        # Add this booking
        schedule[day][start_time][hall] = {
            "status": "Booked",
            "booked_by": booking["booked_by"],
            "end_time": booking["end_time"],
            "purpose": booking["purpose"],
        }

    return {"schedule": schedule}


@app.post("/cleanup", status_code=200)
def manual_cleanup():
    """Manually trigger cleanup of expired bookings."""
    count = cleanup_expired_bookings()
    return {
        "message": f"Cleaned up {count} expired booking(s)",
        "count": count
    }
