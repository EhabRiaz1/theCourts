from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import BookingViewSet, BookingStatusView

router = DefaultRouter()
router.register(r'courts', views.CourtViewSet, basename='court')
router.register(r'bookings', BookingViewSet)

app_name = 'courts'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('booking/', views.booking_view, name='booking'),
    path('api/courts/available_slots/', views.CourtViewSet.as_view({'get': 'available_slots'}), name='available-slots'),
    path('api/', include(router.urls)),
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('booking_status/', views.BookingStatusView.as_view(), name='booking_status'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)