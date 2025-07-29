from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('lost/logged-in/', views.lost_persons_logged_in, name='lost_persons_logged_in'),
    path('found/logged-in/', views.found_persons_logged_in, name='found_persons_logged_in'),
    path('lost/logged-out/', views.lost_person_logged_out, name='lost_person_logged_out'),
    path('found/logged-out/', views.found_persons_logged_out, name='found_persons_logged_out'),
    path('lost/profile/', views.lost_person_profile, name='lost_person_profile'),
    path('found/profile/', views.found_person_profile, name='found_person_profile'),
    path('report/lost/', views.report_lost_person, name='report_lost_person'),
    path('report/found/', views.report_found_person, name='report_found_person'),
    path('upload/lost/', views.lost_person_image_upload, name='lost_person_image_upload'),
    path('upload/found/', views.found_person_image_upload, name='found_person_image_upload'),
    path('user/profile/', views.user_profile, name='user_profile'),
    path('logout/', views.logout_view, name='logout'),
] 