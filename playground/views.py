from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, EmailAuthenticationForm
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import sys
import site
# Add user site-packages to path
user_site_packages = site.getusersitepackages()
if user_site_packages not in sys.path:
    sys.path.append(user_site_packages)

import face_recognition
import numpy as np
from .models import LostPerson, FoundPerson, Match
import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models import Q

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
            # Get next URL from POST data since form submission might lose GET parameters
            next_url = request.POST.get('next', request.GET.get('next', ''))
            if next_url and next_url.startswith('/'):  # Security check
                return redirect(next_url)
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
    lost_persons = LostPerson.objects.all().order_by('-date_reported')  # Most recent first
    return render(request, 'playground/lost_persons_logged_in.html', {'lost_persons': lost_persons})

@login_required
def found_persons_logged_in(request):
    found_persons = FoundPerson.objects.all().order_by('-date_reported')  # Most recent first
    return render(request, 'playground/found_persons_logged_in.html', {'found_persons': found_persons})

def lost_person_logged_out(request):
    lost_persons = LostPerson.objects.all().order_by('-date_reported')  # Most recent first
    return render(request, 'playground/lost_person_logged_out.html', {'lost_persons': lost_persons})

def found_persons_logged_out(request):
    found_persons = FoundPerson.objects.all().order_by('-date_reported')  # Most recent first
    return render(request, 'playground/found_persons_logged_out.html', {'found_persons': found_persons})

def lost_person_profile(request):
    return render(request, 'playground/lost_person_profile.html')

def found_person_profile(request, person_id=None):
    if person_id:
        found_person = get_object_or_404(FoundPerson, id=person_id)
        # Get the match if this person was previously reported as lost
        match = Match.objects.filter(found_person=found_person, match_percentage__gte=70.0).first()
        return render(request, 'playground/found_person_profile.html', {
            'person': found_person,
            'match': match
        })
    return redirect('found_persons_logged_out')

# Image upload/report pages

def validate_image(image):
    if image.size > 5 * 1024 * 1024:  # 5MB limit
        raise ValidationError('Image file size must be less than 5MB.')
    
    ext_validator = FileExtensionValidator(['jpg', 'jpeg', 'png'])
    try:
        ext_validator(image)
    except ValidationError:
        raise ValidationError('Only JPG and PNG files are allowed.')

def detect_faces(image_path):
    try:
        # Load the image
        image = face_recognition.load_image_file(image_path)
        # Detect faces
        face_locations = face_recognition.face_locations(image)
        if not face_locations:
            return False, None
        # Get face encodings
        face_encodings = face_recognition.face_encodings(image, face_locations)
        if not face_encodings:
            return False, None
        return True, face_encodings[0]  # Return the first face encoding
    except Exception as e:
        print(f"Error detecting faces: {e}")
        return False, None

def find_matching_faces(encoding, threshold=0.7):
    # Search for matches among unresolved lost persons
    lost_persons = LostPerson.objects.filter(is_resolved=False)
    matches = []
    
    for person in lost_persons:
        try:
            if person.face_encoding:
                # Convert stored encoding from bytes back to numpy array
                face_encoding_bytes = person.face_encoding
                if isinstance(face_encoding_bytes, str):
                    # Handle old string format
                    stored_encoding = np.fromstring(face_encoding_bytes[1:-1], sep=' ')
                else:
                    # Handle new bytes format
                    stored_encoding = np.frombuffer(face_encoding_bytes, dtype=np.float64)
                
                # Calculate face distance
                face_distance = face_recognition.face_distance([stored_encoding], encoding)[0]
                if face_distance < threshold:  # Lower distance means better match
                    confidence = (1 - face_distance) * 100
                    matches.append((person, confidence))
        except Exception as e:
            print(f"Error comparing faces: {e}")
            continue
    
    return sorted(matches, key=lambda x: x[1], reverse=True)  # Sort by confidence

@login_required
def report_lost_person(request):
    if request.method == 'POST':
        try:
            print("Received POST request with data:", request.POST)
            print("Received FILES:", request.FILES)
            
            # Validate form data
            full_name = request.POST.get('fullName')
            last_seen = request.POST.get('lastSeenLocation')
            age = request.POST.get('age')
            gender = request.POST.get('gender')
            ob_number = request.POST.get('policeObNumber')
            disability = request.POST.get('disability')
            disability_details = request.POST.get('disabilityDetails')
            image = request.FILES.get('imageUpload')
            
            print("Extracted data:", {
                'full_name': full_name,
                'last_seen': last_seen,
                'age': age,
                'gender': gender,
                'ob_number': ob_number,
                'disability': disability,
                'disability_details': disability_details,
                'image': image
            })

            if not all([full_name, last_seen, age, gender, ob_number, image]):
                messages.error(request, 'Please fill all required fields.')
                return render(request, 'playground/report_lost_person.html')

            # Validate image
            validate_image(image)

            # Save image temporarily
            temp_path = default_storage.save(f'temp/{image.name}', ContentFile(image.read()))
            full_temp_path = os.path.join(settings.MEDIA_ROOT, temp_path)

            # Detect faces and get encoding
            has_face, face_encoding = detect_faces(full_temp_path)
            
            if not has_face:
                messages.error(request, 'No clear face detected in the image. Please upload a clearer photo.')
                os.remove(full_temp_path)
                return render(request, 'playground/report_lost_person.html')

            print("About to create LostPerson record")
            try:
                from django.utils import timezone
                
                # Create lost person record
                lost_person = LostPerson.objects.create(
                    reporter=request.user,
                    full_name=full_name,
                    last_seen_location=last_seen,
                    location=last_seen,  # Using last seen as general location
                    age=age,
                    gender='M' if gender == 'male' else 'F',  # Convert to model's format
                    ob_number=ob_number,
                    police_station='Not Provided',  # Default value
                    contact_phone='Not Provided',  # Default value
                    description=f"{'Has disability: ' + disability_details if disability == 'yes' else 'No disability'}",
                    date_last_seen=timezone.now(),  # Current time as default
                    photo=image,  # Changed from image to photo
                    face_encoding=face_encoding.tobytes() if face_encoding is not None else None
                )
                print("Successfully created LostPerson record:", lost_person.id)
            except Exception as db_error:
                print("Error creating LostPerson record:", str(db_error))
                raise

            # Search for matches
            potential_matches = find_matching_faces(face_encoding)
            
            # Create matches with high confidence
            for found_person, confidence in potential_matches:
                if confidence >= 70:  # Auto-confirm matches above 70% confidence
                    Match.objects.create(
                        lost_person=lost_person,
                        found_person=found_person,
                        confidence=confidence,
                        is_confirmed=True
                    )

            # Clean up temp file
            os.remove(full_temp_path)

            messages.success(request, 'Report submitted successfully.')
            return redirect('lost_persons_logged_in')

        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')

    return render(request, 'playground/report_lost_person.html')

@login_required
def report_found_person(request):
    if request.method == 'POST':
        temp_path = None
        try:
            # Get form data - only image is required
            image = request.FILES.get('imageUpload')
            
            if not image:
                messages.error(request, 'Please upload a photo of the found person.')
                return render(request, 'playground/report_found_person.html')

            # Validate image
            validate_image(image)
            
            # Save image temporarily
            temp_path = default_storage.save(f'temp/{image.name}', ContentFile(image.read()))
            full_temp_path = os.path.join(settings.MEDIA_ROOT, temp_path)

            # Detect faces and get encoding
            has_face, face_encoding = detect_faces(full_temp_path)
            
            if not has_face:
                messages.error(request, 'No clear face detected in the image. Please upload a clearer photo.')
                os.remove(full_temp_path)
                return render(request, 'playground/report_found_person.html')

            # Get optional form data
            full_name = request.POST.get('fullName', '')
            location = request.POST.get('location', '')
            age = request.POST.get('age', None)
            if age:
                try:
                    age = int(age)
                except ValueError:
                    age = None
            gender = request.POST.get('gender', '')
            ob_number = request.POST.get('policeObNumber', '')
            police_station = request.POST.get('policeStation', '')
            contact_phone = request.POST.get('contact', '')
            disability = request.POST.get('disability', 'no')
            disability_details = request.POST.get('disabilityDetails', '')
            description = request.POST.get('description', '')

            # Create found person record
            found_person = FoundPerson.objects.create(
                reporter=request.user,
                full_name=full_name if full_name else None,
                location=location if location else None,
                age=age,
                gender=gender if gender else None,
                ob_number=ob_number if ob_number else None,
                police_station=police_station if police_station else None,
                contact_phone=contact_phone if contact_phone else None,
                has_disability=disability == 'yes',
                disability_details=disability_details if disability == 'yes' else None,
                description=description if description else None,
                photo=image,
                face_encoding=face_encoding.tobytes() if face_encoding is not None else None
            )

            # Search for potential matches among lost persons
            if face_encoding is not None:
                potential_matches = find_matching_faces(face_encoding)
                high_confidence_matches = [(lost, conf) for lost, conf in potential_matches if conf >= 70]
                
                if high_confidence_matches:
                    # Get the best match
                    matched_lost_person, confidence = high_confidence_matches[0]
                    
                    # Create the match record
                    match = Match.objects.create(
                        lost_person=matched_lost_person,
                        found_person=found_person,
                        match_percentage=confidence
                    )
                    
                    # Update the lost person's status
                    matched_lost_person.is_resolved = True
                    matched_lost_person.save()
                    
                    # Clean up temp file
                    os.remove(full_temp_path)
                    
                    messages.success(request, 
                        f'Match found! This person was reported missing. Confidence: {confidence:.1f}%')
                    return redirect('found_person_profile', person_id=found_person.id)
            
            # If no matches found or no face encoding, just save as a new found person
            # Clean up temp file
            os.remove(full_temp_path)
            
            messages.success(request, 'Found person report submitted successfully.')
            return redirect('found_persons_logged_in')

        except ValidationError as e:
            if temp_path:
                full_temp_path = os.path.join(settings.MEDIA_ROOT, temp_path)
                if os.path.exists(full_temp_path):
                    os.remove(full_temp_path)
            messages.error(request, str(e))
            return render(request, 'playground/report_found_person.html')
        except Exception as e:
            if temp_path:
                full_temp_path = os.path.join(settings.MEDIA_ROOT, temp_path)
                if os.path.exists(full_temp_path):
                    os.remove(full_temp_path)
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'playground/report_found_person.html')

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