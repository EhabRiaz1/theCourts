from datetime import datetime, timedelta
from django.utils import timezone
from courts.models import Court, Booking

class CourtService:
    @staticmethod
    def assign_court(sport_type, start_time, end_time):
        """Assign appropriate court based on sport type and availability"""
        if sport_type == 'PICKLE':
            # Try Priority court first
            priority_court = Court.objects.filter(
                court_type='PICKLE_PRIORITY',
                is_active=True
            ).first()
            
            if priority_court and CourtService.check_availability(priority_court, start_time, end_time):
                return priority_court
                
            # Try Standard court if Priority is not available
            standard_court = Court.objects.filter(
                court_type='PICKLE_STANDARD',
                is_active=True
            ).first()
            
            if standard_court and CourtService.check_availability(standard_court, start_time, end_time):
                return standard_court
        else:
            # Handle Paddle court
            paddle_court = Court.objects.filter(
                court_type='PADDLE',
                is_active=True
            ).first()
            
            if paddle_court and CourtService.check_availability(paddle_court, start_time, end_time):
                return paddle_court
                
        return None

    @staticmethod
    def check_availability(court, start_time, end_time):
        """Check if court is available for the given time slot"""
        return not Booking.objects.filter(
            court=court,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=['PENDING', 'APPROVED']
        ).exists()

    @staticmethod
    def validate_booking_time(start_time, end_time):
        """Validate booking time constraints"""
        current_time = timezone.now()
        duration = (end_time - start_time).total_seconds() / 3600
        
        if start_time <= current_time + timedelta(minutes=15):
            raise ValueError("Bookings must be made at least 15 minutes in advance")
        
        # Check if either start or end time falls in closed hours
        start_hour = start_time.hour
        end_hour = end_time.hour
        
        # Helper function to check if hour is in closed period
        def is_closed_hour(hour):
            return 3 < hour < 6
        
        if is_closed_hour(start_hour) or is_closed_hour(end_hour):
            raise ValueError("Bookings cannot start or end between 3 AM and 6 AM")
        
        # Check if booking spans across closed hours
        if start_hour <= 3 and end_hour >= 6:
            raise ValueError("Bookings cannot span across closed hours (3 AM - 6 AM)")
        
        # Add logging to show time slots
        print("\n=== Booking Time Slots ===")
        current = start_time
        while current < end_time:
            next_slot = current + timedelta(minutes=30)
            print(f"Slot: {current.strftime('%I:%M %p')} - {next_slot.strftime('%I:%M %p')}")
            current = next_slot
        print("=======================\n")
        
        if duration < 1:
            raise ValueError("Minimum booking duration is 1 hour")
        if duration > 7:
            raise ValueError("Maximum booking duration is 7 hours")
        if duration % 0.5 != 0:
            raise ValueError("Booking duration must be in increments of 30 minutes") 