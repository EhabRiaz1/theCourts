let selectedSport = null;
let selectedDate = null;
let selectedTime = null;
let duration = 2;
let currentPage = 'sportSelection';

// Add this function at the top of your file to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const PAGES = {
    sportSelection: { next: 'dateSelection', progress: 20 },
    dateSelection: { next: 'timeSelection', prev: 'sportSelection', progress: 40 },
    timeSelection: { next: 'userDetails', prev: 'dateSelection', progress: 60 },
    userDetails: { next: 'confirmation', prev: 'timeSelection', progress: 80 },
    confirmation: { prev: 'userDetails', progress: 100 }
};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize flatpickr with specific options
    flatpickr("#datePicker", {
        enableTime: false,
        dateFormat: "Y-m-d",
        minDate: "today",
        maxDate: new Date().fp_incr(30),
        altInput: true,
        altFormat: "F j, Y",
        onChange: function(selectedDates) {
            if (selectedDates.length > 0) {
                selectedDate = selectedDates[0];
                document.getElementById('dateNextBtn').disabled = false;
                updateBookingSummary();
            }
        }
    });

    // Hide all pages except the first one
    document.querySelectorAll('.booking-page').forEach(page => {
        page.style.display = 'none';
    });
    document.getElementById('sportSelection').style.display = 'block';

    // Initialize sport selection buttons
    document.querySelectorAll('.sport-card').forEach(card => {
        card.addEventListener('click', function() {
            selectSport(this.dataset.sport, this);
        });
    });

    // Initialize duration controls
    const decreaseBtn = document.getElementById('decreaseDuration');
    const increaseBtn = document.getElementById('increaseDuration');
    
    if (decreaseBtn && increaseBtn) {
        decreaseBtn.addEventListener('click', () => adjustDuration(-0.5));
        increaseBtn.addEventListener('click', () => adjustDuration(0.5));
        
        // Set initial duration state
        duration = 1; // Start with 1 hour instead of 2
        document.getElementById('durationDisplay').textContent = '1 hour';
        document.getElementById('duration').value = '1';
        
        // Set initial button states
        decreaseBtn.disabled = duration <= MIN_DURATION;
        increaseBtn.disabled = duration >= MAX_DURATION;
    }
});

function selectSport(sport, element) {
    selectedSport = sport;
    
    // Update visual selection
    document.querySelectorAll('.sport-card').forEach(card => {
        card.classList.remove('selected');
    });
    element.classList.add('selected');
    
    // Enable continue button
    document.getElementById('sportNextBtn').disabled = false;
    
    // Update booking summary
    updateBookingSummary();
}

function nextPage() {
    if (!validateCurrentPage()) return;

    const nextPageId = PAGES[currentPage].next;
    if (!nextPageId) return;

    // Hide current page
    document.getElementById(currentPage).style.display = 'none';
    
    // Show next page
    document.getElementById(nextPageId).style.display = 'block';
    
    // Update progress bar
    document.getElementById('bookingProgress').style.width = `${PAGES[nextPageId].progress}%`;
    
    // Update current page
    currentPage = nextPageId;

    // Special handling for time slots page
    if (currentPage === 'timeSelection') {
        fetchAvailableTimeSlots();
    }
}

function previousPage() {
    const prevPageId = PAGES[currentPage].prev;
    if (!prevPageId) return;

    // Hide current page
    document.getElementById(currentPage).style.display = 'none';
    
    // Show previous page
    document.getElementById(prevPageId).style.display = 'block';
    
    // Update progress bar
    document.getElementById('bookingProgress').style.width = `${PAGES[prevPageId].progress}%`;
    
    // Update current page
    currentPage = prevPageId;
}

function validateCurrentPage() {
    switch(currentPage) {
        case 'sportSelection':
            if (!selectedSport) {
                showError('Please select a sport');
                return false;
            }
            return true;
            
        case 'dateSelection':
            if (!selectedDate) {
                showError('Please select a date');
                return false;
            }
            return true;
            
        case 'timeSelection':
            if (!selectedTime) {
                showError('Please select a time slot');
                return false;
            }
            return true;
            
        default:
            return true;
    }
}

function fetchAvailableTimeSlots() {
    const dateStr = selectedDate.toISOString().split('T')[0];
    const url = `/api/courts/available_slots/?date=${dateStr}&sport_type=${selectedSport}&duration=${duration}`;
    
    fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        const timeSlotsContainer = document.getElementById('timeSlots');
        timeSlotsContainer.innerHTML = '';

        if (data.available_slots && data.available_slots.length > 0) {
            const slotsGrid = document.createElement('div');
            slotsGrid.className = 'time-slots-grid';

            // Filter out invalid slots based on duration
            const validSlots = data.available_slots.filter(slot => {
                const startTime = new Date(slot.start_time);
                const endTime = new Date(startTime.getTime() + (duration * 60 * 60 * 1000));
                
                const startHour = startTime.getHours();
                const endHour = endTime.getHours();
                
                // Don't show slots that:
                // 1. Start in closed hours (3 AM - 6 AM)
                // 2. End in closed hours (3 AM - 6 AM)
                // 3. Cross into closed hours
                // 4. Are 7-hour slots after 8 PM
                if (endHour >= 3 && endHour < 6 || // End during closed hours
                    startHour >= 3 && startHour < 6 || // Start during closed hours
                    (startHour < 3 && endHour >= 3) || // Cross into closed hours
                    (duration === 7 && startHour >= 20)) { // 7-hour restriction
                    return false;
                }
                
                return true;
            });

            if (validSlots.length === 0) {
                timeSlotsContainer.innerHTML = `
                    <div class="alert alert-info">
                        No available ${duration}-hour slots for this date. 
                        Please try a different date or adjust the duration.
                    </div>`;
                return;
            }

            validSlots.forEach(slot => {
                const time = new Date(slot.start_time);
                const button = document.createElement('button');
                button.className = 'time-slot';
                button.textContent = time.toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    hour12: true 
                });
                button.onclick = () => selectTimeSlot(slot);
                slotsGrid.appendChild(button);
            });

            timeSlotsContainer.appendChild(slotsGrid);
        } else {
            timeSlotsContainer.innerHTML = `
                <div class="alert alert-info text-center">
                    No available slots for this date
                </div>`;
        }
    })
    .catch(error => {
        console.error('Error fetching time slots:', error);
        const timeSlotsContainer = document.getElementById('timeSlots');
        timeSlotsContainer.innerHTML = `
            <div class="alert alert-danger">
                Failed to load available time slots. Please try again.
            </div>`;
    });
}

function selectTimeSlot(slot) {
    selectedTime = slot;
    
    // Update visual selection
    document.querySelectorAll('.time-slot').forEach(btn => {
        btn.classList.remove('selected');
    });
    event.target.classList.add('selected');
    
    // Enable continue button
    document.getElementById('timeNextBtn').disabled = false;
    
    updateBookingSummary();
}

function updateBookingSummary() {
    const summary = document.getElementById('bookingSummary');
    if (!summary) return;

    let html = '';
    
    // Sport (1st)
    html += `
        <div class="summary-item">
            <h5 class="booking-summary-heading" style="color: #000000 !important;">Sport</h5>
            <p class="booking-summary-value" style="color: #000000 !important;">
                ${selectedSport === 'PICKLE' ? 'Pickle Ball' : 'Paddle Ball'}
            </p>
        </div>
    `;
    
    // Date (2nd)
    html += `
        <div class="summary-item">
            <h5 class="summary-heading" style="color: #000000 !important;">Date</h5>
            <p style="color: #000000 !important;">${selectedDate ? selectedDate.toLocaleDateString('en-US', { 
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            }) : '-'}</p>
        </div>
    `;

    // Duration (3rd)
    html += `
        <div class="summary-item">
            <h5 class="summary-heading" style="color: #000000 !important;">Duration</h5>
            <p style="color: #000000 !important;">${duration} ${duration === 1 ? 'hour' : 'hours'}</p>
        </div>
    `;
    
    // Time (4th)
    html += `
        <div class="summary-item">
            <h5 class="summary-heading" style="color: #000000 !important;">Time</h5>
            <p style="color: #000000 !important;">${selectedTime ? new Date(selectedTime.start_time).toLocaleTimeString([], { 
                hour: '2-digit',
                minute: '2-digit'
            }) : '-'}</p>
        </div>
    `;

    // Total Price (5th)
    const basePrice = selectedSport === 'PICKLE' ? 6000 : 8000;
    const totalPrice = basePrice * duration;
    html += `
        <div class="summary-item total">
            <h5 class="summary-heading" style="color: #000000 !important;">Total Price</h5>
            <p style="color: #000000 !important;">PKR ${totalPrice.toLocaleString()}</p>
        </div>
    `;

    summary.innerHTML = html;
}

function showError(message) {
    const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
    document.getElementById('errorMessage').textContent = message;
    errorModal.show();
}

// Add this function to handle booking submission
function submitBooking() {
    console.log("Starting submitBooking...");
    
    const csrfToken = getCookie('csrftoken');
    console.log("CSRF Token:", csrfToken ? "Present" : "Missing");
    
    if (!csrfToken) {
        console.error("CSRF token not found!");
        showError("Security token missing. Please refresh the page.");
        return;
    }

    // Validate booking data first
    if (!validateBookingData()) {
        return;
    }

    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Processing...';
    }

    const isAuthenticated = document.body.classList.contains('user-authenticated');
    console.log("User authenticated:", isAuthenticated);
    
    // Calculate end time
    const startTime = new Date(selectedTime.start_time);
    const endTime = new Date(startTime.getTime() + (duration * 60 * 60 * 1000));
    
    // Calculate total price
    const basePrice = selectedSport === 'PICKLE' ? 6000 : 8000;
    const totalPrice = basePrice * duration;

    let bookingData = {
        court: selectedSport === 'PICKLE' ? 1 : 2,
        start_time: selectedTime.start_time,
        end_time: endTime.toISOString(),
        duration_hours: duration,
        total_price: totalPrice,
        status: 'PENDING'
    };

    if (isAuthenticated) {
        // For authenticated users, only send phone numbers
        const phoneNumber = document.getElementById('phoneNumber')?.value;
        const whatsappNumber = document.getElementById('whatsappNumber')?.value;
        
        if (!phoneNumber) {
            showError('Please enter your phone number');
            return;
        }

        Object.assign(bookingData, {
            guest_phone: phoneNumber,
            whatsapp_number: whatsappNumber || phoneNumber
        });
    } else {
        // Guest user logic remains the same
        const guestName = document.getElementById('guestName')?.value;
        const guestEmail = document.getElementById('guestEmail')?.value;
        const phoneNumber = document.getElementById('phoneNumber')?.value;
        const whatsappNumber = document.getElementById('guestWhatsapp')?.value;

        if (!guestName || !guestEmail || !phoneNumber) {
            showError('Please fill in all required fields');
            return;
        }

        Object.assign(bookingData, {
            guest_name: guestName,
            guest_email: guestEmail,
            guest_phone: phoneNumber,
            whatsapp_number: whatsappNumber || phoneNumber
        });
    }

    console.log("Final booking data:", bookingData);

    fetch('/api/bookings/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(bookingData),
        credentials: 'include'
    })
    .then(async response => {
        const data = await response.json();
        console.log('Server response:', {
            status: response.status,
            statusText: response.statusText,
            data: data
        });
        
        if (!response.ok) {
            throw new Error(data.detail || data.error || JSON.stringify(data));
        }
        return data;
    })
    .then(data => {
        document.getElementById('userDetails').style.display = 'none';
        document.getElementById('confirmation').style.display = 'block';
        document.getElementById('bookingReference').textContent = data.booking_reference;
        updateConfirmationSummary(data);
        document.getElementById('bookingProgress').style.width = '100%';
    })
    .catch(error => {
        console.error('Full error details:', {
            message: error.message,
            error: error
        });
        showError(error.message || 'An error occurred while creating the booking');
    })
    .finally(() => {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Confirm Booking';
        }
    });
}

function validateBookingData() {
    if (!selectedSport || !selectedDate || !selectedTime) {
        showError('Please complete all booking details');
        return false;
    } 
    // If user is authenticated, skip guest form validation
    if (document.body.classList.contains('user-authenticated')) {
        return true;
    } 

    // Only validate guest form fields if user is not authenticated
    const guestName = document.getElementById('guestName');
    const guestEmail = document.getElementById('guestEmail');
    const guestPhone = document.getElementById('phoneNumber');

        // Check if elements exist and have values
    if (!guestName || !guestName.value.trim()) {
            showError('Please enter your full name');
            return false;
    }

    if (!guestEmail || !guestEmail.value.trim()) {
            showError('Please enter your email address');
            return false;
     }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(guestEmail.value)) {
        showError('Please enter a valid email address');
        return false;
    }

    if (!guestPhone || !guestPhone.value.trim()) {
            showError('Please enter your phone number');
            return false;
    }

    // Validate phone number (basic validation)
    const phoneRegex = /^\d{10,}$/;
    if (!phoneRegex.test(guestPhone.value.replace(/\D/g, ''))) {
        showError('Please enter a valid phone number');
        return false;
    }

    return true;
    }

function updateConfirmationSummary(bookingData) {
    const summary = document.getElementById('confirmationSummary');
    if (!summary) return;

    const sportName = selectedSport === 'PICKLE' ? 'Pickle Ball' : 'Paddle Ball';
    const basePrice = selectedSport === 'PICKLE' ? 6000 : 8000;
    const totalPrice = basePrice * duration;

    summary.innerHTML = `
        <div class="mb-3">
            <h6>Sport</h6>
            <p class="mb-1">${sportName}</p>
        </div>
        <div class="mb-3">
            <h6>Date & Time</h6>
            <p class="mb-1">${new Date(selectedTime.start_time).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            })}</p>
            <p class="mb-1">${new Date(selectedTime.start_time).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
            })}</p>
        </div>
        <div class="mb-3">
            <h6>Duration</h6>
            <p class="mb-1">${duration} ${duration === 1 ? 'hour' : 'hours'}</p>
        </div>
        <div class="mb-3">
            <h6>Total Price</h6>
            <p class="fs-4 fw-bold mb-0">PKR ${totalPrice.toLocaleString()}</p>
        </div>
    `;
}

const MIN_DURATION = 1;
const MAX_DURATION = 7;
const DURATION_STEP = 0.5;

function adjustDuration(change) {
    console.log('Adjusting duration by:', change); // Debug log
    let newDuration = duration + change;
    
    if (newDuration >= MIN_DURATION && newDuration <= MAX_DURATION) {
        duration = newDuration;
        
        // Update display and hidden input
        const durationDisplay = document.getElementById('durationDisplay');
        const durationInput = document.getElementById('duration');
        
        if (durationDisplay && durationInput) {
            durationDisplay.textContent = `${newDuration} hour${newDuration !== 1 ? 's' : ''}`;
            durationInput.value = newDuration;
            
            // Update button states
            document.getElementById('decreaseDuration').disabled = newDuration <= MIN_DURATION;
            document.getElementById('increaseDuration').disabled = newDuration >= MAX_DURATION;
            
            // Update booking summary if on the appropriate page
            if (currentPage === 'dateSelection' || currentPage === 'timeSelection') {
                updateBookingSummary();
            }
            
            // If on time selection page, refresh available slots
            if (currentPage === 'timeSelection' && selectedDate) {
                fetchAvailableTimeSlots();
            }
        }
    }
}

function setupWhatsAppButton() {
    const button = document.getElementById('whatsappButton');
    if (button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const bookingRef = document.getElementById('bookingReference').textContent;
            const userName = document.getElementById('userName')?.value || 
                           document.getElementById('guestName')?.value || 
                           'Customer';
            
            const message = `Hi, I have recently made a booking. My name is ${userName} and my reference number is ${bookingRef}. I would like to share my payment receipt.`;
            
            const whatsappUrl = `https://wa.me/923334965444?text=${encodeURIComponent(message)}`;
            window.open(whatsappUrl, '_blank');
        });
    }
}

function showConfirmationPage(bookingData) {
    // ... existing confirmation code ...
    
    // Setup WhatsApp button
    setupWhatsAppButton();
}

function sendWhatsAppMessage() {
    // Get the booking reference from the confirmation page
    const bookingRef = document.getElementById('bookingReference').textContent;
    
    // Get the selected sport, date, time, and duration from the booking summary
    const sportElement = document.querySelector('#confirmationSummary [data-summary="sport"]');
    const dateElement = document.querySelector('#confirmationSummary [data-summary="date"]');
    const timeElement = document.querySelector('#confirmationSummary [data-summary="time"]');
    const durationElement = document.querySelector('#confirmationSummary [data-summary="duration"]');
    const totalElement = document.querySelector('#confirmationSummary [data-summary="total"]');
    
    // Construct the message
    const message = `Hello! I would like to confirm my booking:\n\n` +
        `Booking Reference: ${bookingRef}\n` +
        `Sport: ${sportElement ? sportElement.textContent : ''}\n` +
        `Date: ${dateElement ? dateElement.textContent : ''}\n` +
        `Time: ${timeElement ? timeElement.textContent : ''}\n` +
        `Duration: ${durationElement ? durationElement.textContent : ''}\n` +
        `Total Amount: ${totalElement ? totalElement.textContent : ''}\n\n` +
        `Please find attached the payment receipt.`;

    // Encode the message for URL
    const encodedMessage = encodeURIComponent(message);
    
    // Replace this with your actual WhatsApp business number
    const phoneNumber = '923XXXXXXXXX';  // Format: country code + number without '+'
    
    // Construct the WhatsApp URL
    const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodedMessage}`;
    
    // Open WhatsApp in a new tab
    window.open(whatsappUrl, '_blank');
}