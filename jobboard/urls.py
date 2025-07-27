from django.urls import path
from . import views


urlpatterns = [
    # login/Register routes
    path("tutor/register", views.register_tutor, name="register_tutor"),
    path("student/register", views.register_student, name="register_student"),
    path("tutor/login", views.login_tutor, name="login_tutor"),
    path("student/login", views.login_student, name="login_student"),
    path("verify_otp", views.verify_otp, name="verify_otp"),
    # Get profile routes
    path("student/<int:student_id>", views.get_student, name="get_student"),
    path("tutor/<int:tutor_id>", views.get_tutor, name="get_tutor"),
    # Jobs
    path("jobs/all", views.job_list, name="job_list"),
    path("jobs/<int:job_id>/apply", views.apply_job, name="apply_job"),
    path("jobs/create", views.create_job, name="create_job"),
    # Applications
    path(
        "student/applications", views.student_applications, name="student_applications"
    ),
    path("tutor/applications", views.tutor_applications, name="tutor_applications"),
    path(
        "application/<int:application_id>/update_status",
        views.update_application_status,
        name="update_application_status",
    ),
    # Misc
    path("tutors/all", views.get_registered_tutors, name="get_registered_tutors"),
    path("student/jobs", views.my_jobs, name="my_jobs"),
    path("get_in_touch", views.get_in_touch, name="get_in_touch"),
    # Admin
    path(
        "admin/jobpost/<int:job_id>/",
        views.admin_jobpost_detail,
        name="admin-jobpost-detail",
    ),
]
