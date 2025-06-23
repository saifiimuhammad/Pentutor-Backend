from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # Email Verification
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    # Password Management
    path('change-password/', views.change_password, name='change_password'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # Social Authentication
    path('auth/google/', views.google_auth, name='google_auth'),
    path('auth/apple/', views.apple_auth, name='apple_auth'),
    
  
]