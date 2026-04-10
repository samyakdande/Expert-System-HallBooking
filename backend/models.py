from pydantic import BaseModel, field_validator
from backend.config import HALLS, DAYS
import re


class BookingRequest(BaseModel):
    hall: str
    day: str
    start_time: str
    end_time: str
    booked_by: str
    purpose: str

    @field_validator("hall", mode="before")
    @classmethod
    def validate_hall(cls, v: str) -> str:
        if v not in HALLS:
            raise ValueError(f"Invalid hall '{v}'. Must be one of: {', '.join(HALLS)}")
        return v

    @field_validator("day", mode="before")
    @classmethod
    def validate_day(cls, v: str) -> str:
        if v not in DAYS:
            raise ValueError(f"Invalid day '{v}'. Must be one of: {', '.join(DAYS)}")
        return v

    @field_validator("start_time", mode="before")
    @classmethod
    def validate_start_time(cls, v: str) -> str:
        # Validate HH:MM format (24-hour)
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(f"Invalid start_time '{v}'. Must be in HH:MM format (e.g., 09:00, 14:30)")
        return v

    @field_validator("end_time", mode="before")
    @classmethod
    def validate_end_time(cls, v: str) -> str:
        # Validate HH:MM format (24-hour)
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(f"Invalid end_time '{v}'. Must be in HH:MM format (e.g., 09:00, 14:30)")
        return v

    @field_validator("booked_by", mode="before")
    @classmethod
    def validate_booked_by(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("booked_by must not be empty or whitespace-only")
        return v.strip()

    @field_validator("purpose", mode="before")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("purpose must not be empty or whitespace-only")
        return v.strip()


class BookingResponse(BaseModel):
    message: str
    booking: dict


class ConflictResponse(BaseModel):
    message: str
    free_halls: list[str]
    free_slots: list[str]
    recommended_hall: str
    recommended_slot: str
    contact_number: str
