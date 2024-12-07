from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.booking_views import BookingViewSet
from courts.views import CourtViewSet

router = DefaultRouter()
router.register(r'bookings', BookingViewSet)
router.register(r'courts', CourtViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
