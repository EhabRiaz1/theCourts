from django.urls import path
from .views.auth import LoginView, LogoutView
from .views.dashboard import DashboardView
from .views.bookings import (
    PendingBookingsView,
    AllBookingsView,
    BookingHistoryView,
    CourtCalendarView,
    AnalyticsView,
    UpdateBookingStatusView
)

app_name = 'management'

urlpatterns = [
    # Authentication URLs
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('', DashboardView.as_view(), name='dashboard'),
    
    # Booking Management URLs
    path('bookings/pending/', PendingBookingsView.as_view(), name='pending_bookings'),
    path('bookings/all/', AllBookingsView.as_view(), name='all_bookings'),
    path('bookings/history/', BookingHistoryView.as_view(), name='booking_history'),
    path('bookings/calendar/', CourtCalendarView.as_view(), name='court_calendar'),
    path('bookings/analytics/', AnalyticsView.as_view(), name='analytics'),
    
    # API Endpoints
    path('api/bookings/<int:pk>/update-status/', 
         UpdateBookingStatusView.as_view(), 
         name='update_booking_status'),
] 