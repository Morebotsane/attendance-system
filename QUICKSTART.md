# Quick Start Guide

Get your Hospital Attendance System up and running in 10 minutes!

## 📋 Prerequisites Check

Before you start, make sure you have:
- [ ] Python 3.11 or higher (`python --version`)
- [ ] PostgreSQL 15 or higher
- [ ] Redis (optional for now)
- [ ] Git

## 🚀 Step-by-Step Setup

### 1. Clone or Navigate to Project
```bash
cd hospital-attendance-system
```

### 2. Set Up Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Generate a Fernet key for QR encryption
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Copy the output and add it to .env as QR_ENCRYPTION_KEY
```

Edit `.env` and update these key values:
```bash
SECRET_KEY="your-random-secret-key-min-32-characters"
QR_ENCRYPTION_KEY="your-fernet-key-from-above"
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/attendance_db"
```

### 3. Set Up Database

#### Option A: Using PostgreSQL directly
```bash
# Create database
createdb attendance_db

# Or using psql
psql -U postgres
CREATE DATABASE attendance_db;
\q
```

#### Option B: Using Docker
```bash
docker-compose up -d db redis
```

### 4. Install Backend Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Initialize Database

```bash
# Still in backend directory with venv activated

# Initialize Alembic (if not already done)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### 6. Run the Backend

```bash
# Make sure you're in backend directory with venv activated
uvicorn main:app --reload
```

You should see:
```
🚀 Starting Hospital Attendance System...
📍 Environment: development
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 7. Test the API

Open your browser to:
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

You should see the interactive API documentation!

## 🧪 Test the System

### Create a Test Department
```bash
curl -X POST "http://localhost:8000/api/v1/departments" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Emergency Department",
    "code": "EMERG",
    "location": "Building A, Floor 1",
    "latitude": -29.3167,
    "longitude": 27.4833,
    "geofence_radius": 100
  }'
```

### Create a Test Employee
```bash
curl -X POST "http://localhost:8000/api/v1/employees" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_number": "EMP001",
    "first_name": "Test",
    "last_name": "User",
    "email": "test@example.com",
    "position": "Nurse",
    "password": "secure_password123"
  }'
```

## 🎯 Next Steps

Now that your backend is running:

1. **Generate QR Code for Employee**
   - Use the `/api/v1/admin/generate-qr/{employee_id}` endpoint
   - Print or display the QR code

2. **Test Check-In**
   - Navigate to the check-in endpoint in API docs
   - Upload a test photo
   - Provide GPS coordinates
   - Scan the QR code

3. **View Attendance Records**
   - Check `/api/v1/attendance/today` endpoint
   - See real-time attendance

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check if PostgreSQL is running
pg_isctl status

# Or if using Docker
docker-compose ps
```

### Import Errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use
```bash
# Use a different port
uvicorn main:app --reload --port 8001
```

## 📚 Development Workflow

```bash
# Start database (if using Docker)
docker-compose up -d db redis

# Activate virtual environment
cd backend && source venv/bin/activate

# Run server with auto-reload
uvicorn main:app --reload

# In another terminal: Run tests
pytest

# Run with coverage
pytest --cov=app
```

## 🔑 Default Test Credentials

After running the initial seed script:
- Employee Number: `EMP001`
- Password: `test123` (change in production!)

## 📖 What's Next?

1. **Implement Authentication** - Add JWT auth to endpoints
2. **Build Frontend** - Create React components
3. **Add Reports** - Implement analytics
4. **Deploy** - Set up production environment

Check the main README.md for full documentation!

## 🆘 Need Help?

- Check API docs: http://localhost:8000/api/docs
- Review logs in terminal
- Check `/docs` folder for detailed guides
- Examine example code in service files

---

**You're all set! 🎉**

The backend is running and ready for development. Start building features!
