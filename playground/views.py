from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, EmailAuthenticationForm
from django.contrib import messages

# Home page

def index(request):
    return render(request, 'playground/index.html')

# Authentication

def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('lost_persons_logged_in')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = EmailAuthenticationForm()
    return render(request, 'playground/Login.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('lost_persons_logged_in')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    return render(request, 'playground/Sign_up.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

# Lost and found person pages

@login_required
def lost_persons_logged_in(request):
    return render(request, 'playground/lost_persons_logged_in.html')

@login_required
def found_persons_logged_in(request):
    return render(request, 'playground/found_persons_logged_in.html')

def lost_person_logged_out(request):
    return render(request, 'playground/lost_person_logged_out.html')

def found_persons_logged_out(request):
    return render(request, 'playground/found_persons_logged_out.html')

def lost_person_profile(request):
    return render(request, 'playground/lost_person_profile.html')

def found_person_profile(request):
    return render(request, 'playground/found_person_profile.html')

# Image upload/report pages

@login_required
def report_lost_person(request):
    return render(request, 'playground/report_lost_person.html')

@login_required
def report_found_person(request):
    return render(request, 'playground/report_found_person.html')

@login_required
def lost_person_image_upload(request):
    return render(request, 'playground/lost_person_image_upload.html')

@login_required
def found_person_image_upload(request):
    return render(request, 'playground/found_person_image_upload.html')

# User profile

@login_required
def user_profile(request):
    return render(request, 'playground/user_profile.html')
