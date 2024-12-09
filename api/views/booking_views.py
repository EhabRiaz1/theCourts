from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from courts.models import Court, Booking
from api.serializers.booking_serializers import BookingSerializer
import random
import string
from django.db import transaction

class AllowAnyForCreateBookingPermission(permissions.BasePermission):
    """
    Custom permission to allow anyone to create a booking,
    but require authentication for other actions
    """
    def has_permission(self, request, view):
        # Allow create (POST) for everyone
        if view.action == 'create':
            return True
        # For other actions, require authentication
        return request.user and request.user.is_authenticated

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [AllowAnyForCreateBookingPermission]

    def generate_booking_reference(self):
        """Generate a unique booking reference"""
        prefix = timezone.now().strftime('%y%m')
        
        for _ in range(10):
            random_digits = ''.join(random.choices(string.digits, k=4))
            reference = f"{prefix}{random_digits}"
            
            if not Booking.objects.filter(booking_reference=reference).exists():
                return reference
            
        raise ValueError("Failed to generate unique booking reference after multiple attempts")

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                data = request.data.copy()
                
                # Generate and validate booking reference
                booking_ref = self.generate_booking_reference()
                data['booking_reference'] = booking_ref
                
                start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
                duration_hours = float(data['duration_hours'])
                end_time = start_time + timedelta(hours=duration_hours)

                # Handle user information
                if request.user.is_authenticated:
                    data.update({
                        'guest_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                        'guest_email': request.user.email,
                        'user': request.user.id
                    })
                    # Only update phone if not provided in request
                    if 'guest_phone' not in data:
                        data['guest_phone'] = getattr(request.user, 'phone_number', '')

                # Get court based on court ID directly from request
                court = Court.objects.get(id=data['court'])
                
                # Calculate price
                hourly_rate = Decimal(str(court.hourly_rate))
                duration_decimal = Decimal(str(duration_hours))
                total_price = (hourly_rate * duration_decimal).quantize(Decimal('0.01'))

                # Update data with calculated fields
                data.update({
                    'end_time': end_time.isoformat(),
                    'total_price': str(total_price),
                    'duration_hours': duration_hours,
                    'status': 'PENDING'
                })

                print(f"Data before serialization: {data}")  # Debug print
                
                serializer = self.get_serializer(data=data)
                if not serializer.is_valid():
                    print(f"Serializer errors: {serializer.errors}")
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                booking = serializer.save()

                return Response({
                    'booking_reference': booking.booking_reference,
                    'status': 'success',
                    'message': 'Booking created successfully',
                    'total_price': str(booking.total_price)
                }, status=status.HTTP_201_CREATED)

        except Court.DoesNotExist:
            return Response({"error": "Invalid court ID"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "An unexpected error occurred", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 