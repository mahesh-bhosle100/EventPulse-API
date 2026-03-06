import io
import qrcode
import logging
from celery import shared_task
from django.core.mail import EmailMessage
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

logger = logging.getLogger(__name__)


def generate_qr_image(token_str):
    """Generate a QR code image as bytes."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(token_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


def generate_ticket_pdf_bytes(booking):
    """Generate a PDF ticket with QR code embedded."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('title', parent=styles['Title'], fontSize=22, textColor=colors.HexColor('#1a1a2e'))
    label_style = ParagraphStyle('label', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
    value_style = ParagraphStyle('value', parent=styles['Normal'], fontSize=13, fontName='Helvetica-Bold')

    # Header
    elements.append(Paragraph('EVENT TICKET', title_style))
    elements.append(Spacer(1, 0.5 * cm))

    # Event Details Table
    data = [
        ['Event', booking.event.title],
        ['Date & Time', booking.event.start_datetime.strftime('%d %B %Y, %I:%M %p')],
        ['Venue', booking.event.venue],
        ['City', booking.event.city],
        ['Ticket Type', booking.ticket_type.name],
        ['Attendee', booking.user.full_name],
        ['Email', booking.user.email],
        ['Booking Ref', booking.booking_reference],
        ['Qty', str(booking.quantity)],
        ['Total Paid', f'INR {booking.total_amount}'],
    ]

    table = Table(data, colWidths=[4 * cm, 12 * cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 1 * cm))

    # QR Code
    try:
        qr_buffer = generate_qr_image(str(booking.qrcode.token))
        qr_img = Image(qr_buffer, width=5 * cm, height=5 * cm)
        elements.append(Paragraph('Scan QR Code at Entry:', label_style))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(qr_img)
    except Exception:
        pass

    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph('This is your official entry pass. Please present at the venue.', label_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer


@shared_task(bind=True, max_retries=3)
def generate_ticket_pdf_and_send_email(self, booking_id):
    """
    Celery Task 1:
    - Generate QR code and save to DB
    - Generate PDF ticket
    - Send email with PDF attachment
    """
    from apps.bookings.models import Booking
    from apps.qrcodes.models import QRCode

    try:
        booking = Booking.objects.select_related(
            'user', 'event', 'ticket_type'
        ).get(pk=booking_id)

        # Generate and save QR code
        qr_obj, created = QRCode.objects.get_or_create(booking=booking)
        qr_buffer = generate_qr_image(str(qr_obj.token))
        qr_obj.qr_image.save(
            f'qr_{booking.booking_reference}.png',
            ContentFile(qr_buffer.read()),
            save=True
        )

        # Generate PDF
        pdf_buffer = generate_ticket_pdf_bytes(booking)
        booking.ticket_pdf.save(
            f'ticket_{booking.booking_reference}.pdf',
            ContentFile(pdf_buffer.read()),
            save=True
        )

        # Send email
        email = EmailMessage(
            subject=f'Your Ticket for {booking.event.title}',
            body=f"""Hi {booking.user.full_name},

Your booking is confirmed!

Event: {booking.event.title}
Date: {booking.event.start_datetime.strftime('%d %B %Y, %I:%M %p')}
Venue: {booking.event.venue}, {booking.event.city}
Ticket Type: {booking.ticket_type.name}
Booking Ref: {booking.booking_reference}
Quantity: {booking.quantity}
Total Paid: INR {booking.total_amount}

Please find your ticket PDF attached. Show the QR code at the venue entry.

See you at the event!
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[booking.user.email],
        )

        # Attach PDF
        booking.ticket_pdf.seek(0) if hasattr(booking.ticket_pdf, 'seek') else None
        with booking.ticket_pdf.open('rb') as pdf_file:
            email.attach(
                f'ticket_{booking.booking_reference}.pdf',
                pdf_file.read(),
                'application/pdf'
            )

        email.send()
        logger.info(f'Ticket sent to {booking.user.email} for booking {booking.booking_reference}')

    except Exception as exc:
        logger.error(f'Failed to generate ticket for booking {booking_id}: {exc}')
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True)
def send_event_reminder(self, event_id):
    """
    Celery Task 2:
    - Send reminder email to all confirmed attendees 24 hours before event
    """
    from apps.events.models import Event
    from apps.bookings.models import Booking

    try:
        event = Event.objects.get(pk=event_id)
        bookings = Booking.objects.filter(
            event=event, status=Booking.CONFIRMED
        ).select_related('user')

        for booking in bookings:
            email = EmailMessage(
                subject=f'Reminder: {event.title} is tomorrow',
                body=f"""Hi {booking.user.full_name},

Just a reminder that your event is tomorrow!

Event: {event.title}
Date: {event.start_datetime.strftime('%d %B %Y, %I:%M %p')}
Venue: {event.venue}, {event.city}
Booking Ref: {booking.booking_reference}

Don't forget to bring your ticket QR code for entry.

See you there!
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[booking.user.email],
            )
            email.send()

        logger.info(f'Reminders sent for event {event.title} to {bookings.count()} attendees')

    except Exception as exc:
        logger.error(f'Failed to send reminders for event {event_id}: {exc}')


@shared_task
def auto_cancel_unpaid_booking(booking_id):
    """
    Celery Task 3:
    - Auto cancel booking if payment is not completed in 15 minutes
    - Releases ticket quota back
    """
    from apps.bookings.models import Booking, Payment

    try:
        booking = Booking.objects.select_related('payment').get(pk=booking_id)

        if booking.status == Booking.PENDING:
            booking.status = Booking.CANCELLED
            booking.save()

            if hasattr(booking, 'payment') and booking.payment.status == Payment.INITIATED:
                booking.payment.status = Payment.FAILED
                booking.payment.save()

            logger.info(f'Auto-cancelled unpaid booking {booking.booking_reference}')

    except Booking.DoesNotExist:
        logger.warning(f'Booking {booking_id} not found for auto-cancel')
    except Exception as exc:
        logger.error(f'Failed to auto-cancel booking {booking_id}: {exc}')


@shared_task
def schedule_event_reminders():
    """
    Celery Beat Task:
    - Runs every hour, finds events starting in ~24 hours
    - Schedules reminder emails
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.events.models import Event

    now = timezone.now()
    reminder_window_start = now + timedelta(hours=23)
    reminder_window_end = now + timedelta(hours=25)

    events = Event.objects.filter(
        start_datetime__gte=reminder_window_start,
        start_datetime__lte=reminder_window_end,
        status=Event.PUBLISHED
    )

    for event in events:
        send_event_reminder.delay(event.id)
        logger.info(f'Scheduled reminder for event: {event.title}')
