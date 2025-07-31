from django.urls import path
from . import views

urlpatterns = [
    # Auth & Registration
    path("tutor/register", views.register_tutor),
    path("student/register", views.register_student),
    path("tutor/login", views.login_tutor),
    path("student/login", views.login_student),
    path("verify_otp", views.verify_otp),
    # Profile (Student & Tutor)
    path("student/<int:student_id>", views.get_student),
    path("student/<int:student_id>/update", views.update_student),
    path("student/<int:student_id>/delete", views.delete_student),
    path("tutor/<int:tutor_id>", views.get_tutor),
    path("tutor/<int:tutor_id>/update", views.update_tutor),
    path("tutor/<int:tutor_id>/delete", views.delete_tutor),
    # Jobs
    path("jobs/all", views.job_list),
    path("jobs/create", views.create_job),
    path("jobs/<int:job_id>/apply", views.apply_job),
    path("jobs/<int:job_id>/update", views.update_job),
    path("jobs/<int:job_id>/delete", views.delete_job),
    path("jobs/<int:job_id>/set_expiration", views.set_job_expiration),
    path("jobs/status", views.get_jobs_by_status),
    path("jobs/<int:job_id>/save", views.toggle_save_job),
    path("jobs/saved", views.view_saved_jobs),
    path("jobs/applied", views.view_applied_jobs),
    path("jobs/recommended", views.job_recommendation),
    # Applications
    path("student/applications", views.student_applications),
    path("tutor/applications", views.tutor_applications),
    path(
        "application/<int:application_id>/update_status",
        views.update_application_status,
    ),
    path("application/<int:application_id>/history", views.track_application_history),
    path("application/<int:application_id>/withdraw", views.withdraw_application),
    # Employers
    path("employer/create", views.create_employer_profile),
    path("employer", views.get_employer_profile),
    path("employer/update", views.update_employer_profile),
    path("employer/delete", views.delete_employer_profile),
    # Misc
    path("tutors/all", views.get_registered_tutors),
    path("student/jobs", views.my_jobs),
    path("get_in_touch", views.get_in_touch),
    # Admin
    path("admin/jobpost/<int:job_id>/", views.admin_jobpost_detail),
    path("admin/users", views.view_all_users),
    path("admin/user/<str:user_type>/<int:user_id>/", views.view_user),
    path("admin/user/<str:user_type>/<int:user_id>/edit", views.edit_user),
    path("admin/user/<str:user_type>/<int:user_id>/disable", views.disable_user),
    path("admin/user/<str:user_type>/<int:user_id>/enable", views.enable_user),
    path("admin/employer/<int:employer_id>/", views.approve_reject_employer),
    path("admin/activity", views.user_activity_list),
]
