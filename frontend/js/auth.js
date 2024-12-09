const AUTH_TOKEN_KEY = 'authToken';

function isLoggedIn() {
    return !!localStorage.getItem(AUTH_TOKEN_KEY);
}

function getAuthToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function logout() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem('user');
    window.location.href = '/index.html';
}

function updateAuthButtons() {
    const authButtonsContainer = document.getElementById('authButtons');
    
    if (isLoggedIn()) {
        // User is logged in - show profile dropdown
        authButtonsContainer.innerHTML = `
            <div class="dropdown">
                <button class="custom-btn btn dropdown-toggle" type="button" id="userDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                    My Account
                </button>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
                    <li><a class="dropdown-item" href="/my-bookings.html">My Bookings</a></li>
                    <li><a class="dropdown-item" href="/profile.html">Profile</a></li>
                    <li><hr class="dropdown-divider"></li>
                    <li><a class="dropdown-item" href="#" onclick="logout()">Logout</a></li>
                </ul>
            </div>
        `;
    } else {
        // User is not logged in - show login/register buttons
        authButtonsContainer.innerHTML = `
            <div class="d-flex gap-2">
                <a href="/login.html" class="custom-btn btn">
                    Login
                </a>
                <a href="/register.html" class="custom-btn btn" style="background: rgb(204, 228, 75);">
                    Register
                </a>
            </div>
        `;
    }
}

// Initialize auth buttons when the page loads
document.addEventListener('DOMContentLoaded', function() {
    updateAuthButtons();
}); 