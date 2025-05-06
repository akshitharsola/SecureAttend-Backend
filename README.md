# SecureAttend

SecureAttend is a secure multi-factor attendance system designed to prevent proxy attendance in educational institutions. The system uses a combination of QR code scanning, face recognition, and Bluetooth proximity detection to ensure that students are physically present in the classroom.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Backend Architecture](#backend-architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Server](#running-the-server)
- [API Endpoints](#api-endpoints)
- [Technology Stack](#technology-stack)
- [Contributing](#contributing)
- [License](#license)

## Overview

SecureAttend addresses the challenge of proxy attendance in educational institutions by implementing a multi-factor authentication system:

1. **QR Code Verification**: Faculty generates a unique QR code for each session
2. **Face Recognition**: Students verify their identity using on-device face authentication
3. **Bluetooth Proximity**: System confirms student's physical presence near the faculty device

The combination of these three factors ensures that attendance is marked only when the student is physically present in the classroom, preventing proxy attendance.

## Features

- **User Management**: Admin, faculty, and student roles with appropriate permissions
- **Course and Room Management**: Create and manage courses and rooms for attendance sessions
- **Session Management**: Faculty can create, start, and end attendance sessions
- **QR Code Generation**: Secure, encrypted QR codes for attendance verification
- **Multi-factor Authentication**: QR code, face recognition, and Bluetooth proximity
- **Attendance Tracking**: Comprehensive tracking of attendance with verification factors
- **Attendance History**: Students can view their attendance history
- **Session Analytics**: Faculty can view detailed attendance statistics for each session

## Backend Architecture

The backend is built using FastAPI, a modern, fast web framework for building APIs with Python. The architecture follows a modular approach with the following components:

```
secure_attend/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration versions
│   ├── env.py                  # Alembic environment
│   └── script.py.mako          # Migration template
├── app/
│   ├── api/
│   │   ├── endpoints/          # API route handlers
│   │   │   ├── admin.py        # Admin dashboard endpoints
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── attendance.py   # Attendance endpoints
│   │   │   ├── courses.py      # Course management endpoints
│   │   │   ├── rooms.py        # Room management endpoints
│   │   │   └── sessions.py     # Session management endpoints
│   │   └── deps.py             # API dependencies
│   ├── core/                   # Core functionality
│   │   ├── config.py           # Configuration settings
│   │   └── security.py         # Security utilities
│   ├── db/                     # Database management
│   │   ├── base.py             # Database models collection
│   │   ├── base_class.py       # Base model class
│   │   └── session.py          # Database session management
│   ├── models/                 # Database models
│   │   ├── user.py             # User model
│   │   ├── course.py           # Course model
│   │   ├── room.py             # Room model
│   │   ├── session.py          # Session model
│   │   └── attendance.py       # Attendance model
│   ├── schemas/                # Pydantic schemas
│   │   ├── course.py           # Course schemas
│   │   ├── room.py             # Room schemas
│   │   ├── session.py          # Session schemas
│   │   └── user.py             # User schemas
│   ├── services/               # Business logic
│   │   ├── course.py           # Course service
│   │   ├── room.py             # Room service
│   │   ├── session.py          # Session service
│   │   ├── attendance.py       # Attendance service
│   │   ├── qr_code.py          # QR code service
│   │   └── user.py             # User service
│   └── main.py                 # Application entry point
├── static/                     # Static files
│   └── qr_codes/               # Generated QR codes
├── templates/                  # HTML templates
│   └── admin/
│       └── dashboard.html      # Admin dashboard
├── run.py                      # Run script
└── requirements.txt            # Project dependencies
```

The backend implements a robust set of API endpoints for user authentication, session management, and attendance tracking, with comprehensive error handling and input validation.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Pip (Python package installer)
- Virtual environment tool (venv or conda)
- SQLite (for development) or PostgreSQL (for production)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/akshitharsola/secure_attend.git
   cd secure_attend
   ```

2. Create and activate a virtual environment:
   ```bash
   # Using venv
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with the following variables:
   ```
   DATABASE_URL=sqlite:///./secureattend.db
   SECRET_KEY=your-secret-key
   ADMIN_EMAIL=admin@secureattend.com
   ADMIN_PASSWORD=adminpassword
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

### Running the Server

To start the server, simply run:

```bash
python run.py
```

This will start the FastAPI server on `http://0.0.0.0:8000` by default. You can access the API documentation at `http://localhost:8000/docs`.

For development purposes, you can also run the server with auto-reload:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

The backend provides the following key API endpoints:

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/token` - Get admin token for dashboard

### User Management
- `GET /api/v1/admin/users` - Get all users
- `POST /api/v1/admin/users` - Create new user
- `PUT /api/v1/admin/users/{user_id}` - Update user
- `DELETE /api/v1/admin/users/{user_id}` - Delete user

### Course Management
- `GET /api/v1/courses/` - Get all courses
- `POST /api/v1/courses/` - Create new course
- `GET /api/v1/courses/{course_id}` - Get course details
- `PUT /api/v1/courses/{course_id}` - Update course
- `DELETE /api/v1/courses/{course_id}` - Delete course

### Room Management
- `GET /api/v1/rooms/` - Get all rooms
- `POST /api/v1/rooms/` - Create new room
- `GET /api/v1/rooms/{room_id}` - Get room details
- `PUT /api/v1/rooms/{room_id}` - Update room
- `DELETE /api/v1/rooms/{room_id}` - Delete room

### Session Management
- `POST /api/v1/sessions/create` - Create new session
- `GET /api/v1/sessions/{session_id}` - Get session details
- `POST /api/v1/sessions/{session_id}/start` - Start session
- `POST /api/v1/sessions/{session_id}/end` - End session
- `GET /api/v1/sessions/{session_id}/qr` - Get session QR code

### Attendance
- `POST /api/v1/attendance/mark` - Mark attendance
- `POST /api/v1/attendance/mark-with-qr` - Mark attendance with QR
- `POST /api/v1/attendance/mark-with-factors` - Mark with verification factors
- `GET /api/v1/attendance/history` - Get student attendance history
- `GET /api/v1/attendance/faculty/sessions` - Get faculty session history
- `GET /api/v1/attendance/session/{session_id}/full` - Get session attendances

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: JWT tokens
- **QR Code**: qrcode, cryptography libraries
- **Frontend**: Android (Kotlin) mobile application with:
  - Face recognition using ML Kit
  - QR code scanning using ZXing
  - Bluetooth proximity using BLE

## Contributing

Contributions to SecureAttend are welcome! Please feel free to submit pull requests or open issues to improve the project.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
