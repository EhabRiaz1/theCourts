from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta, time
import random
import string
from decimal import Decimal
from .models import Court, Booking, UserProfile
from .serializers import CourtSerializer, BookingSerializer, UserProfileSerializer
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin, AllowAnyCreateIsAuthenticatedOrReadOnly
from django.contrib.auth.mixins import UserPassesTestMixin
from .notifications import get_booking_status
from django.http import JsonResponse

# Template Views
class HomeView(TemplateView):
    template_name = 'courts/home.html'

def booking_view(request):
    context = {
        'pickle_ball_price': Court.objects.filter(court_type__startswith='PICKLE').first().hourly_rate,
        'paddle_ball_price': Court.objects.filter(court_type='PADDLE').first().hourly_rate,
        'user': request.user,
        'is_authenticated': request.user.is_authenticated,
    }
    print(f"User authenticated in view: {request.user.is_authenticated}")
    return render(request, 'courts/booking.html', context)

# API ViewSets
class CourtViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Court.objects.filter(is_active=True)
    serializer_class = CourtSerializer
    
    def get_available_courts(self, sport_type, start_time, end_time):
        """Get available courts for a specific time slot"""
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
        
        available_courts = []
        for court in courts:
            if not Booking.objects.filter(
                court=court,
                status__in=['PENDING', 'APPROVED'],
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists():
                available_courts.append(court)
        
        return available_courts

    @action(detail=False, methods=['get'])
    def check_availability(self, request):
        """Real-time availability checking endpoint"""
        try:
            date_str = request.query_params.get('date')
            start_time_str = request.query_params.get('start_time')
            duration_hours = float(request.query_params.get('duration', 1))
            sport_type = request.query_params.get('sport_type')

            if not all([date_str, start_time_str, sport_type]):
                return Response(
                    {"error": "Missing required parameters"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Combine date and time
            start_time = datetime.strptime(
                f"{date_str} {start_time_str}",
                '%Y-%m-%d %H:%M'
            )
            end_time = start_time + timedelta(hours=duration_hours)

            # Validate booking time
            current_time = timezone.now()
            if start_time <= current_time + timedelta(minutes=15):
                return Response(
                    {"error": "Bookings must be made at least 15 minutes in advance"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get available courts
            available_courts = self.get_available_courts(sport_type, start_time, end_time)
            
            return Response({
                'available': len(available_courts) > 0,
                'courts': [
                    {
                        'id': court.id,
                        'name': court.name,
                        'type': court.court_type,
                        'hourly_rate': court.hourly_rate
                    }
                    for court in available_courts
                ]
            })

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def schedule(self, request):
        """Get court schedule for a specific date"""
        try:
            date_str = request.query_params.get('date')
            sport_type = request.query_params.get('sport_type')

            if not date_str:
                return Response(
                    {"error": "Date is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Get relevant courts
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

            # Get all bookings for these courts on the specified date
            bookings = Booking.objects.filter(
                court__in=courts,
                start_time__date=date,
                status__in=['PENDING', 'APPROVED']
            ).order_by('start_time')

            # Prepare schedule
            schedule = {}
            for court in courts:
                court_bookings = bookings.filter(court=court)
                schedule[court.name] = [
                    {
                        'booking_reference': booking.booking_reference,
                        'start_time': booking.start_time.strftime('%H:%M'),
                        'end_time': booking.end_time.strftime('%H:%M'),
                        'status': booking.status,
                        'duration_hours': booking.duration_hours
                    }
                    for booking in court_bookings
                ]

            return Response({
                'date': date_str,
                'schedule': schedule
            })

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        """Get available time slots for a specific date and sport"""
        try:
            # Log request parameters
            print("Request params:", request.query_params)
            
            # Get parameters from request
            date_str = request.query_params.get('date')
            sport_type = request.query_params.get('sport_type')
            duration = float(request.query_params.get('duration', 2))

            print(f"Processing request - Date: {date_str}, Sport: {sport_type}, Duration: {duration}")

            if not all([date_str, sport_type]):
                print("Missing required parameters")
                return Response(
                    {"error": "Date and sport type are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError as e:
                print(f"Date parsing error: {e}")
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get courts based on sport type
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

            print(f"Found {courts.count()} courts for {sport_type}")

            if not courts.exists():
                print("No courts found")
                return Response(
                    {"error": "No courts available for selected sport"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Generate time slots
            available_slots = []
            current_time = timezone.localtime()
            
            # Generate slots from 6 AM to 3 AM next day
            start_hour = 6
            end_hour = 27  # 3 AM next day (24 + 3)

            print(f"Generating slots from {start_hour}:00 to {end_hour % 24}:00")

            for hour in range(start_hour, end_hour):
                actual_hour = hour % 24
                slot_date = date
                
                if hour >= 24:
                    slot_date = date + timedelta(days=1)

                for minute in [0, 30]:
                    slot_time = datetime.combine(slot_date, time(actual_hour, minute))
                    slot_datetime = timezone.make_aware(slot_time)
                    
                    if slot_datetime <= current_time:
                        continue

                    end_time = slot_datetime + timedelta(hours=duration)
                    
                    # Enhanced validation for closed hours
                    def is_closed_hour(hour):
                        return 3 < hour < 6
                    
                    # Skip if start or end time is in closed hours
                    if is_closed_hour(slot_datetime.hour) or is_closed_hour(end_time.hour):
                        continue
                    
                    # Skip if booking spans across closed hours
                    if slot_datetime.hour <= 3 and end_time.hour >= 6:
                        continue

                    # Check availability across all courts
                    is_available = False
                    for court in courts:
                        existing_bookings = Booking.objects.filter(
                            court=court,
                            status__in=['PENDING', 'APPROVED'],
                            start_time__lt=end_time,
                            end_time__gt=slot_datetime
                        )
                        if not existing_bookings.exists():
                            is_available = True
                            break

                    if is_available:
                        available_slots.append({
                            'start_time': slot_datetime.isoformat(),
                            'end_time': end_time.isoformat()
                        })

            print(f"Found {len(available_slots)} available slots")
            return Response({
                'available_slots': available_slots
            })

        except Exception as e:
            print(f"Error in available_slots: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from datetime import datetime, timedelta, time
import random
import string
from .models import Court, Booking
from .serializers import BookingSerializer

class AdminBaseMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

class AdminDashboardView(AdminBaseMixin, TemplateView):
    template_name = 'courts/admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get counts for different booking statuses
        context['pending_count'] = Booking.objects.filter(status='PENDING').count()
        context['approved_count'] = Booking.objects.filter(status='APPROVED').count()
        context['rejected_count'] = Booking.objects.filter(status='REJECTED').count()
        context['cancelled_count'] = Booking.objects.filter(status='CANCELLED').count()
        
        # Get today's bookings
        today = timezone.now().date()
        context['todays_bookings'] = Booking.objects.filter(
            start_time__date=today
        ).order_by('start_time')
        
        return context

class PendingBookingsView(AdminBaseMixin, TemplateView):
    template_name = 'courts/admin/pending_bookings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bookings'] = Booking.objects.filter(
            status='PENDING'
        ).order_by('start_time')
        context['court_types'] = Court.COURT_TYPES
        return context

class AllBookingsView(AdminBaseMixin, TemplateView):
    template_name = 'courts/admin/all_bookings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bookings'] = Booking.objects.all().order_by('-created_at')
        context['court_types'] = Court.COURT_TYPES
        return context

def admin_dashboard(request):
    # Your logic here
    return render(request, 'courts/admin_dashboard.html')

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = (AllowAnyCreateIsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        print("=== Booking Creation Debug ===")
        print("Request method:", request.method)
        print("Request user:", request.user)
        print("Request auth:", request.auth)
        print("Request headers:", request.headers)
        print("Request data:", request.data)
        print("===========================")
        
        data = request.data.copy()
        
        # Generate booking reference
        now = timezone.now()
        while True:
            random_digits = ''.join(random.choices(string.digits, k=4))
            booking_reference = f"{now.strftime('%y%m')}{random_digits}"
            if not Booking.objects.filter(booking_reference=booking_reference).exists():
                break
        
        data['booking_reference'] = booking_reference

        # Handle authenticated users
        if request.user.is_authenticated:
            print("User info:", {
                "id": request.user.id,
                "email": request.user.email,
                "full_name": request.user.get_full_name()
            })
            
            data['user'] = request.user.id
            # Use user's information if guest info not provided
            if not data.get('guest_name'):
                data['guest_name'] = request.user.get_full_name() or request.user.email
            if not data.get('guest_email'):
                data['guest_email'] = request.user.email
            if not data.get('guest_phone'):
                # Try to get phone from user profile if it exists
                try:
                    profile = request.user.userprofile
                    data['guest_phone'] = getattr(profile, 'phone', '')
                except:
                    data['guest_phone'] = ''

        print("Processed data before validation:", data)

        # Validate time slot availability
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        duration_hours = float(data['duration_hours'])
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Get appropriate courts based on sport type
        if data['sport_type'] == 'PICKLE':
            courts = Court.objects.filter(
                court_type__in=['PICKLE_PRIORITY', 'PICKLE_STANDARD'],
                is_active=True
            )
        else:
            courts = Court.objects.filter(
                court_type='PADDLE',
                is_active=True
            )

        # Find an available court
        available_court = None
        for court in courts:
            if not Booking.objects.filter(
                court=court,
                status__in=['PENDING', 'APPROVED'],
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists():
                available_court = court
                break

        if not available_court:
            return Response(
                {"error": "No courts available for selected time slot"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate total price
        data['court'] = available_court.id
        data['end_time'] = end_time.isoformat()
        data['total_price'] = float(available_court.hourly_rate) * duration_hours

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
            
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class BookingStatusView(TemplateView):
    template_name = 'courts/booking_status.html'
    
    def get(self, request, *args, **kwargs):
        reference = request.GET.get('reference')
        
        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if not reference:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Reference number is required'
                })
            
            result = get_booking_status(reference)
            return JsonResponse(result, safe=False)
            
        # For regular requests, render the template
        context = self.get_context_data(**kwargs)
        if reference:
            context['result'] = get_booking_status(reference)
            context['reference'] = reference
        return self.render_to_response(context)