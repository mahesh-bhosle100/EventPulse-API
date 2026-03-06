# Event Ticketing & Management System API

Beginner-friendly backend API built with Django REST Framework. It supports events, ticket types, bookings, Razorpay payments, QR check-in, and background tasks with Celery.

## Tech Stack
- Backend: Django 4.2 + DRF
- Database: MySQL 8.0
- Cache/Broker: Redis 7
- Background jobs: Celery + Celery Beat
- Payments: Razorpay
- File storage: Cloudinary
- Auth: JWT (SimpleJWT)
- PDF: ReportLab
- QR: qrcode
- Docs: drf-spectacular (Swagger)
- Docker: Docker + Docker Compose

## Quick Start (Docker)
1. Copy env file:
```bash
cp .env.example .env
```

2. Start containers:
```bash
docker-compose up --build
```

3. Run migrations and create admin:
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

4. Open the app:
- API: http://localhost:8001/api/
- Docs: http://localhost:8001/api/docs/
- Admin: http://localhost:8001/admin/

Note: This repo maps the API to port 8001 to avoid conflicts on port 8000.

## Run Locally (No Docker)
```bash
# Install dependencies
pip install -r requirements/dev.txt

# MySQL database
mysql -u root -p
CREATE DATABASE event_ticketing;
exit;

# Migrations
python manage.py migrate

# Redis (must be running)
redis-server

# Start Celery
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info

# Start Django
python manage.py runserver
```

## API Endpoints (Summary)
Auth
```
POST   /api/auth/register/
POST   /api/auth/login/
POST   /api/auth/token/refresh/
GET    /api/auth/profile/
POST   /api/auth/change-password/
```

Events
```
GET    /api/events/
POST   /api/events/
GET    /api/events/{id}/
PATCH  /api/events/{id}/
DELETE /api/events/{id}/
GET    /api/events/categories/
GET    /api/events/{id}/reviews/
POST   /api/events/{id}/reviews/
```

Tickets
```
GET    /api/tickets/event/{id}/
POST   /api/tickets/event/{id}/
GET    /api/tickets/{id}/
PATCH  /api/tickets/{id}/
```

Bookings
```
POST   /api/bookings/
POST   /api/bookings/verify-payment/
GET    /api/bookings/my/
GET    /api/bookings/{id}/
POST   /api/bookings/{id}/cancel/
```

Check-in / QR
```
GET    /api/checkin/booking/{id}/qr/
POST   /api/checkin/validate/
```

## Auth Flow (Simple)
1. Register: POST /api/auth/register/
2. Login: POST /api/auth/login/
3. Use token: Authorization: Bearer <access_token>

## Payment Flow (Simple)
1. POST /api/bookings/ -> returns razorpay_order_id
2. Complete Razorpay test payment on frontend
3. POST /api/bookings/verify-payment/ -> confirms booking
4. Celery sends PDF ticket email

## Project Structure (Short)
```
event_ticketing/
  apps/
    users/
    events/
    tickets/
    bookings/
    qrcodes/
    notifications/
  config/
    settings/
    urls.py
    celery.py
  docker/
  requirements/
```
