from django.contrib import admin
from .models import UserProfile, LostPerson, FoundPerson, Match

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number']
    search_fields = ['user__username', 'user__email', 'phone_number']

@admin.register(LostPerson)
class LostPersonAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'age', 'gender', 'date_reported', 'is_resolved']
    list_filter = ['is_resolved', 'gender', 'date_reported']
    search_fields = ['full_name', 'description', 'location']

@admin.register(FoundPerson)
class FoundPersonAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'age', 'gender', 'date_reported', 'is_resolved']
    list_filter = ['is_resolved', 'gender', 'date_reported']
    search_fields = ['full_name', 'description', 'location']

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['lost_person', 'found_person', 'match_percentage', 'date_matched']
    list_filter = ['date_matched']
    search_fields = ['lost_person__full_name', 'found_person__full_name']
