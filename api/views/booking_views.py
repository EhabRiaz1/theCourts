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

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

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
                if not booking_ref:
                    raise ValueError("Empty booking reference generated")
                
                # Ensure booking reference is set
                data['booking_reference'] = booking_ref
                
                start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
                duration_hours = float(data['duration_hours'])
                end_time = start_time + timedelta(hours=duration_hours)

                # Handle user information
                if request.user.is_authenticated:
                    data['guest_name'] = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
                    data['guest_email'] = request.user.email
                    data['guest_phone'] = getattr(request.user, 'phone_number', '')
                    data['user'] = request.user.id
                else:
                    # Validate guest information is provided
                    if not all([data.get('guest_name'), data.get('guest_email'), data.get('guest_phone')]):
                        return Response(
                            {"error": "Guest information (name, email, and phone) is required"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                sport_type = data.pop('sport_type')
                if sport_type == 'PICKLE':
                    courts = Court.objects.filter(
                        court_type__in=['PICKLE_PRIORITY', 'PICKLE_STANDARD'],
                        is_active=True
                    )
                else:
                    courts = Court.objects.filter(
                        court_type='PADDLE',
                        is_active=True
                    )

                court = None
                for c in courts:
                    if not Booking.objects.filter(
                        court=c,
                        status__in=['PENDING', 'APPROVED'],
                        start_time__lt=end_time,
                        end_time__gt=start_time
                    ).exists():
                        court = c
                        break

                if not court:
                    raise ValueError("No courts available for the selected time")

                hourly_rate = Decimal(str(court.hourly_rate))
                duration_decimal = Decimal(str(duration_hours))
                total_price = (hourly_rate * duration_decimal).quantize(Decimal('0.01'))

                # Update data with required fields
                data.update({
                    'court': court.id,
                    'end_time': end_time.isoformat(),
                    'total_price': str(total_price),  # Ensure total_price is a string
                    'duration_hours': duration_hours,
                    'status': 'PENDING'
                })

                print(f"Data before serialization: {data}")  # Debug print
                
                serializer = self.get_serializer(data=data)
                if not serializer.is_valid():
                    print(f"Serializer errors: {serializer.errors}")
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                print(f"Validated data: {serializer.validated_data}")  # Debug print
                
                booking = serializer.save()
                
                # Verify all required fields were saved
                if not booking.total_price:
                    raise ValueError("Total price was not saved correctly")

                return Response({
                    'booking_reference': booking.booking_reference,
                    'status': 'success',
                    'message': 'Booking created successfully',
                    'total_price': str(booking.total_price)  # Include in response
                }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            print(f"ValueError: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 