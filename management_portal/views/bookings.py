from django.views.generic import ListView, TemplateView, View
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ..mixins import ManagementLoginRequiredMixin
from courts.models import Booking, Court
from courts.notifications import send_booking_status_notification
from datetime import datetime, timedelta
import json
from django.utils.safestring import mark_safe

class PendingBookingsView(ManagementLoginRequiredMixin, ListView):
    template_name = 'management_portal/bookings/pending.html'
    context_object_name = 'bookings'
    
    def get_queryset(self):
        return Booking.objects.filter(
            status='PENDING'
        ).order_by('start_time')

class AllBookingsView(ManagementLoginRequiredMixin, ListView):
    template_name = 'management_portal/bookings/all.html'
    context_object_name = 'bookings'
    
    def get_queryset(self):
        return Booking.objects.filter(
            status='APPROVED',
            end_time__gte=timezone.now()
        ).order_by('start_time')

class BookingHistoryView(ManagementLoginRequiredMixin, ListView):
    template_name = 'management_portal/bookings/history.html'
    context_object_name = 'bookings'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Booking.objects.all().order_by('-created_at')
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Filter by date range if provided
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(created_at__range=[start, end])
            except ValueError:
                pass
                
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Booking.STATUS_CHOICES
        return context

class CourtCalendarView(ManagementLoginRequiredMixin, TemplateView):
    template_name = 'management_portal/bookings/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all courts grouped by type
        courts_by_type = {}
        for court in Court.objects.filter(is_active=True).order_by('court_type', 'name'):
            if court.court_type not in courts_by_type:
                courts_by_type[court.court_type] = {
                    'courts': [],
                    'events': []
                }
            courts_by_type[court.court_type]['courts'].append({
                'id': court.id,
                'name': court.name
            })
        
        # Get bookings
        bookings = Booking.objects.filter(
            Q(status='PENDING') | Q(status='APPROVED'),
            start_time__gte=timezone.now() - timedelta(days=7),
            start_time__lte=timezone.now() + timedelta(days=30)
        ).select_related('court')
        
        # Organize bookings by court type
        for booking in bookings:
            court_type = booking.court.court_type
            if court_type in courts_by_type:
                courts_by_type[court_type]['events'].append({
                    'id': str(booking.id),
                    'resourceId': booking.court.id,
                    'title': f"{booking.guest_name} ({booking.booking_reference})",
                    'start': booking.start_time.isoformat(),
                    'end': booking.end_time.isoformat(),
                    'className': booking.status.lower(),
                    'extendedProps': {
                        'reference': booking.booking_reference,
                        'guest_name': booking.guest_name,
                        'court_name': booking.court.name,
                        'status': booking.status,
                        'notes': booking.admin_notes
                    }
                })
        
        context['calendar_data'] = courts_by_type
        context['calendar_data_json'] = mark_safe(json.dumps(courts_by_type))
        
        return context

class AnalyticsView(ManagementLoginRequiredMixin, TemplateView):
    template_name = 'management_portal/bookings/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range (default to current month)
        end_date = timezone.now()
        start_date = self.request.GET.get('start_date')
        end_date_param = self.request.GET.get('end_date')
        
        if start_date and end_date_param:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_param, '%Y-%m-%d')
            except ValueError:
                start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get approved bookings within date range
        bookings = Booking.objects.filter(
            status='APPROVED',
            start_time__range=[start_date, end_date]
        )
        
        # Calculate revenue by court type
        revenue_by_type = {}
        for court_type, _ in Court.COURT_TYPES:
            revenue = bookings.filter(
                court__court_type=court_type
            ).aggregate(
                total_revenue=Sum('total_price'),
                booking_count=Count('id')
            )
            revenue_by_type[court_type] = {
                'revenue': revenue['total_revenue'] or 0,
                'count': revenue['booking_count'] or 0
            }
        
        context.update({
            'revenue_by_type': revenue_by_type,
            'start_date': start_date,
            'end_date': end_date,
            'total_revenue': sum(data['revenue'] for data in revenue_by_type.values()),
            'total_bookings': sum(data['count'] for data in revenue_by_type.values())
        })
        return context

class UpdateBookingStatusView(ManagementLoginRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        # Get status from either POST data or form data
        status = request.POST.get('status') or request.data.get('status')
        notes = request.POST.get('notes', '')
        
        if status not in dict(Booking.STATUS_CHOICES):
            return JsonResponse({'error': 'Invalid status'}, status=400)
            
        booking.status = status
        if notes:
            booking.admin_notes = notes
        booking.save()
        
        # Send notification
        try:
            send_booking_status_notification(booking)
        except Exception as e:
            print(f"Failed to send notification: {e}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Booking {booking.booking_reference} has been {status.lower()}'
        }) 