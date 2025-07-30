import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lostandfound_project.settings')
django.setup()

from playground.views import detect_faces, find_matching_faces
from playground.models import LostPerson, FoundPerson

def test_face_matching():
    # Test with identical images
    lost_path = os.path.join('media', 'lost_persons', 'Steve.jpg')
    found_path = os.path.join('media', 'found_persons', 'Steve.jpg')

    print("Testing with identical images (Steve.jpg)...")
    print(f"Lost person image: {lost_path}")
    print(f"Found person image: {found_path}")

    # Get face encodings
    print("\nGetting face encodings...")
    has_face_lost, encoding_lost = detect_faces(lost_path)
    has_face_found, encoding_found = detect_faces(found_path)

    if has_face_lost and has_face_found:
        print("Successfully detected faces in both images")
        print("\nTesting face matching...")
        matches = find_matching_faces(encoding_found)
        print(f"Found {len(matches)} potential matches")
        for person, confidence in matches:
            print(f"Match found with confidence: {confidence:.1f}%")
    else:
        print("Could not detect faces in one or both images")
        if not has_face_lost:
            print("- Failed to detect face in lost person image")
        if not has_face_found:
            print("- Failed to detect face in found person image")

    # Test with different images
    print("\nTesting with different images...")
    other_lost_path = os.path.join('media', 'lost_persons', 'njugush.jpg')
    print(f"Comparing {found_path} with {other_lost_path}")
    
    has_face_other, encoding_other = detect_faces(other_lost_path)
    if has_face_other and has_face_found:
        matches = find_matching_faces(encoding_found, threshold=0.6)  # Using our new threshold
        print(f"Found {len(matches)} potential matches")
        for person, confidence in matches:
            print(f"Match found with confidence: {confidence:.1f}%")
    else:
        print("Could not detect faces in one or both images")

if __name__ == '__main__':
    test_face_matching()
