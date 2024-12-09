class BookingWebSocket {
    constructor(userId, token) {
        this.ws = new WebSocket(`ws://localhost:8000/ws/${userId}?token=${token}`);
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch(data.type) {
                case 'booking_status_update':
                    this.handleBookingStatusUpdate(data);
                    break;
                case 'new_booking':
                    this.handleNewBooking(data);
                    break;
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket connection closed');
            // Implement reconnection logic here
        };
    }

    handleBookingStatusUpdate(data) {
        // Update UI with new booking status
        const bookingElement = document.querySelector(`#booking-${data.booking_id}`);
        if (bookingElement) {
            bookingElement.querySelector('.status').textContent = data.status;
            // Add appropriate styling based on status
        }
    }

    handleNewBooking(data) {
        // Handle new booking notification (for admin interface)
        if (isAdmin) {
            // Add new booking to the list
            // Show notification
        }
    }
} 