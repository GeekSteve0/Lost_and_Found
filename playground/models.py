from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

class BasePerson(models.Model):
    """Base model for both lost and found persons"""
    full_name = models.CharField(max_length=255, blank=True, null=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ], blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    date_reported = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    police_station = models.CharField(max_length=255, blank=True, null=True)
    ob_number = models.CharField(max_length=50, blank=True, null=True)
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    face_encoding = models.BinaryField(null=True, blank=True)  # To store face recognition data

    class Meta:
        abstract = True

class LostPerson(BasePerson):
    date_last_seen = models.DateTimeField()
    last_seen_location = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='lost_persons/')
    
    def __str__(self):
        return f"Lost: {self.full_name}"

class FoundPerson(BasePerson):
    date_found = models.DateTimeField(auto_now_add=True)
    found_location = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='found_persons/')
    has_disability = models.BooleanField(default=False)
    disability_details = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Found: {self.full_name or 'Unknown Person'}"
    
    class Meta:
        ordering = ['-date_found']  # Show newest first

class Match(models.Model):
    """Records matches between lost and found persons"""
    lost_person = models.ForeignKey(LostPerson, on_delete=models.CASCADE)
    found_person = models.ForeignKey(FoundPerson, on_delete=models.CASCADE)
    match_percentage = models.FloatField()  # Store face recognition confidence
    date_matched = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Match: {self.lost_person.full_name} - {self.found_person.full_name}"

    @property
    def is_confirmed(self):
        """Auto-confirm if match percentage is above 70%"""
        return self.match_percentage >= 70.0

    class Meta:
        verbose_name_plural = "Matches"
