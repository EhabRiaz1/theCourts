from rest_framework import serializers
from courts.models import Booking, Court
from .court_serializers import CourtSerializer
from django.utils import timezone

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'id', 'court', 'guest_name', 'guest_email', 'guest_phone',
            'whatsapp_number', 'booking_reference', 'start_time', 'end_time',
            'duration_hours', 'total_price', 'status', 'created_at'
        ]
        read_only_fields = ['created_at']

    def validate(self, data):
        request = self.context.get('request')
        
        # Debug print
        print("Validation Data:", data)
        print("Request User:", request.user if request else "No request")
        
        # Validate start and end times
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        if end_time and start_time and end_time <= start_time:
            raise serializers.ValidationError("End time must be after start time")

        # Always require phone number
        if not data.get('guest_phone'):
            raise serializers.ValidationError({"guest_phone": "Phone number is required"})

        # If user is not authenticated, validate guest information
        if not request or not request.user.is_authenticated:
            if not data.get('guest_name'):
                raise serializers.ValidationError({"guest_name": "Guest name is required for non-authenticated users"})
            if not data.get('guest_email'):
                raise serializers.ValidationError({"guest_email": "Guest email is required for non-authenticated users"})
        
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        
        # If user is authenticated, associate the booking with the user
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            
        return super().create(validated_data)

class BookingDetailSerializer(serializers.ModelSerializer):
    court = CourtSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'court', 'guest_name', 'guest_email', 'guest_phone',
            'whatsapp_number', 'booking_reference', 'start_time', 'end_time',
            'duration_hours', 'total_price', 'status', 'status_display',
            'admin_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['booking_reference', 'created_at', 'updated_at']

class BookingStatsSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_bookings = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    court_type = serializers.CharField() 