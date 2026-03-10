# Project Structure

## Overview

```
hospital-attendance-system/
│
├── 📄 README.md                    # Main documentation
├── 📄 QUICKSTART.md                # Quick start guide
├── 📄 .env.example                 # Environment variables template
├── 📄 .gitignore                   # Git ignore rules
├── 📄 docker-compose.yml           # Docker orchestration
├── 📄 Makefile                     # Convenience commands
│
├── 📁 backend/                     # FastAPI Backend
│   ├── 📄 main.py                  # Application entry point
│   ├── 📄 requirements.txt         # Python dependencies
│   ├── 📄 Dockerfile               # Backend Docker config
│   │
│   ├── 📁 app/                     # Main application code
│   │   ├── 📁 api/                 # API layer
│   │   │   ├── 📁 endpoints/       # API route handlers
│   │   │   │   ├── attendance.py   # ✅ Check-in/out endpoints
│   │   │   │   ├── auth.py         # 🔐 Authentication
│   │   │   │   ├── employees.py    # 👥 Employee management
│   │   │   │   ├── departments.py  # 🏢 Department management
│   │   │   │   ├── reports.py      # 📊 Analytics & reports
│   │   │   │   └── admin.py        # ⚙️ Admin functions
│   │   │   └── 📁 dependencies/    # Shared dependencies
│   │   │
│   │   ├── 📁 core/                # Core configuration
│   │   │   └── config.py           # ⚙️ Settings & config
│   │   │
│   │   ├── 📁 db/                  # Database layer
│   │   │   ├── base.py             # Base model class
│   │   │   └── session.py          # DB session management
│   │   │
│   │   ├── 📁 models/              # Database models
│   │   │   └── models.py           # 📋 SQLAlchemy models
│   │   │
│   │   ├── 📁 schemas/             # Request/Response schemas
│   │   │   └── schemas.py          # 📝 Pydantic schemas
│   │   │
│   │   ├── 📁 services/            # Business logic
│   │   │   ├── qr_service.py       # 📱 QR code generation
│   │   │   ├── geofence_service.py # 📍 Location validation
│   │   │   └── photo_service.py    # 📸 Photo handling
│   │   │
│   │   ├── 📁 storage/             # File storage
│   │   │   ├── photos/             # 📸 Check-in/out photos
│   │   │   ├── qr_codes/           # 📱 Generated QR codes
│   │   │   └── temp/               # Temporary files
│   │   │
│   │   └── 📁 utils/               # Utility functions
│   │
│   ├── 📁 alembic/                 # Database migrations
│   │   └── versions/               # Migration files
│   │
│   └── 📁 tests/                   # Test suite
│       ├── unit/                   # Unit tests
│       └── integration/            # Integration tests
│
├── 📁 frontend/                    # React Frontend (TODO)
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/             # Shared components
│   │   │   ├── attendance/         # Attendance features
│   │   │   ├── admin/              # Admin dashboard
│   │   │   └── reports/            # Report components
│   │   ├── pages/                  # Page components
│   │   ├── services/               # API integration
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── contexts/               # React contexts
│   │   └── utils/                  # Utility functions
│   └── package.json
│
├── 📁 docs/                        # Documentation
│   ├── api/                        # API documentation
│   ├── user_guide/                 # User manual
│   └── deployment/                 # Deployment guides
│
└── 📁 deployment/                  # Deployment configs
    ├── docker/                     # Docker files
    └── nginx/                      # Nginx configs
```

## Key Files Explained

### Backend Core Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application entry point, routes registration |
| `app/core/config.py` | All configuration and environment variables |
| `app/db/session.py` | Database connection and session management |
| `app/models/models.py` | SQLAlchemy database models (tables) |
| `app/schemas/schemas.py` | Pydantic schemas for validation |

### Service Layer

| File | Purpose |
|------|---------|
| `qr_service.py` | Generate & validate encrypted QR codes |
| `geofence_service.py` | Validate GPS coordinates against geofences |
| `photo_service.py` | Handle photo upload, resize, storage |

### API Endpoints

| Endpoint File | Routes |
|---------------|--------|
| `attendance.py` | `/check-in`, `/check-out`, `/today` |
| `auth.py` | `/login`, `/logout`, `/refresh` |
| `employees.py` | `/employees`, `/employees/{id}` |
| `departments.py` | `/departments`, `/departments/{id}` |
| `reports.py` | `/daily`, `/monthly`, `/employee/{id}` |
| `admin.py` | `/generate-qr`, `/flags`, `/audit-log` |

## Database Models

### Main Tables

1. **employees**
   - Employee information
   - QR code data (encrypted)
   - Reference photo URL
   - Department assignment

2. **departments**
   - Department info
   - Geofence coordinates (lat, lon)
   - Geofence radius

3. **attendance_records**
   - Check-in/out timestamps
   - GPS coordinates
   - Photo URLs
   - Device fingerprints
   - Validation metadata

4. **attendance_audit_log**
   - Complete audit trail
   - All check-in/out actions
   - Manual edits

5. **attendance_flags**
   - Anomalies and violations
   - Geofence violations
   - Photo mismatches
   - Suspicious patterns

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (not in git) |
| `.env.example` | Template for .env file |
| `docker-compose.yml` | Local development setup |
| `requirements.txt` | Python dependencies |
| `Makefile` | Convenience commands |

## What's Implemented ✅

- [x] Project structure
- [x] Database models
- [x] QR code generation & validation
- [x] Geofencing service
- [x] Photo upload & storage
- [x] Check-in endpoint (complete)
- [x] Check-out endpoint (complete)
- [x] Configuration management
- [x] Docker setup

## What's TODO 📋

- [ ] Authentication (JWT)
- [ ] Employee endpoints
- [ ] Department endpoints
- [ ] Report generation
- [ ] Admin dashboard endpoints
- [ ] Frontend (React)
- [ ] Tests
- [ ] Deployment configs

## Data Flow

```
1. Employee scans QR code
   ↓
2. Frontend captures photo + GPS
   ↓
3. POST /api/v1/attendance/check-in
   ↓
4. Validate QR (decrypt)
   ↓
5. Validate location (geofence)
   ↓
6. Store photo
   ↓
7. Create attendance record
   ↓
8. Log in audit trail
   ↓
9. Return success response
```

## Security Layers

1. **QR Code** - Encrypted with Fernet + timestamp
2. **Geofence** - GPS validation within radius
3. **Photo** - Required identity verification
4. **Device ID** - Fingerprint tracking
5. **Audit Log** - Complete trail of all actions

---

This structure is designed for:
- ✅ **Scalability** - Easy to add new features
- ✅ **Maintainability** - Clear separation of concerns
- ✅ **Security** - Multiple validation layers
- ✅ **Testing** - Isolated components
- ✅ **Deployment** - Docker-ready
