import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
os.environ["DEBUG"] = "True"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/0"
os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/0"

import django

django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.events.models import Category, Event
from apps.tickets.models import TicketType


def _print(name, response):
    try:
        data = response.json()
    except Exception:
        data = response.content.decode("utf-8", errors="ignore")
    print(f"{name}: {response.status_code} -> {data}")


def run():
    User = get_user_model()

    organizer_email = "organizer@test.com"
    attendee_email = "attendee@test.com"

    User.objects.filter(email__in=[organizer_email, attendee_email]).delete()
    TicketType.objects.filter(event__title="Tech Meetup").delete()
    Event.objects.filter(title="Tech Meetup").delete()
    Category.objects.filter(slug="tech").delete()

    organizer = User.objects.create_user(
        email=organizer_email,
        full_name="Organizer User",
        password="Pass@12345",
        role=User.ORGANIZER,
    )
    attendee = User.objects.create_user(
        email=attendee_email,
        full_name="Attendee User",
        password="Pass@12345",
        role=User.ATTENDEE,
    )

    client = APIClient()

    # Login organizer
    resp = client.post(
        "/api/auth/login/",
        {"email": organizer_email, "password": "Pass@12345"},
        format="json",
    )
    _print("login_organizer", resp)
    organizer_token = resp.data.get("access")

    # Login attendee
    resp = client.post(
        "/api/auth/login/",
        {"email": attendee_email, "password": "Pass@12345"},
        format="json",
    )
    _print("login_attendee", resp)
    attendee_token = resp.data.get("access")

    # Create category (organizer)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {organizer_token}")
    resp = client.post(
        "/api/events/categories/",
        {"name": "Tech", "slug": "tech"},
        format="json",
    )
    _print("create_category", resp)
    category_id = resp.data.get("id")
    if not category_id:
        category_id = Category.objects.get(slug="tech").id

    # Create event (organizer)
    event_payload = {
        "title": "Tech Meetup",
        "description": "A test event",
        "venue": "Hall A",
        "city": "Mumbai",
        "address": "Test Address",
        "start_datetime": "2026-03-10T10:00:00+05:30",
        "end_datetime": "2026-03-10T12:00:00+05:30",
        "status": "published",
        "total_capacity": 100,
        "is_free": False,
        "category_id": category_id,
    }
    resp = client.post("/api/events/", event_payload, format="json")
    _print("create_event", resp)
    event_id = resp.data.get("id")

    # List events (anonymous)
    client.credentials()
    resp = client.get("/api/events/")
    _print("list_events", resp)

    # Create ticket type (organizer)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {organizer_token}")
    ticket_payload = {
        "name": "General",
        "ticket_type": "general",
        "description": "General entry",
        "price": "499.00",
        "total_quantity": 50,
        "sale_start": "2026-03-07T10:00:00+05:30",
        "sale_end": "2026-03-09T23:59:00+05:30",
        "is_active": True,
    }
    resp = client.post(f"/api/tickets/event/{event_id}/", ticket_payload, format="json")
    _print("create_ticket_type", resp)

    # Add review (attendee)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {attendee_token}")
    resp = client.post(
        f"/api/events/{event_id}/reviews/",
        {"rating": 5, "comment": "Great event!"},
        format="json",
    )
    _print("create_review", resp)

    # List reviews (anonymous)
    client.credentials()
    resp = client.get(f"/api/events/{event_id}/reviews/")
    _print("list_reviews", resp)

    # Profile (attendee)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {attendee_token}")
    resp = client.get("/api/auth/profile/")
    _print("get_profile", resp)


if __name__ == "__main__":
    run()
