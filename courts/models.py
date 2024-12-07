from django.conf import settings
from django.db import models
from datetime import datetime, time, timedelta
from rest_framework import permissions

class Court(models.Model):
    COURT_TYPES = [
        ('PICKLE_PRIORITY', 'Pickle Priority'),
        ('PICKLE_STANDARD', 'Pickle Standard'),
        ('PADDLE', 'Paddle'),
    ]
    
    name = models.CharField(max_length=100)
    court_type = models.CharField(max_length=20, choices=COURT_TYPES)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    half_hour_rate = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_court_type_display()})"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    court = models.ForeignKey(Court, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)  # Updated this line
    guest_name = models.CharField(max_length=100, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)
    guest_phone = models.CharField(max_length=20, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    booking_reference = models.CharField(
        max_length=8,  # YYMMXXXX format
        unique=True,
        db_index=True,
        blank=False,
        null=False,
        help_text="Format: YYMMXXXX (Year, Month, Random Digits)"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.booking_reference} - {self.guest_name}"

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    loyalty_points = models.IntegerField(default=0)
    referral_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Profile for {self.user.get_full_name() or self.user.email}"
    
class CourtSchedule:
    @staticmethod
    def get_day_schedule(date, court):
        """Get schedule for a specific court on a specific date"""
        return Booking.objects.filter(
            court=court,
            start_time__date=date,
            status__in=['PENDING', 'APPROVED']
        ).order_by('start_time')

    @staticmethod
    def get_available_slots(date, court, min_duration=1):
        """Get available time slots for a specific court on a specific date"""
        bookings = CourtSchedule.get_day_schedule(date, court)
        
        # Start and end times for the day
        start_of_day = datetime.combine(date, time(6, 0))  # 6 AM
        end_of_day = datetime.combine(date + timedelta(days=1), time(3, 0))  # 3 AM next day
        
        # Find gaps between bookings
        available_slots = []
        current_time = start_of_day
        
        for booking in bookings:
            if (booking.start_time - current_time).total_seconds() / 3600 >= min_duration:
                available_slots.append({
                    'start': current_time,
                    'end': booking.start_time
                })
            current_time = booking.end_time
        
        # Add final slot if available
        if (end_of_day - current_time).total_seconds() / 3600 >= min_duration:
            available_slots.append({
                'start': current_time,
                'end': end_of_day
            })
        
        return available_slots

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user