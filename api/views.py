from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from courts.models import Court, Booking
from courts.notifications import send_booking_notification, send_booking_status_notification
from .serializers import CourtSerializer, BookingSerializer, BookingStatsSerializer
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.permissions import AllowAny, IsAuthenticated
import random
import string

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [AllowAny]



    def create(self, request, *args, **kwargs):
        try:
            # Debug logging
            print("Request Data:", request.data)
            
            # Generate booking reference
            now = timezone.now()
            while True:
                random_digits = ''.join(random.choices(string.digits, k=4))
                booking_reference = f"{now.strftime('%y%m')}{random_digits}"
                if not Booking.objects.filter(booking_reference=booking_reference).exists():
                    break

            # Get data from request
            data = request.data.copy()
            data['booking_reference'] = booking_reference
            
            print("Modified Data:", data)
            
            # Create serializer with request context
            serializer = self.get_serializer(data=data, context={'request': request})
            
            if not serializer.is_valid():
                print("Serializer Errors:", serializer.errors)
                return Response(
                    {"error": serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            booking = serializer.save()
            print("Booking Created:", booking)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            print("Exception:", str(e))
            print("Traceback:", traceback.format_exc())
            return Response(
                {"error": str(e), "detail": traceback.format_exc()}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get booking statistics"""
        today = timezone.now().date()
        
        # Get date range from query params
        range_type = request.query_params.get('range', 'daily')
        start_date = request.query_params.get('start_date', today.isoformat())
        end_date = request.query_params.get('end_date', today.isoformat())

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get bookings within date range
        bookings = Booking.objects.filter(
            start_time__date__range=[start_date, end_date]
        )

        # Calculate statistics by court type
        stats = bookings.values('court__court_type').annotate(
            total_bookings=Count('id'),
            total_revenue=Sum('total_price')
        )

        return Response({
            'range': range_type,
            'start_date': start_date,
            'end_date': end_date,
            'stats': stats
        })

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending bookings in chronological order"""
        pending_bookings = Booking.objects.filter(
            status='PENDING'
        ).order_by('start_time')

        serializer = self.get_serializer(pending_bookings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update booking status and send notification"""
        booking = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Booking.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = new_status
        booking.save()
        
        # Send WhatsApp notification
        send_booking_status_notification(booking)
        
        return Response({"status": "updated"})

    def get_queryset(self):
        """
        Filter bookings based on user authentication status:
        - Authenticated users see their own bookings
        - Staff users see all bookings
        - Unauthenticated users can only create bookings
        """
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return Booking.objects.all()
            return Booking.objects.filter(user=user)
        return Booking.objects.none()

# Create your views here.