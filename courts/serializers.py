from rest_framework import serializers
from .models import Court, Booking, UserProfile
from django.contrib.auth.models import User

class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ['id', 'name', 'court_type', 'hourly_rate', 'half_hour_rate', 'is_active']

class BookingSerializer(serializers.ModelSerializer):
    sport_type = serializers.CharField(write_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'court', 'user', 'guest_name', 'guest_email', 'guest_phone',
            'whatsapp_number', 'booking_reference', 'start_time', 'end_time',
            'duration_hours', 'total_price', 'status', 'sport_type'
        ]
        read_only_fields = ['booking_reference', 'status']
        extra_kwargs = {
            'guest_name': {'required': False},
            'guest_email': {'required': False},
            'guest_phone': {'required': False},
            'whatsapp_number': {'required': False},
            'court': {'required': False},
            'user': {'required': False},
            'end_time': {'required': False},
            'total_price': {'required': False}
        }

    def validate(self, data):
        request = self.context.get('request')
        
        if 'end_time' in data and data.get('start_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError({
                    "end_time": "End time must be after start time"
                })

        if request and request.user.is_authenticated:
            if not data.get('guest_name'):
                data['guest_name'] = request.user.get_full_name() or request.user.email
            if not data.get('guest_email'):
                data['guest_email'] = request.user.email
            if not data.get('guest_phone'):
                try:
                    profile = request.user.userprofile
                    data['guest_phone'] = getattr(profile, 'phone', '')
                except:
                    pass
        else:
            required_fields = ['guest_name', 'guest_email', 'guest_phone']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError({
                        field: "This field is required for guest bookings."
                    })

        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['phone', 'whatsapp_number', 'loyalty_points', 'referral_code']