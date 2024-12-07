let currentBookingId = null;

function filterBookings(courtType) {
    const cards = document.querySelectorAll('.booking-card');
    cards.forEach(card => {
        if (courtType === 'all' || card.dataset.courtType === courtType) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

function showNotesModal(bookingId) {
    currentBookingId = bookingId;
    const modal = new bootstrap.Modal(document.getElementById('notesModal'));
    modal.show();
}

function saveAdminNotes() {
    const notes = document.getElementById('adminNotes').value;
    updateBookingStatus(currentBookingId, null, notes);
}

function updateBookingStatus(bookingId, newStatus, notes = null) {
    const data = {};
    if (newStatus) data.status = newStatus;
    if (notes) data.admin_notes = notes;

    fetch(`/api/bookings/${bookingId}/update_status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(data),
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update booking status');
        }
        return response.json();
    })
    .then(data => {
        // Close modal if open
        const modal = bootstrap.Modal.getInstance(document.getElementById('notesModal'));
        if (modal) modal.hide();

        // Remove the booking card if status was updated
        if (newStatus) {
            const card = document.querySelector(`[data-booking-id="${bookingId}"]`);
            if (card) {
                card.remove();
                // Show "no bookings" message if no cards left
                const remainingCards = document.querySelectorAll('.booking-card');
                if (remainingCards.length === 0) {
                    document.querySelector('.booking-cards').innerHTML = 
                        '<div class="alert alert-info">No pending bookings found.</div>';
                }
            }
        }

        // Show success message
        showAlert('success', 'Booking updated successfully');
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Failed to update booking');
    });
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.booking-cards').parentElement;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto dismiss after 3 seconds
    setTimeout(() => {
        const alert = bootstrap.Alert.getInstance(alertDiv);
        if (alert) {
            alert.close();
        }
    }, 3000);
} 