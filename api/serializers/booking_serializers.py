from rest_framework import serializers
from courts.models import Booking, Court
from .court_serializers import CourtSerializer

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'id', 'court', 'guest_name', 'guest_email', 'guest_phone',
            'whatsapp_number', 'booking_reference', 'start_time', 'end_time',
            'duration_hours', 'total_price', 'status', 'created_at'
        ]
        read_only_fields = ['created_at']

    def create(self, validated_data):
        if not validated_data.get('booking_reference'):
            raise serializers.ValidationError({"booking_reference": "Booking reference is required"})
        if not validated_data.get('total_price'):
            raise serializers.ValidationError({"total_price": "Total price is required"})
        return super().create(validated_data)

    def validate(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        if end_time and start_time and end_time <= start_time:
            raise serializers.ValidationError("End time must be after start time")
        return data

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