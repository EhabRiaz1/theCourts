import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

class NotificationService:
    @staticmethod
    def send_booking_notification(booking):
        """Send initial booking notification via WhatsApp"""
        message = f"""
        Hello {booking.guest_name}!
        
        Thank you for booking with The Courts!
        
        Booking Details:
        Reference: {booking.booking_reference}
        Date: {booking.start_time.strftime('%B %d, %Y')}
        Time: {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}
        Total Amount: PKR {booking.total_price}
        
        Payment Instructions:
        Bank: [Bank Name]
        Account Title: [Account Title]
        Account Number: [Account Number]
        
        Please complete your payment and share the receipt with us.
        Your booking will be confirmed after payment verification.
        """
        NotificationService._send_whatsapp_message(booking, message)

    @staticmethod
    def send_status_notification(booking):
        """Send booking status update notifications"""
        if booking.status == 'APPROVED':
            message = f"""
            Hello {booking.guest_name}!
            
            Your booking at The Courts has been approved!
            
            Booking Details:
            Reference: {booking.booking_reference}
            Date: {booking.start_time.strftime('%B %d, %Y')}
            Time: {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}
            Court: {booking.court.name}
            
            We look forward to seeing you!
            """
        elif booking.status == 'REJECTED':
            message = f"""
            Hello {booking.guest_name},
            
            Unfortunately, your booking request (Ref: {booking.booking_reference}) could not be confirmed.
            
            Please contact us for more information or to make a new booking.
            """
        elif booking.status == 'CANCELLED':
            message = f"""
            Hello {booking.guest_name},
            
            Your booking (Ref: {booking.booking_reference}) has been cancelled.
            
            If you did not request this cancellation, please contact us immediately.
            """
        else:
            return

        NotificationService._send_whatsapp_message(booking, message)

    @staticmethod
    def _send_whatsapp_message(booking, message):
        """Helper function to send WhatsApp messages"""
        try:
            client = Client(
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            )
            
            client.messages.create(
                body=message.strip(),
                from_=f'whatsapp:{os.getenv("TWILIO_WHATSAPP_FROM")}',
                to=f'whatsapp:{booking.whatsapp_number}'
            )
        except Exception as e:
            print(f"WhatsApp notification failed: {str(e)}") 