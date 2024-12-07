import os
from django.core.mail import send_mail
from django.template.loader import render_to_string
from twilio.rest import Client
from dotenv import load_dotenv
from django.core.exceptions import ObjectDoesNotExist
from courts.models import Booking

load_dotenv()

def send_booking_notification(booking):
    """Send booking notifications via email and WhatsApp"""
    # Send email
    send_booking_email(booking)
    # Send WhatsApp message
    send_booking_whatsapp(booking)

def send_booking_status_notification(booking):
    """Send booking status update notifications"""
    if booking.status == 'APPROVED':
        send_approval_notification(booking)
    elif booking.status == 'REJECTED':
        send_rejection_notification(booking)
    elif booking.status == 'CANCELLED':
        send_cancellation_notification(booking)

def send_approval_notification(booking):
    """Send booking approval notifications"""
    # Email
    subject = f'Booking Approved - Reference #{booking.booking_reference}'
    html_message = render_to_string('courts/emails/booking_approved.html', {
        'booking': booking
    })
    
    send_mail(
        subject=subject,
        message='',
        html_message=html_message,
        from_email=os.getenv('EMAIL_HOST_USER'),
        recipient_list=[booking.guest_email],
        fail_silently=False,
    )
    
    # WhatsApp
    send_whatsapp_message(
        booking,
        f"""
        Hello {booking.guest_name}!
        
        Your booking at The Courts has been approved!
        
        Booking Details:
        Reference: {booking.booking_reference}
        Date: {booking.start_time.strftime('%B %d, %Y')}
        Time: {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}
        Court: {booking.court.name}
        
        We look forward to seeing you!
        """
    )

def send_rejection_notification(booking):
    """Send booking rejection notifications"""
    # Email
    subject = f'Booking Update - Reference #{booking.booking_reference}'
    html_message = render_to_string('courts/emails/booking_rejected.html', {
        'booking': booking
    })
    
    send_mail(
        subject=subject,
        message='',
        html_message=html_message,
        from_email=os.getenv('EMAIL_HOST_USER'),
        recipient_list=[booking.guest_email],
        fail_silently=False,
    )
    
    # WhatsApp
    send_whatsapp_message(
        booking,
        f"""
        Hello {booking.guest_name},
        
        Unfortunately, your booking request (Ref: {booking.booking_reference}) could not be confirmed.
        
        Please contact us for more information or to make a new booking.
        """
    )

def send_cancellation_notification(booking):
    """Send booking cancellation notifications"""
    # Email
    subject = f'Booking Cancelled - Reference #{booking.booking_reference}'
    html_message = render_to_string('courts/emails/booking_cancelled.html', {
        'booking': booking
    })
    
    send_mail(
        subject=subject,
        message='',
        html_message=html_message,
        from_email=os.getenv('EMAIL_HOST_USER'),
        recipient_list=[booking.guest_email],
        fail_silently=False,
    )
    
    # WhatsApp
    send_whatsapp_message(
        booking,
        f"""
        Hello {booking.guest_name},
        
        Your booking (Ref: {booking.booking_reference}) has been cancelled.
        
        If you did not request this cancellation, please contact us immediately.
        """
    )

def send_booking_reminder(booking):
    """Send booking reminder notification 24 hours before"""
    # Email
    subject = f'Booking Reminder - Reference #{booking.booking_reference}'
    html_message = render_to_string('courts/emails/booking_reminder.html', {
        'booking': booking
    })
    
    send_mail(
        subject=subject,
        message='',
        html_message=html_message,
        from_email=os.getenv('EMAIL_HOST_USER'),
        recipient_list=[booking.guest_email],
        fail_silently=False,
    )
    
    # WhatsApp
    send_whatsapp_message(
        booking,
        f"""
        Hello {booking.guest_name}!
        
        This is a reminder for your booking tomorrow:
        
        Reference: {booking.booking_reference}
        Date: {booking.start_time.strftime('%B %d, %Y')}
        Time: {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}
        Court: {booking.court.name}
        
        We look forward to seeing you!
        """
    )

def send_whatsapp_message(booking, message):
    """Helper function to send WhatsApp messages"""
    try:
        client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        
        client.messages.create(
            body=message,
            from_=f'whatsapp:{os.getenv("TWILIO_WHATSAPP_FROM")}',
            to=f'whatsapp:{booking.whatsapp_number}'
        )
    except Exception as e:
        print(f"WhatsApp notification failed: {str(e)}") 

def get_booking_status(booking_reference):
    """
    Get the status and details of a booking using its reference number.
    Returns a dictionary with booking information or error message.
    """
    try:
        booking = Booking.objects.get(booking_reference=booking_reference)
        
        return {
            'status': 'success',
            'data': {
                'reference': booking.booking_reference,
                'status': booking.get_status_display(),
                'guest_name': booking.guest_name,
                'court': booking.court.name,
                'date': booking.start_time.strftime('%B %d, %Y'),
                'time': f"{booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}",
                'created_at': booking.created_at.strftime('%B %d, %Y %I:%M %p'),
            }
        }
    except ObjectDoesNotExist:
        return {
            'status': 'error',
            'message': 'Booking not found. Please check your reference number and try again.'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': 'An error occurred while retrieving the booking information.'
        }

        