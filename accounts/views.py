from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, UserUpdateForm, LoginForm
from courts.models import Booking
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView,
    PasswordResetConfirmView, 
    PasswordResetCompleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from .models import UserProfile  # Adjust import based on your user model
from django.db import models

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Registration successful!")
            return redirect("courts:home")
        messages.error(request, "Registration failed. Please correct the errors.")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'courts:home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('courts:home')

@login_required
def profile_view(request):
    # Get bookings where either the user is directly linked or the guest email matches
    bookings = Booking.objects.filter(
        models.Q(user=request.user) |  # Bookings linked to user
        models.Q(guest_email=request.user.email)  # Bookings made with user's email
    ).order_by('-created_at')
    
    context = {
        'bookings': bookings
    }
    return render(request, 'accounts/profile.html', context)

def password_reset_view(request):
    return CustomPasswordResetView.as_view()(request)

class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = '/accounts/password-reset/done/'

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = '/accounts/password-reset/complete/'

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'

class EditProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    template_name = 'accounts/edit_profile.html'
    fields = ['date_of_birth']  # Add other fields you want to make editable
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user.userprofile