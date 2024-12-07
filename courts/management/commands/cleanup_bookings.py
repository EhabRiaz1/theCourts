from django.core.management.base import BaseCommand
from courts.models import Booking

class Command(BaseCommand):
    help = 'Cleanup bookings with empty references'

    def handle(self, *args, **options):
        empty_refs = Booking.objects.filter(booking_reference='')
        count = empty_refs.count()
        if count > 0:
            empty_refs.delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {count} bookings with empty references'))
        else:
            self.stdout.write(self.style.SUCCESS('No bookings with empty references found')) 