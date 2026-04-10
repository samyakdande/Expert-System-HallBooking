# 🏛️ Hall Booking Expert System

An AI-powered hall booking system with dynamic time scheduling, conflict detection, and automatic cleanup of expired bookings.

## ✨ Features

- **6 Halls Management** - Book Hall A through Hall F
- **Dynamic Time Selection** - Pick any start and end time (not limited to fixed slots)
- **Smart Conflict Detection** - Prevents overlapping bookings with time range validation
- **Alternative Suggestions** - Get recommendations for free halls and time slots when conflicts occur
- **Purpose Tracking** - Record the reason for each booking
- **Weekly Timetable View** - Visual grid showing all bookings across the week
- **Automatic Cleanup** - Expired bookings are automatically removed every 5 minutes
- **Real-time Updates** - Timetable refreshes after each booking

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd hall-booking-expert-system
```

2. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

3. Start the backend server:
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4. Open the frontend:
   - Simply open `frontend/index.html` in your web browser
   - Or serve it with any static file server

The API will be available at `http://localhost:8000`

## 📁 Project Structure

```
hall-booking-expert-system/
├── backend/
│   ├── __init__.py
│   ├── config.py           # Configuration (halls, days, contact)
│   ├── database.py         # Database initialization
│   ├── scheduler.py        # Data access layer
│   ├── expert_engine.py    # Conflict detection & suggestions
│   ├── models.py           # Pydantic models
│   ├── main.py             # FastAPI application
│   ├── cleanup.py          # Automatic booking cleanup
│   ├── migrate_db.py       # Database migration script
│   ├── requirements.txt    # Python dependencies
│   └── tests/              # Test suite
│       ├── __init__.py
│       ├── test_smoke.py   # Smoke tests
│       └── test_api.py     # API integration tests
├── frontend/
│   ├── index.html          # Main HTML page
│   ├── style.css           # Styling
│   └── app.js              # Frontend logic
└── .kiro/
    └── specs/              # Specification documents
```

## 🔧 API Endpoints

### POST /book
Create a new booking.

**Request Body:**
```json
{
  "hall": "Hall A",
  "day": "Monday",
  "start_time": "09:00",
  "end_time": "11:00",
  "booked_by": "John Doe",
  "purpose": "Team Meeting"
}
```

**Responses:**
- `201` - Booking confirmed
- `409` - Conflict (with alternative suggestions)
- `422` - Validation error

### GET /schedule
Get the full weekly schedule with all bookings.

**Response:**
```json
{
  "schedule": {
    "Monday": {
      "09:00": {
        "Hall A": {
          "status": "Booked",
          "booked_by": "John Doe",
          "end_time": "11:00",
          "purpose": "Team Meeting"
        }
      }
    }
  }
}
```

### POST /cleanup
Manually trigger cleanup of expired bookings.

**Response:**
```json
{
  "message": "Cleaned up 3 expired booking(s)",
  "count": 3
}
```

## 🧪 Testing

Run the test suite:
```bash
pytest backend/tests/ -v
```

All tests use in-memory SQLite databases to avoid affecting production data.

## 🎨 Frontend Features

- **Booking Form** - Select hall, day, start/end time, name, and purpose
- **Weekly Grid View** - See all bookings organized by day and hall
- **Color Coding**:
  - 🟢 Green = Available
  - 🔴 Red = Booked
- **Conflict Handling** - Shows alternative halls, free slots, and contact info
- **Responsive Design** - Works on desktop and mobile

## 🔄 Automatic Cleanup

The system automatically removes expired bookings:
- Runs every 5 minutes in the background
- Removes bookings where `end_time` has passed
- Cleans up bookings from previous days
- Runs on server startup

## 📞 Contact

For manual booking assistance, call: **+1-800-HALLBOOK**

## 🛠️ Configuration

Edit `backend/config.py` to customize:
- Hall names
- Days of the week
- Contact number

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Known Issues

None at the moment. Please report any bugs you find!

## 🔮 Future Enhancements

- User authentication
- Email notifications
- Recurring bookings
- Calendar export (iCal)
- Mobile app
- Admin dashboard
