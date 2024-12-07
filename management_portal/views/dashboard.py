from django.views.generic import TemplateView
from ..mixins import ManagementLoginRequiredMixin
from courts.models import Booking

class DashboardView(ManagementLoginRequiredMixin, TemplateView):
    template_name = 'management_portal/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get booking counts by status
        context['pending_count'] = Booking.objects.filter(status='PENDING').count()
        context['approved_count'] = Booking.objects.filter(status='APPROVED').count()
        context['rejected_count'] = Booking.objects.filter(status='REJECTED').count()
        context['cancelled_count'] = Booking.objects.filter(status='CANCELLED').count()
        
        # Get recent bookings
        context['recent_bookings'] = Booking.objects.all().order_by('-created_at')[:5]
        
        return context 