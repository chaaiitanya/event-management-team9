from django.shortcuts import render, redirect
from apps.users.forms import LoginForm,  RegistrationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required



@login_required
def home(request):
    return redirect('main:dashboard')

def login_user(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        email = request.POST.get('email', None)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(email=email, password=password)
            if user:
                login(request, user)
                messages.success(request, f"Welcome back, {user.name}.")
                return redirect('main:dashboard')
            else:
                messages.error(request, "An error occurred. Kindly try again with correct credentials, reset password if you have forgotten or contact us.")
    return render(request, 'login.html', {
        'form': form,
    })

def signup_user(request):
    form = RegistrationForm(initial={'is_tutor': 'is_tutor'})
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user.is_client = True
            user.save()
            account = authenticate(email=email, password=raw_password)
            messages.success(request, f"Welcome {account.name}. You have successfully logged in.")
            login(request, account)
            if request.GET.get('next'):
                return redirect(next)
            return redirect('main:dashboard')
        else:
            messages.error(request, "Error creating account. Please correct the highlighted errors")
    return render(request, "register.html", {
        'form': form,
    })

@login_required
def logout_user(request):
    next_ = request.GET.get('next', '/')
    if request.user.is_authenticated:
        username = request.user.name
        logout(request)
    return redirect(next_)