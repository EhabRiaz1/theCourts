from rest_framework import serializers
from courts.models import Court

class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ['id', 'name', 'court_type', 'hourly_rate', 'half_hour_rate', 'is_active']

class CourtDetailSerializer(serializers.ModelSerializer):
    court_type_display = serializers.CharField(source='get_court_type_display', read_only=True)
    
    class Meta:
        model = Court
        fields = [
            'id', 'name', 'court_type', 'court_type_display',
            'hourly_rate', 'half_hour_rate', 'is_active'
        ] 