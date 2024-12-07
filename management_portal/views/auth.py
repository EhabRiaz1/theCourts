from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.contrib.auth.forms import AuthenticationForm

class LoginView(View):
    template_name = 'management_portal/auth/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect('management:dashboard')
            logout(request)
            messages.error(request, "You don't have permission to access the management portal.")
        return render(request, self.template_name, {'form': AuthenticationForm()})
    
    def post(self, request):
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                return redirect('management:dashboard')
            messages.error(request, "You don't have permission to access the management portal.")
        return render(request, self.template_name, {'form': form})

@method_decorator(login_required, name='dispatch')
class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('management:login') 