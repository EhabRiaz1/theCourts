from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from courts.models import Court, Booking
from api.serializers.court_serializers import CourtSerializer, CourtDetailSerializer
from api.services.court_service import CourtService
from datetime import datetime

class CourtViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = Court.objects.filter(is_active=True)
    serializer_class = CourtSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourtDetailSerializer
        return CourtSerializer

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def check_availability(self, request):
        """Real-time availability checking endpoint"""
        try:
            date_str = request.query_params.get('date')
            start_time_str = request.query_params.get('start_time')
            duration_hours = float(request.query_params.get('duration', 1))
            sport_type = request.query_params.get('sport_type')

            if not all([date_str, start_time_str, sport_type]):
                return Response(
                    {"error": "Missing required parameters"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Combine date and time
            start_time = datetime.strptime(f"{date_str} {start_time_str}", '%Y-%m-%d %H:%M')
            end_time = start_time + timedelta(hours=duration_hours)

            # Use CourtService to validate and check availability
            try:
                CourtService.validate_booking_time(start_time, end_time)
                available_courts = CourtService.get_available_courts(sport_type, start_time, end_time)
                
                return Response({
                    'available': len(available_courts) > 0,
                    'courts': CourtSerializer(available_courts, many=True).data
                })
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError:
            return Response(
                {"error": "Invalid date/time format"},
                status=status.HTTP_400_BAD_REQUEST
            ) 