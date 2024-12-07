from django.contrib import admin
from courts.models import Court, Booking, UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_phone', 'get_whatsapp', 'loyalty_points')
    search_fields = ('user__email', 'user__phone_number')
    
    def get_phone(self, obj):
        return obj.user.phone_number
    get_phone.short_description = 'Phone Number'
    
    def get_whatsapp(self, obj):
        return obj.user.whatsapp_number
    get_whatsapp.short_description = 'WhatsApp Number'

@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('name', 'court_type', 'hourly_rate', 'is_active')
    list_filter = ('court_type', 'is_active')
    search_fields = ('name',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'guest_name', 'court', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'court', 'start_time')
    search_fields = ('booking_reference', 'guest_name', 'guest_email')
    readonly_fields = ('booking_reference', 'created_at', 'updated_at')