from django.urls import path
from . import views

urlpatterns = [
    # Meetings
    path('create/', views.create_meeting, name='create_meeting'),
    path('join/<str:meeting_id>/', views.join_meeting, name='join_meeting'),
    path('leave/<str:meeting_id>/', views.leave_meeting, name='leave_meeting'),
    path('end/<str:meeting_id>/', views.end_meeting, name='end_meeting'),
    path('<str:meeting_id>/participants/', views.get_meeting_participants, name='meeting_participants'),
     path('download-recording/<int:meeting_id>/', views.download_recording, name='download-recording'),
]