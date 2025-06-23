from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from google.oauth2 import id_token
from google.auth.transport import requests
import json

from .models import CustomUser, EmailVerificationToken, PasswordResetToken
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    PasswordChangeSerializer, PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer
)
from .utils import send_verification_email, send_password_reset_email

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        send_verification_email(user)
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'User registered successfully. Please check your email for verification.',
            'user': UserProfileSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Login successful',
            'user': UserProfileSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data["refresh_token"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Profile updated successfully', 'user': serializer.data})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    token = request.data.get('token')
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
        if verification_token.is_expired():
            return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = verification_token.user
        user.is_email_verified = True
        user.save()
        verification_token.delete()
        
        return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)
    except EmailVerificationToken.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification(request):
    email = request.data.get('email')
    try:
        user = CustomUser.objects.get(email=email)
        if user.is_email_verified:
            return Response({'message': 'Email already verified'}, status=status.HTTP_200_OK)
        send_verification_email(user)
        return Response({'message': 'Verification email sent'}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = PasswordChangeSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            user = CustomUser.objects.get(email=email)
            send_password_reset_email(user)
            return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)  # Don't reveal if user exists
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        try:
            reset_token = PasswordResetToken.objects.get(token=serializer.validated_data['token'])
            if reset_token.is_expired() or reset_token.is_used:
                return Response({'error': 'Token expired or already used'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = reset_token.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            reset_token.is_used = True
            reset_token.save()
            
            return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
        except PasswordResetToken.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    token = request.data.get('token')
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_OAUTH2_CLIENT_ID)
        
        email = idinfo['email']
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_email_verified': True,
            }
        )
        
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Google authentication successful',
            'user': UserProfileSerializer(user).data,
            'tokens': tokens,
            'created': created
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def apple_auth(request):
    # Apple Sign-In implementation
    token = request.data.get('token')
    # Implement Apple ID token verification
    # This requires additional setup with Apple Developer Console
    return Response({'message': 'Apple authentication - Implementation needed'}, 
                   status=status.HTTP_501_NOT_IMPLEMENTED)
