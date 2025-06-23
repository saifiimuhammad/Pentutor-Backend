from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import EmailVerificationToken, PasswordResetToken

def send_verification_email(user):
    # Delete existing tokens
    EmailVerificationToken.objects.filter(user=user).delete()
    
    # Create new token
    token = EmailVerificationToken.objects.create(user=user)
    
    subject = 'Verify Your Email Address'
    message = f'''
    Hi {user.first_name},
    
    Please click the link below to verify your email address:
    
    http://localhost:3000/verify-email/{token.token}
    
    This link will expire in 24 hours.
    
    Best regards,
    Your App Team
    '''
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def send_password_reset_email(user):
    # Delete existing tokens
    PasswordResetToken.objects.filter(user=user, is_used=False).delete()
    
    # Create new token
    token = PasswordResetToken.objects.create(user=user)
    
    subject = 'Password Reset Request'
    message = f'''
    Hi {user.first_name},
    
    You requested a password reset. Click the link below to reset your password:
    
    http://localhost:3000/reset-password/{token.token}
    
    This link will expire in 1 hour.
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    Your App Team
    '''
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )