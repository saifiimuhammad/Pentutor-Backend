from django.urls import path
from . import views


urlpatterns = [
    path("create/", views.create_job, name="create_job"),
    path("all/", views.job_list, name="job_list"),
    path("apply/<int:job_id>/", views.apply_job, name="apply_job"),
    path(
        "student/applications/", views.student_applications, name="student_applications"
    ),
    path("tutor/applications/", views.tutor_applications, name="tutor_applications"),
    path(
        "applications/<int:application_id>/status/",
        views.update_application_status,
        name="update_application_status",
    ),
]
