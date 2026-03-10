# Hospital Attendance System

A modern, secure attendance tracking system using **QR codes**, **photo capture**, and **geofencing** to eliminate bottlenecks and prevent fraud.

Built for the Ministry of Health - Lesotho

## 🎯 Features

- ✅ **QR Code Check-in/Check-out** - Fast, contactless attendance tracking
- 📸 **Photo Capture** - Verify identity at each check-in/out
- 📍 **Geofencing** - GPS validation ensures staff are on-site
- 🔒 **Encrypted QR Codes** - Prevent sharing and replay attacks
- 📱 **Device Fingerprinting** - Detect suspicious patterns
- 🚨 **Anomaly Detection** - Flag unusual attendance patterns
- 📊 **Real-time Dashboards** - Live attendance monitoring
- 📈 **Comprehensive Reports** - Daily, weekly, monthly analytics

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)

### Getting Started

1. Clone and configure:
```bash
cp .env.example .env
# Edit .env with your configuration
```

2. Start with Docker:
```bash
docker-compose up -d
```

3. Access:
- API: http://localhost:8000
- Docs: http://localhost:8000/api/docs

See full documentation in `/docs` directory.

---
**Built with ❤️ for Ministry of Health - Lesotho**
