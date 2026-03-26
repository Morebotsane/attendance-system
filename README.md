# 🏥 Hospital Attendance System

A production-ready attendance tracking system with **QR codes**, **biometric photo verification**, **geofencing**, and **dual-channel notifications** (SMS + Email).

**Built for the Ministry of Health - Lesotho** 🇱🇸

[![Tests](https://github.com/Morebotsane/attendance-system/workflows/Run%20Tests/badge.svg)](https://github.com/Morebotsane/attendance-system/actions)
[![Coverage](https://img.shields.io/badge/coverage-60%25-yellow.svg)](https://github.com/Morebotsane/attendance-system)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)

---

## �� Key Features

### 🔐 Security & Authentication
- **Encrypted QR Codes** - Prevent sharing and replay attacks
- **Photo Verification** - Capture and validate identity at each check-in/out
- **Multi-role Authentication** (Admin, Manager, Employee)
- **JWT Token Security** - Secure API access with refresh tokens
- **Device Fingerprinting** - Detect suspicious patterns

### 📍 Location & Attendance
- **GPS Geofencing** - Verify staff are physically on-site
- **Real-time Validation** - Haversine distance calculations
- **Duplicate Prevention** - Block multiple check-ins per day
- **Attendance Flags** - Auto-flag geofence violations, late arrivals
- **Audit Logging** - Complete attendance history with validation metadata

### 📱 Notifications (NEW!)
- **Dual SMS Providers** - Africa's Talking (primary) + Twilio (backup)
- **Automatic Failover** - Never miss a notification
- **Email Notifications** - HTML + Plain text via SMTP
- **Background Processing** - Non-blocking via Celery + Redis
- **Rate Limiting** - Budget protection (1000 SMS/day limit)
- **Notification Templates** - Check-in, check-out, alerts

### 📊 Reports & Analytics
- **Daily Reports** - Attendance summaries by department
- **Monthly Analytics** - Trends, patterns, insights
- **Employee Reports** - Individual attendance history
- **Flags Dashboard** - Violations and anomalies
- **Real-time Stats** - Live attendance monitoring

### 🧪 Testing & CI/CD
- **75 Automated Tests** (65 integration + 10 unit)
- **60% Code Coverage**
- **GitHub Actions CI/CD** - Auto-run tests on every push
- **Pytest + AsyncIO** - Comprehensive test suite

---

## 🏗️ Architecture

### Tech Stack
- **Backend:** FastAPI 0.109, Python 3.11
- **Database:** PostgreSQL 15 + Asyncpg
- **Cache:** Redis 7
- **Task Queue:** Celery 5.3
- **Auth:** JWT (python-jose)
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **File Storage:** Local + S3-compatible

### Services
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│ PostgreSQL  │     │    Redis    │
│   (API)     │     │  (Database) │     │   (Cache)   │
└──────┬──────┘     └─────────────┘     └──────┬──────┘
       │                                         │
       │            ┌─────────────┐             │
       └───────────▶│   Celery    │◀────────────┘
                    │  (Workers)  │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
       ┌──────▼──────┐         ┌───────▼────────┐
       │ Africa's    │         │     Gmail      │
       │  Talking    │         │     SMTP       │
       │   (SMS)     │         │    (Email)     │
       └─────────────┘         └────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Morebotsane/attendance-system.git
cd attendance-system
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials:
# - Database connection
# - Redis URL
# - SMS provider keys (Africa's Talking, Twilio)
# - Email SMTP credentials
```

3. **Start with Docker**
```bash
docker-compose up -d
```

4. **Run database migrations**
```bash
docker-compose exec api alembic upgrade head
```

5. **Access the system**
- **API Docs:** http://localhost:8000/api/docs
- **Health Check:** http://localhost:8000/health

### Manual Setup (without Docker)
```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Start PostgreSQL and Redis
# ... (your local setup)

# Run migrations
alembic upgrade head

# Start API
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (separate terminal)
celery -A app.core.celery_app worker --loglevel=info --queues=notifications
```

---

## 📱 SMS & Email Configuration

### Africa's Talking (Primary SMS)
1. Sign up at [africastalking.com](https://africastalking.com)
2. Get your API Key and Username
3. Add to `.env`:
```bash
AFRICAS_TALKING_USERNAME=your_username
AFRICAS_TALKING_API_KEY=your_api_key
```

### Twilio (Backup SMS)
1. Sign up at [twilio.com](https://www.twilio.com/try-twilio)
2. Get Account SID, Auth Token, Phone Number
3. Add to `.env`:
```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
```

### Gmail SMTP (Email)
1. Enable 2FA on your Gmail account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Add to `.env`:
```bash
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
```

---

## 🧪 Testing

### Run All Tests
```bash
docker-compose exec api pytest tests/ -v
```

### Run Specific Test Suites
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Test Statistics
- **Total Tests:** 75
- **Unit Tests:** 10
- **Integration Tests:** 65
- **Coverage:** 60%

---

## 📖 API Documentation

### Authentication
```bash
# Login
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "password"
}

# Returns JWT token
```

### Check-in
```bash
POST /api/v1/attendance/check-in
Content-Type: multipart/form-data

- qr_code_data: "encrypted_qr_string"
- latitude: -29.3167
- longitude: 27.4833
- device_id: "device_fingerprint"
- photo: file.jpg
```

### Check-out
```bash
POST /api/v1/attendance/check-out
# Same parameters as check-in
```

See full API documentation at `/api/docs` (Swagger UI)

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `REDIS_URL` | Redis connection string | Yes | `redis://redis:6379/0` |
| `SECRET_KEY` | JWT secret key | Yes | - |
| `AFRICAS_TALKING_USERNAME` | Africa's Talking username | No | `sandbox` |
| `AFRICAS_TALKING_API_KEY` | Africa's Talking API key | No | - |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | No | - |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | No | - |
| `TWILIO_PHONE_NUMBER` | Twilio phone number | No | - |
| `SMTP_USER` | SMTP username | No | - |
| `SMTP_PASSWORD` | SMTP password | No | - |
| `FROM_EMAIL` | Email sender address | No | - |

---

## 📦 Project Structure
```
attendance-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/        # API routes
│   │   ├── core/                 # Config, security, celery
│   │   ├── db/                   # Database setup
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Business logic
│   │   │   ├── sms_service.py   # Dual SMS provider
│   │   │   ├── email_service.py # Email notifications
│   │   │   ├── qr_service.py    # QR generation/validation
│   │   │   ├── geofence_service.py  # GPS validation
│   │   │   └── photo_service.py # Photo management
│   │   ├── tasks/                # Celery background tasks
│   │   ├── templates/            # Notification templates
│   │   └── middleware/           # Rate limiting
│   ├── tests/
│   │   ├── unit/                 # Unit tests
│   │   └── integration/          # Integration tests
│   ├── main.py                   # FastAPI app
│   └── requirements.txt
├── .github/
│   └── workflows/
│       └── test.yml              # CI/CD pipeline
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 🚀 Deployment

### Docker Production
```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Environment-specific Settings
- **Development:** `.env` (local)
- **Staging:** `.env.staging`
- **Production:** Environment variables or secrets management

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest tests/ -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📄 License

This project is proprietary software developed for the Ministry of Health - Lesotho.

---

## 👨‍💻 Author

**Ntai Morebotsane**  
ICT Intern - Ministry of Health, Lesotho  
Master's in Computer Science (In Progress)

---

## 🙏 Acknowledgments

- Ministry of Health - Lesotho ICT Department
- Right to Care Lesotho
- FastAPI Community
- Africa's Talking & Twilio for SMS infrastructure

---

**Built with ❤️ for Ministry of Health - Lesotho** 🇱🇸
