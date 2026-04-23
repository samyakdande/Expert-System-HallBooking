from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import logging
import os

# Configure application logging
log_file_path = os.path.join(os.path.dirname(__file__), "bookings.log")
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
from backend.config import TIME_SLOTS, HALLS
from backend.database import get_connection, init_db
from backend.expert_engine import check_conflict, suggest_alternatives
from backend.models import BookingRequest, BookingResponse, ConflictResponse, CancelRequest
from backend.scheduler import create_booking, get_all_bookings
from backend.email_service import send_confirmation_email
from backend.cleanup import cleanup_expired_bookings


# Background task for periodic cleanup
async def periodic_cleanup():
    """Run cleanup every 5 minutes."""
    while True:
        try:
            count = cleanup_expired_bookings()
            if count > 0:
                logger.info(f"Cleaned up {count} expired booking(s)")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        await asyncio.sleep(300)  # 5 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    # Startup
    init_db()
    cleanup_expired_bookings()  # Clean up on startup
    logger.info("Database initialized and system starting up")
    
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
def book_hall(request: BookingRequest, background_tasks: BackgroundTasks):
    conn = get_connection()
    try:
        # Check for time overlap conflicts (not just exact start_time match)
        if has_time_overlap(conn, request.hall, request.date, request.start_time, request.end_time):
            suggestions = suggest_alternatives(conn, request.hall, request.date, request.start_time)
            logger.warning(f"Booking conflict detected for {request.hall} on {request.date} ({request.start_time}-{request.end_time}) by {request.booked_by}")
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
            request.date,
            request.start_time,
            request.end_time,
            request.email,
            request.booked_by,
            request.purpose,
        )
        booking_data = {
            "id": booking_id,
            "hall": request.hall,
            "date": request.date,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "email": request.email,
            "booked_by": request.booked_by,
            "purpose": request.purpose,
        }
        
        background_tasks.add_task(send_confirmation_email, request.email, booking_data)
        
        logger.info(f"New booking confirmed: ID {booking_id} for {request.hall} on {request.date} ({request.start_time}-{request.end_time}) by {request.booked_by} (Purpose: {request.purpose})")

        return BookingResponse(
            message="Booking confirmed",
            booking=booking_data,
        )
    finally:
        conn.close()


def has_time_overlap(conn, hall: str, date: str, start_time: str, end_time: str) -> bool:
    """Check if the requested time range overlaps with any existing booking for this hall on this date."""
    existing = conn.execute(
        """
        SELECT start_time, end_time FROM bookings
        WHERE hall = ? AND date = ?
        """,
        (hall, date),
    ).fetchall()
    
    for booking in existing:
        existing_start = booking["start_time"]
        existing_end = booking["end_time"]
        
        # Check if time ranges overlap
        # Overlap occurs if: new_start < existing_end AND new_end > existing_start
        if start_time < existing_end and end_time > existing_start:
            return True
    
    return False


@app.post("/cancel", status_code=200)
def cancel_booking(request: CancelRequest):
    conn = get_connection()
    try:
        # Check if booking exists
        booking = conn.execute(
            """
            SELECT id, booked_by, purpose FROM bookings
            WHERE hall = ? AND date = ? AND start_time = ?
            """,
            (request.hall, request.date, request.start_time)
        ).fetchone()

        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Booking not found or already cancelled."
            )

        # Delete the booking
        conn.execute(
            """
            DELETE FROM bookings
            WHERE hall = ? AND date = ? AND start_time = ?
            """,
            (request.hall, request.date, request.start_time)
        )
        conn.commit()

        # Log cancellation
        logger.info(f"Booking cancelled: ID {booking['id']} for {request.hall} on {request.date} at {request.start_time} by {booking['booked_by']}. Reason: {request.reason}")

        return {"message": "Booking cancelled successfully"}
    finally:
        conn.close()


@app.get("/schedule", status_code=200)
def get_schedule():
    conn = get_connection()
    try:
        all_bookings = get_all_bookings(conn)
    finally:
        conn.close()

    # Build schedule with ALL bookings (not just fixed time slots)
    # Group by date and start_time dynamically
    schedule = {}
    
    # Add all actual bookings to the schedule
    for booking in all_bookings:
        date = booking["date"]
        start_time = booking["start_time"]
        hall = booking["hall"]
        
        # Create the date and time slot if it doesn't exist
        if date not in schedule:
            schedule[date] = {}
        if start_time not in schedule[date]:
            schedule[date][start_time] = {}
        
        # Add this booking
        schedule[date][start_time][hall] = {
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
    if count > 0:
        logger.info(f"Manual cleanup triggered: {count} expired booking(s) removed")
    return {
        "message": f"Cleaned up {count} expired booking(s)",
        "count": count
    }


# Serve the frontend statically at the root level for deployment
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    logger.warning(f"Frontend directory not found at {frontend_dir}. Running API only mode.")
