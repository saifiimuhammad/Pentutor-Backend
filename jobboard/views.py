from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import model_to_dict
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from datetime import date
from django.shortcuts import get_object_or_404
from rest_framework import status

from .helper import log_activity, validate_file
from .models import (
    StudentProfile,
    JobPost,
    TutorProfile,
    Application,
    ContactMessage,
    Subject,
    EmployerProfile,
    UserActivity,
)
from .serializers import (
    ApplicationSerializer,
    EmployerSerializer,
    JobPostSerializer,
    TutorProfileSerializer,
    StudentProfileSerializer,
)
from .pagination import StandardPagination
from .utils import send_notification


HOST_EMAIL = "muhammadsaifarain786@gmail.com"


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_job(request):
    try:
        data = request.data

        # Check if user is a student
        try:
            student_profile = StudentProfile.objects.get(user=request.user)
            job = JobPost.objects.create(
                student=student_profile,
                title=data.get("title"),
                description=data.get("description"),
                city=data.get("city"),
                job_type=data.get("job_type"),
                classes=data.get("classes"),
                days_to_study=data.get("days_to_study"),
                time_to_study=data.get("time_to_study"),
                gender=data.get("gender"),
                budget=data.get("budget"),
                qualification_required=data.get("qualification_required"),
                experience_required=data.get("experience_required"),
                contact=data.get("contact"),
                study_mode=data.get("study_mode"),
            )
        except StudentProfile.DoesNotExist:
            # If not a student, check if user is an employer
            try:
                employer_profile = EmployerProfile.objects.get(user=request.user)
                job = JobPost.objects.create(
                    employer=employer_profile,
                    title=data.get("title"),
                    description=data.get("description"),
                    city=data.get("city"),
                    job_type=data.get("job_type"),
                    classes=data.get("classes"),
                    days_to_study=data.get("days_to_study"),
                    time_to_study=data.get("time_to_study"),
                    gender=data.get("gender"),
                    budget=data.get("budget"),
                    qualification_required=data.get("qualification_required"),
                    experience_required=data.get("experience_required"),
                    contact=data.get("contact"),
                    study_mode=data.get("study_mode"),
                )
            except EmployerProfile.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "User is neither a student nor an employer",
                    }
                )

        # Handle ManyToMany subjects
        subject_ids = data.get("subjects", [])
        if subject_ids:
            job.subjects.set(subject_ids)

        log_activity(request.user, f"Created a job {job.pk}")
        return Response(
            {"success": True, "message": "Job posted successfully", "job_id": job.id}
        )

    except Exception as e:
        return Response({"success": False, "message": str(e)})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_job(request, job_id):
    try:
        job = JobPost.objects.get(id=job_id)

        # Check if user owns the job
        if job.student and job.student.user != request.user:
            return Response({"success": False, "message": "Unauthorized"}, status=403)
        if job.employer and job.employer.user != request.user:
            return Response({"success": False, "message": "Unauthorized"}, status=403)

        data = request.data

        for field in [
            "title",
            "description",
            "city",
            "job_type",
            "classes",
            "days_to_study",
            "time_to_study",
            "gender",
            "budget",
            "qualification_required",
            "experience_required",
            "contact",
            "study_mode",
        ]:
            if field in data:
                setattr(job, field, data.get(field))

        # Update subjects if provided
        if "subjects" in data:
            job.subjects.set(data["subjects"])

        job.save()
        log_activity(request.user, f"Updated a job {job_id}")
        return Response({"success": True, "message": "Job updated successfully"})

    except JobPost.DoesNotExist:
        return Response({"success": False, "message": "Job not found"}, status=404)
    except Exception as e:
        return Response({"success": False, "message": str(e)})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_job(request, job_id):
    try:
        job = JobPost.objects.get(id=job_id)

        # Check if user owns the job
        if job.student and job.student.user != request.user:
            return Response({"success": False, "message": "Unauthorized"}, status=403)
        if job.employer and job.employer.user != request.user:
            return Response({"success": False, "message": "Unauthorized"}, status=403)

        job.delete()
        log_activity(request.user, f"Job a deleted {job_id}")
        return Response({"success": True, "message": "Job deleted successfully"})

    except JobPost.DoesNotExist:
        return Response({"success": False, "message": "Job not found"}, status=404)
    except Exception as e:
        return Response({"success": False, "message": str(e)})


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def set_job_expiration(request, job_id):
    try:
        job = JobPost.objects.get(id=job_id)

        # Check if user owns the job
        if job.student and job.student.user != request.user:
            return Response({"success": False, "message": "Unauthorized"}, status=403)
        if job.employer and job.employer.user != request.user:
            return Response({"success": False, "message": "Unauthorized"}, status=403)

        expiration_date = request.data.get("expires_at")
        if not expiration_date:
            return Response(
                {"success": False, "message": "Expiration date is required"}
            )

        job.expires_at = expiration_date
        job.save()
        log_activity(request.user, f"Set job expiration date {job_id}")
        return Response({"success": True, "message": "Expiration date set"})

    except JobPost.DoesNotExist:
        return Response({"success": False, "message": "Job not found"}, status=404)
    except Exception as e:
        return Response({"success": False, "message": str(e)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_jobs_by_status(request):
    status = request.query_params.get("status", "").lower()
    today = date.today()

    if status == "active":
        jobs = JobPost.objects.filter(is_draft=False, expiration_date__gte=today)
    elif status == "expired":
        jobs = JobPost.objects.filter(is_draft=False, expiration_date__lt=today)
    elif status == "draft":
        jobs = JobPost.objects.filter(is_draft=True)
    else:
        return Response({"success": False, "message": "Invalid status"})

    paginator = StandardPagination()
    paginated_jobs = paginator.paginate_queryset(jobs, request)
    serialized = JobPostSerializer(paginated_jobs, many=True)

    return paginator.get_paginated_response({"success": True, "jobs": serialized.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_save_job(request, job_id):
    try:
        profile = TutorProfile.objects.get(user=request.user)
    except TutorProfile.DoesNotExist:
        return Response(
            {"success": False, "message": "Tutor profile not found."}, status=404
        )

    job = get_object_or_404(JobPost, id=job_id)

    if job in profile.saved_jobs.all():
        profile.saved_jobs.remove(job)
        log_activity(request.user, f"Saved a job {job_id}")
        return Response({"success": True, "message": "Job unsaved."})
    else:
        profile.saved_jobs.add(job)
        log_activity(request.user, f"Unsaved a job {job_id}")
        return Response({"success": True, "message": "Job saved."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_saved_jobs(request):
    try:
        profile = TutorProfile.objects.get(user=request.user)
        saved_jobs = profile.saved_jobs.all().order_by("-created_at")

        paginator = StandardPagination()
        paginated_jobs = paginator.paginate_queryset(saved_jobs, request)

        data = [
            {
                "id": job.id,
                "title": job.title,
                "location": job.location,
                "posted_at": job.created_at,
            }
            for job in paginated_jobs
        ]

        return paginator.get_paginated_response({"success": True, "jobs": data})
    except TutorProfile.DoesNotExist:
        return Response(
            {"success": False, "message": "Tutor profile not found."},
            status=404,
        )
    except Exception as err:
        return Response(
            {"success": False, "message": "Something went wrong.", "error": str(err)},
            status=500,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_applied_jobs(request):
    profile = TutorProfile.objects.get(user=request.user)
    applications = Application.objects.filter(tutor=profile).order_by("-created_at")

    paginator = StandardPagination()
    paginated_apps = paginator.paginate_queryset(applications, request)

    data = [
        {
            "job_id": app.job.id,
            "title": app.job.title,
            "status": app.status,
            "applied_on": app.created_at,
        }
        for app in paginated_apps
    ]

    return paginator.get_paginated_response({"success": True, "applied_jobs": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def track_application_history(request, application_id):
    try:
        # Use tutor instead of applicant (based on your model)
        application = Application.objects.get(
            id=application_id, tutor__user=request.user
        )

        # status_history is a list of dicts, e.g., [{"status": "pending", "timestamp": "...", "note": "..."}]
        history = application.status_history

        # Sort by timestamp (assuming it's in ISO format)
        sorted_history = sorted(
            history, key=lambda x: x.get("timestamp", ""), reverse=True
        )

        return Response(
            {
                "success": True,
                "application_id": application.id,
                "job_title": application.job.title if application.job else None,
                "history": sorted_history,
            },
            status=200,
        )

    except Application.DoesNotExist:
        return Response(
            {"success": False, "message": "Application not found."}, status=404
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def withdraw_application(request, application_id):
    try:
        application = Application.objects.get(
            id=application_id, tutor__user=request.user
        )

        if application.status == "withdrawn":
            return Response(
                {"success": False, "message": "Application already withdrawn."}
            )

        application.status = "withdrawn"
        application.save()

        log_activity(request.user, f"Withdrawn application {application_id}")
        return Response(
            {"success": True, "message": "Application withdrawn successfully."}
        )

    except Application.DoesNotExist:
        return Response(
            {"success": False, "message": "Application not found or unauthorized."}
        )

    except Exception as e:
        return Response({"success": False, "message": str(e)})


@api_view(["GET"])
def job_list(request):
    try:
        city = request.GET.get("city")
        subject = request.GET.get("subject")
        job_type = request.GET.get("job_type")
        study_mode = request.GET.get("study_mode")
        search = request.GET.get("search")

        jobs = JobPost.objects.all().order_by("-created_at")

        if city:
            jobs = jobs.filter(city__icontains=city)

        if subject:
            jobs = jobs.filter(subjects__id=subject)

        if job_type:
            jobs = jobs.filter(job_type=job_type)

        if study_mode:
            jobs = jobs.filter(study_mode=study_mode)

        if search:
            jobs = jobs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(jobs, request)

        job_data = [
            {
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "contact": job.contact,
                "city": job.city,
                "job_type": job.job_type,
                "subjects": [s.name for s in job.subjects.all()],
                "student": job.student.user.username if job.student else None,
                "employer": job.employer.user.username if job.employer else None,
                "created_at": job.created_at.strftime("%Y-%m-%d %H:%M"),
                "study_mode": job.study_mode,
            }
            for job in page
        ]

        return paginator.get_paginated_response({"success": True, "jobs": job_data})

    except Exception as e:
        return Response({"success": False, "message": str(e)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apply_job(request, job_id):
    try:
        job = JobPost.objects.get(id=job_id)
        tutor_profile = TutorProfile.objects.get(user=request.user)

        if Application.objects.filter(job=job, tutor=tutor_profile).exists():
            return Response(
                {"success": False, "message": "You have already applied for this job"},
                status=400,
            )

        serializer = ApplicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(job=job, tutor=tutor_profile)
            log_activity(request.user, f"Applied to a Job post {job_id}")
            send_notification(
                user=job.student.user if job.student.user else job.employer.user,
                subject="New Job Application",
                message=f"{request.user.username} applied for {job.title}",
                url=f"/dashboard/applications/{job.id}/",
            )
            return Response(
                {
                    "success": True,
                    "message": "Applied successfully.",
                }
            )
        else:
            return Response({"success": False, "errors": serializer.errors}, status=400)

    except JobPost.DoesNotExist:
        return Response({"success": False, "message": "Job not found."}, status=404)
    except TutorProfile.DoesNotExist:
        return Response(
            {"success": False, "message": "Tutor profile not found."}, status=404
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_applications(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        job_id = request.GET.get("job_id")

        if job_id:
            jobs = JobPost.objects.filter(id=job_id, student=student_profile)
        else:
            jobs = JobPost.objects.filter(student=student_profile)

        applications = (
            Application.objects.filter(job__in=jobs)
            .select_related("tutor", "job", "tutor__user")
            .prefetch_related("tutor__subjects")
            .order_by("-applied_at")
        )

        # Apply pagination
        paginator = StandardPagination()
        paginated_apps = paginator.paginate_queryset(applications, request)

        data = []
        for app in paginated_apps:
            data.append(
                {
                    "job_id": app.job.id,
                    "job_title": app.job.title,
                    "tutor": {
                        "username": app.tutor.user.username,
                        "bio": getattr(app.tutor, "bio", ""),
                        "subjects": [s.name for s in app.tutor.subjects.all()],
                    },
                    "message": app.message,
                    "status": app.status,
                    "applied_at": app.applied_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

        return paginator.get_paginated_response({"success": True, "applications": data})

    except StudentProfile.DoesNotExist:
        return Response(
            {"success": False, "message": "Student profile not found."}, status=404
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tutor_applications(request):
    try:
        tutor_profile = TutorProfile.objects.get(user=request.user)
        applications = (
            Application.objects.filter(tutor=tutor_profile)
            .select_related("job", "job__student", "job__student__user")
            .order_by("-applied_at")
        )

        paginator = StandardPagination()
        paginated_apps = paginator.paginate_queryset(applications, request)

        data = []
        for app in paginated_apps:
            data.append(
                {
                    "job_id": app.job.id,
                    "job_title": app.job.title,
                    "job_description": app.job.description,
                    "city": app.job.city,
                    "student": app.job.student.user.username,
                    "message": app.message,
                    "status": app.status,
                    "applied_at": app.applied_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

        return paginator.get_paginated_response({"success": True, "applications": data})

    except TutorProfile.DoesNotExist:
        return Response(
            {"success": False, "message": "Tutor profile not found."}, status=404
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_application_status(request, application_id):
    try:
        application = Application.objects.select_related("job").get(id=application_id)
        job = application.job
        user = request.user

        # Check if the logged-in user is the owner of the job (either student or employer)
        is_student = job.student and job.student.user == user if job.student else False
        is_employer = (
            job.employer and job.employer.user == user if job.employer else False
        )

        if not (is_student or is_employer):
            return Response(
                {"success": False, "message": "Unauthorized access."}, status=403
            )

        new_status = request.data.get("status")
        if new_status not in ["accepted", "pending", "rejected"]:
            return Response(
                {"success": False, "message": "Invalid status."}, status=400
            )

        application.status = new_status
        application.save()

        log_activity(
            user,
            f"Application {new_status} by {'student' if is_student else 'employer'}.",
        )

        send_notification(
            user=application.tutor.user,
            subject="Your Application Was Reviewed",
            message=f"Your application for {application.job.title} was {status}",
            url=f"/applications/{application.id}/",
        )

        return Response({"success": True, "message": f"Application {new_status}."})

    except Application.DoesNotExist:
        return Response(
            {"success": False, "message": "Application not found."}, status=404
        )


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def view_application_statuses(request):
#     try:
#         profile = TutorProfile.objects.get(user=request.user)
#         applications = Application.objects.filter(tutor=profile)

#         serializer = ApplicationSerializer(applications, many=True)

#         return Response({"success": True, "applications": serializer.data})

#     except Exception as e:
#         return Response({"success": False, "message": str(e)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_registered_tutors(request):
    try:
        tutors = (
            TutorProfile.objects.select_related("user")
            .prefetch_related("subjects")
            .all()
        )

        plan_priority = {"PREMIUM": 1, "BASIC": 2, "FREE": 3}

        sorted_tutors = sorted(
            tutors,
            key=lambda t: plan_priority.get(
                getattr(t.user.payment_profile, "plan", "FREE"), 4
            ),
        )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(sorted_tutors, request)

        data = []
        for tutor in page:
            data.append(
                {
                    "username": tutor.user.username,
                    "bio": tutor.bio,
                    "subjects": [s.name for s in tutor.subjects.all()],
                    "plan": getattr(tutor.user.payment_profile, "plan", "FREE"),
                }
            )

        return paginator.get_paginated_response({"success": True, "tutors": data})

    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_jobs(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        jobs = JobPost.objects.filter(student=student_profile).order_by("-created_at")

        paginator = StandardPagination()
        page = paginator.paginate_queryset(jobs, request)

        job_data = []
        for job in page:
            job_data.append(
                {
                    "id": job.id,
                    "title": job.title,
                    "description": job.description,
                    "contact": job.contact,
                    "city": job.city,
                    "job_type": job.job_type,
                    "subjects": [s.name for s in job.subjects.all()],
                    "created_at": job.created_at.strftime("%Y-%m-%d %H:%M"),
                    "study_mode": job.study_mode,
                }
            )

        return paginator.get_paginated_response({"success": True, "jobs": job_data})

    except StudentProfile.DoesNotExist:
        return Response(
            {"success": False, "message": "Student profile not found."}, status=404
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_in_touch(request):
    try:
        name = request.data.get("name")
        email = request.data.get("email")
        phone = request.data.get("phone")
        message = request.data.get("message")

        ContactMessage.objects.create(
            name=name, email=email, phone=phone, message=message
        )
        log_activity(request.user, "Contacted us")
        return Response({"success": True, "message": "Thanks for contacting us!"})
    except Exception as err:
        return Response(
            {"success": False, "message": "Something went wrong.", "error": err}
        )


@api_view(["POST"])
def login_tutor(request):
    try:
        username = request.data.get("username")
        password = request.data.get("password")

        tutor = TutorProfile.objects.get(user__username=username)
        if tutor.user.check_password(password):
            # Generate 6-digit OTP
            otp = get_random_string(length=6, allowed_chars="1234567890")
            tutor.otp_code = otp
            tutor.save()

            # Send email
            send_mail(
                "Your OTP Code",
                f"Your OTP code is: {otp}",
                # settings.DEFAULT_FROM_EMAIL,
                HOST_EMAIL,
                [tutor.email],
                fail_silently=False,
            )

            return Response(
                {
                    "success": True,
                    "message": "OTP sent to your email.",
                }
            )

        else:
            return Response({"success": False, "message": "Invalid credentials."})
    except TutorProfile.DoesNotExist:
        return Response({"success": False, "message": "Tutor not found."})


@api_view(["POST"])
def register_tutor(request):
    try:
        full_name = request.data.get("full_name")
        email = request.data.get("email")
        mobile_number_1 = request.data.get("mobile_number_1")
        date_of_birth = request.data.get("date_of_birth")
        country = request.data.get("country")
        city = request.data.get("city")
        area = request.data.get("area")
        cnic = request.data.get("cnic")
        cnic_front = request.FILES.get("cnic_front")
        cnic_back = request.FILES.get("cnic_back")
        degree_image = request.FILES.get("degree_image")
        profile_image = request.FILES.get("profile_image")

        if (
            not full_name
            or not email
            or not mobile_number_1
            or not date_of_birth
            or not country
            or not city
            or not area
            or not cnic
            or not cnic_front
            or not cnic_back
            or not degree_image
            or not profile_image
        ):
            return Response({"success": False, "message": "All fields are required."})

        if TutorProfile.objects.filter(cnic=cnic, email=email).exists():
            return Response({"success": False, "message": "Tutor already exists."})

        for file, name in [
            (cnic_front, "CNIC Front"),
            (cnic_back, "CNIC Back"),
            (degree_image, "Degree Image"),
            (profile_image, "Profile Image"),
        ]:
            validate_file(file, name)

        tutor = TutorProfile.objects.create(
            full_name=full_name,
            email=email,
            mobile_number_1=mobile_number_1,
            date_of_birth=date_of_birth,
            country=country,
            city=city,
            area=area,
            cnic=cnic,
            cnic_front=cnic_front,
            cnic_back=cnic_back,
            degree_image=degree_image,
            profile_image=profile_image,
            user=request.user,
        )

        tutor.save()

        log_activity(request.user, "Tutor registered successfully")
        return Response(
            {
                "success": True,
                "message": "Tutor registered successfully.",
                "tutor": model_to_dict(tutor),
            }
        )

    except Exception as err:
        return Response(
            {"success": False, "message": "Something went wrong.", "error": str(err)}
        )


@api_view(["POST"])
def verify_otp(request):
    user_id = request.data.get("id")
    otp = request.data.get("otp")
    user_type = request.data.get("user_type")  # "tutor" or "student"

    if not user_id or not otp or not user_type:
        return Response(
            {"success": False, "message": "id, otp, and user_type are required"},
            status=400,
        )

    try:
        if user_type == "tutor":
            tutor = TutorProfile.objects.get(id=user_id)
            if tutor.otp_code == otp:
                tutor.otp_code = None
                tutor.save()

                log_activity(request.user, f"OTP verified for Tutor ID {user_id}")
                return Response(
                    {
                        "success": True,
                        "message": "OTP verified. Login successful.",
                        "tutor": model_to_dict(tutor),
                    },
                    status=200,
                )
            else:
                return Response(
                    {"success": False, "message": "Invalid OTP."}, status=400
                )

        elif user_type == "student":
            student = StudentProfile.objects.get(id=user_id)
            if student.otp_code == otp:
                student.otp_code = None
                student.save()

                log_activity(request.user, f"OTP verified for Student ID {user_id}")
                return Response(
                    {
                        "success": True,
                        "message": "OTP verified. Login successful.",
                        "student": model_to_dict(student),
                    },
                    status=200,
                )
            else:
                return Response(
                    {"success": False, "message": "Invalid OTP."}, status=400
                )

        else:
            return Response(
                {"success": False, "message": "Invalid user type"}, status=400
            )

    except TutorProfile.DoesNotExist:
        return Response({"success": False, "message": "Tutor not found."}, status=404)
    except StudentProfile.DoesNotExist:
        return Response({"success": False, "message": "Student not found."}, status=404)
    except Exception as err:
        return Response({"success": False, "message": str(err)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_tutor(request, tutor_id):
    try:
        tutor = TutorProfile.objects.get(id=tutor_id)
        return Response(
            {
                "success": True,
                "tutor": model_to_dict(tutor),
            }
        )
    except TutorProfile.DoesNotExist:
        return Response({"success": False, "message": "Tutor not found."})
    except Exception as err:
        return Response(
            {"success": False, "message": "Something went wrong.", "error": str(err)}
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_tutor(request, tutor_id):
    try:
        tutor = TutorProfile.objects.get(id=tutor_id)

        if tutor.user != request.user:
            return Response({"success": False, "message": "Unauthorized."}, status=403)

        serializer = TutorProfileSerializer(tutor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Tutor profile updated successfully.",
                    "tutor": serializer.data,
                }
            )
        else:
            return Response({"success": False, "errors": serializer.errors}, status=400)

    except TutorProfile.DoesNotExist:
        return Response({"success": False, "message": "Tutor not found."}, status=404)
    except Exception as err:
        return Response(
            {"success": False, "message": "Update failed.", "error": str(err)},
            status=500,
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_tutor(request, tutor_id):
    try:
        tutor = TutorProfile.objects.get(id=tutor_id)

        if tutor.user != request.user:
            return Response({"success": False, "message": "Unauthorized."}, status=403)

        tutor.delete()
        return Response({"success": True, "message": "Tutor profile deleted."})
    except TutorProfile.DoesNotExist:
        return Response({"success": False, "message": "Tutor not found."}, status=404)
    except Exception as err:
        return Response(
            {"success": False, "message": "Error occurred.", "error": str(err)},
            status=500,
        )


@api_view(["POST"])
def login_student(request):
    try:
        username = request.data.get("username")
        password = request.data.get("password")

        student = StudentProfile.objects.get(user__username=username)
        if student.user.check_password(password):
            # Generate 6-digit OTP
            otp = get_random_string(length=6, allowed_chars="1234567890")
            student.otp_code = otp
            student.save()

            # Send email
            send_mail(
                "Your OTP Code",
                f"Your OTP code is: {otp}",
                # settings.DEFAULT_FROM_EMAIL,
                HOST_EMAIL,
                [student.email],
                fail_silently=False,
            )

            return Response(
                {
                    "success": True,
                    "message": "OTP sent to your email.",
                }
            )

        else:
            return Response({"success": False, "message": "Invalid credentials."})
    except StudentProfile.DoesNotExist:
        return Response({"success": False, "message": "Tutor not found."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_student(request):
    try:
        data = request.data

        required_fields = [
            "name",
            "email",
            "phone",
            "date_of_birth",
            "country",
            "city",
            "area",
        ]
        for field in required_fields:
            if not data.get(field):
                return Response({"success": False, "message": f"{field} is required."})

        for file, name in [
            (request.FILES.get("cnic_or_form_b_pic"), "CNIC or Form-B"),
            (request.FILES.get("degree"), "Degree Image"),
            (request.FILES.get("profile"), "Profile Image"),
        ]:
            validate_file(file, name)

        student_profile = StudentProfile.objects.create(
            user=request.user,
            name=data.get("name"),
            email=data.get("email"),
            phone=data.get("phone"),
            date_of_birth=data.get("date_of_birth"),
            country=data.get("country"),
            city=data.get("city"),
            area=data.get("area"),
            highest_qualification=data.get("highest_qualification"),
            institute=data.get("institute"),
            preffered_method=data.get("preffered_method"),
            days_to_study=data.get("days_to_study"),
            timing_to_study=data.get("timing_to_study"),
            cnic=data.get("cnic"),
            cnic_or_form_b_pic=request.FILES.get("cnic_or_form_b_pic"),
            degree=request.FILES.get("degree"),
            profile=request.FILES.get("profile"),
        )

        subject_ids = data.getlist("subjects")
        if subject_ids:
            student_profile.subjects.set(Subject.objects.filter(id__in=subject_ids))

        log_activity(request.user, "Student registered successfully")
        return Response(
            {
                "success": True,
                "message": "Student registered successfully.",
                "student": model_to_dict(student_profile),
            }
        )

    except Exception as err:
        return Response(
            {
                "success": False,
                "message": "Something went wrong.",
                "error": str(err),
            }
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_student(request, student_id):
    try:
        student_id = StudentProfile.objects.get(id=student_id)
        return Response(
            {
                "success": True,
                "student_id": model_to_dict(student_id),
            }
        )
    except StudentProfile.DoesNotExist:
        return Response({"success": False, "message": "Tutor not found."})
    except Exception as err:
        return Response(
            {"success": False, "message": "Something went wrong.", "error": str(err)}
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_student(request, student_id):
    try:
        student = StudentProfile.objects.get(id=student_id)

        if student.user != request.user:
            return Response({"success": False, "message": "Unauthorized."}, status=403)

        serializer = StudentProfileSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Student profile updated.",
                    "student": serializer.data,
                }
            )
        return Response({"success": False, "errors": serializer.errors}, status=400)

    except StudentProfile.DoesNotExist:
        return Response({"success": False, "message": "Student not found."}, status=404)
    except Exception as err:
        return Response(
            {"success": False, "message": "Update failed.", "error": str(err)},
            status=500,
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_student(request, student_id):
    try:
        student = StudentProfile.objects.get(id=student_id)

        if student.user != request.user:
            return Response({"success": False, "message": "Unauthorized."}, status=403)

        student.delete()
        return Response({"success": True, "message": "Student profile deleted."})

    except StudentProfile.DoesNotExist:
        return Response({"success": False, "message": "Student not found."}, status=404)
    except Exception as err:
        return Response(
            {"success": False, "message": "Delete failed.", "error": str(err)},
            status=500,
        )


@api_view(["POST"])
def create_employer_profile(request):
    try:
        if EmployerProfile.objects.filter(user=request.user).exists():
            return Response(
                {"success": False, "message": "Employer profile already exists."},
                status=400,
            )

        serializer = EmployerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            log_activity(request.user, "Employer profile created")
            return Response(
                {
                    "success": True,
                    "message": "Employer profile created.",
                    "profile": serializer.data,
                }
            )
        return Response({"success": False, "errors": serializer.errors}, status=400)

    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_employer_profile(request):
    try:
        profile = EmployerProfile.objects.get(user=request.user)
        serializer = EmployerSerializer(profile)
        return Response({"success": True, "profile": serializer.data}, status=200)
    except EmployerProfile.DoesNotExist:
        return Response({"success": False, "message": "Profile not found."}, status=404)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_employer_profile(request):
    try:
        profile = EmployerProfile.objects.get(user=request.user)
        serializer = EmployerSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_activity(request.user, "Employer profile updated")
            return Response(
                {
                    "success": True,
                    "message": "Employer profile updated.",
                    "profile": serializer.data,
                }
            )
        return Response({"success": False, "errors": serializer.errors}, status=400)

    except EmployerProfile.DoesNotExist:
        return Response({"success": False, "message": "Profile not found."}, status=404)
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=500)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_employer_profile(request):
    try:
        profile = EmployerProfile.objects.get(user=request.user)
        profile.delete()
        log_activity(request.user, "Employer profile deleted")
        return Response(
            {"success": True, "message": "Employer profile deleted."}, status=200
        )
    except EmployerProfile.DoesNotExist:
        return Response({"success": False, "message": "Profile not found."}, status=404)
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=500)


# @api_view(["PUT"])
# @permission_classes([IsAuthenticated])
# def withdraw_application(request, job_id):
#     try:
#         tutor_profile = request.user  # Assuming OneToOne field
#         application = get_object_or_404(Application, job_id=job_id, tutor=tutor_profile)

#         if application.status in ["withdrawn", "rejected"]:
#             return Response(
#                 {
#                     "success": False,
#                     "error": "Application already withdrawn or rejected.",
#                 },
#                 status=400,
#             )

#         application.status = "withdrawn"
#         application.save()
#         log_activity(request.user, "Withdrawn application")
#         return Response(
#             {"success": True, "message": "Application withdrawn successfully."}
#         )
#     except Exception as err:
#         return Response({"success": False, "error": str(err)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def job_recommendation(request):
    try:
        tutor = TutorProfile.objects.get(user=request.user)
    except TutorProfile.DoesNotExist:
        return Response({"error": "Tutor profile not found."}, status=404)

    tutor_subjects = set(tutor.subjects.values_list("name", flat=True))
    tutor_city = tutor.city.lower() if tutor.city else ""

    jobs = JobPost.objects.filter(status="approved")
    recommendations = []

    for job in jobs:
        job_subjects = set(job.subjects.values_list("name", flat=True))
        job_city = job.city.lower() if job.city else ""

        match_score = len(tutor_subjects.intersection(job_subjects))

        if tutor_city and tutor_city in job_city:
            match_score += 1

        if match_score > 0:
            recommendations.append((job, match_score))

    recommendations.sort(key=lambda x: x[1], reverse=True)

    recommended_jobs = [job for job, _ in recommendations]

    paginator = StandardPagination()
    page = paginator.paginate_queryset(recommended_jobs, request)
    serialized = JobPostSerializer(page, many=True)

    return paginator.get_paginated_response(
        {"success": True, "recommended_jobs": serialized.data}
    )


# Admin only APIs


@api_view(["GET"])
# @permission_classes([IsAdminUser])
def view_all_users(request):
    try:
        page_number = request.GET.get("page", 1)

        students = StudentProfile.objects.all().values() or {}
        tutors = TutorProfile.objects.all().values() or {}
        employers = EmployerProfile.objects.all().values() or {}

        student_paginator = Paginator(students, 10)
        tutor_paginator = Paginator(tutors, 10)
        employer_paginator = Paginator(employers, 10)

        students_page = student_paginator.get_page(page_number)
        tutors_page = tutor_paginator.get_page(page_number)
        employers_page = employer_paginator.get_page(page_number)

        users = {
            "students": list(students_page),
            "tutors": list(tutors_page),
            "employers": list(employers_page),
        }

        return Response(
            {
                "success": True,
                "users": users,
                "pagination": {
                    "current_page": int(page_number),
                    "total_student_pages": student_paginator.num_pages,
                    "total_tutor_pages": tutor_paginator.num_pages,
                    "total_employer_pages": employer_paginator.num_pages,
                },
            }
        )

    except Exception as err:
        return Response({"success": False, "error": str(err)}, status=500)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def view_user(request, user_type, user_id):
    try:
        model = {
            "student": StudentProfile,
            "tutor": TutorProfile,
            "employer": EmployerProfile,
        }.get(user_type.lower())

        if not model:
            return Response(
                {"success": False, "error": "Invalid user type"}, status=400
            )

        user = model.objects.get(id=user_id)

        data = {
            "id": user.id,
            "username": user.user.username,
            "email": user.user.email,
            "is_active": user.user.is_active,
            "type": user_type.lower(),
        }
        return Response({"success": True, "user": data})
    except model.DoesNotExist:
        return Response({"success": False, "error": "User not found"}, status=404)
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["PUT"])
@permission_classes([IsAdminUser])
def edit_user(request, user_type, user_id):
    try:
        model = {
            "student": StudentProfile,
            "tutor": TutorProfile,
            "employer": EmployerProfile,
        }.get(user_type.lower())

        if not model:
            return Response(
                {"success": False, "error": "Invalid user type"}, status=400
            )

        user = model.objects.get(id=user_id)

        username = request.data.get("username")
        email = request.data.get("email")

        if username:
            user.user.username = username
        if email:
            user.user.email = email

        user.user.save()
        log_activity(request.user, "User updated")
        return Response({"success": True, "message": "User updated"})
    except model.DoesNotExist:
        return Response({"success": False, "error": "User not found"}, status=404)
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def disable_user(request, user_type, user_id):
    try:
        model = {
            "student": StudentProfile,
            "tutor": TutorProfile,
            "employer": EmployerProfile,
        }.get(user_type.lower())

        if not model:
            return Response(
                {"success": False, "error": "Invalid user type"}, status=400
            )

        user = model.objects.get(id=user_id)
        user.user.is_active = False
        user.user.save()
        log_activity(request.user, "User disabled")
        return Response({"success": True, "message": "User disabled"})
    except model.DoesNotExist:
        return Response({"success": False, "error": "User not found"}, status=404)
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def enable_user(request, user_type, user_id):
    try:
        model = {
            "student": StudentProfile,
            "tutor": TutorProfile,
            "employer": EmployerProfile,
        }.get(user_type.lower())

        if not model:
            return Response(
                {"success": False, "error": "Invalid user type"}, status=400
            )

        user = model.objects.get(id=user_id)
        user.user.is_active = True
        user.user.save()
        log_activity(request.user, "User enabled")
        return Response({"success": True, "message": "User enabled"})
    except model.DoesNotExist:
        return Response({"success": False, "error": "User not found"}, status=404)
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAdminUser])
def admin_jobpost_detail(request, job_id):
    try:
        job = JobPost.objects.get(pk=job_id)
    except JobPost.DoesNotExist:
        return Response({"success": False, "error": "Job post not found"}, status=404)

    # View Job
    if request.method == "GET":
        serializer = JobPostSerializer(job)
        return Response({"success": True, "job": serializer.data})

    # Update (Edit Job)
    if request.method == "PUT":
        serializer = JobPostSerializer(job, data=request.data)
        if serializer.is_valid():
            serializer.save()
            log_activity(request.user, f"Job post updated! {job.pk}")
            return Response({"success": True, "job": serializer.data})
        return Response({"success": False, "errors": serializer.errors}, status=400)

    # Approve or Block
    if request.method == "PATCH":
        status_action = request.data.get("status")
        if status_action in ["approved", "blocked", "pending"]:
            job.status = status_action
            job.save()
            log_activity(
                request.user, f"{job.pk} Job status updated to {status_action}"
            )
            return Response(
                {"success": True, "message": f"Job status updated to {status_action}"}
            )
        return Response({"success": False, "error": "Invalid status"}, status=400)

    # Remove Job
    if request.method == "DELETE":
        job.delete()
        log_activity(request.user, f"{job.pk} Job post deleted successfully")
        return Response(
            {"success": True, "message": "Job post deleted successfully"},
            status=204,
        )


@api_view(["GET", "PATCH"])
@permission_classes([IsAdminUser])
def approve_reject_employer(request, employer_id):
    try:
        employer = EmployerProfile.objects.get(pk=employer_id)
    except EmployerProfile.DoesNotExist:
        return Response({"success": False, "error": "Employer not found"}, status=404)

    if request.method == "GET":
        serializer = EmployerSerializer(employer)
        return Response({"success": True, "employer": serializer.data}, status=200)

    if request.method == "PATCH":
        status_action = request.data.get("status")
        if status_action in ["approved", "rejected", "pending"]:
            employer.status = status_action
            employer.save()
            log_activity(request.user, f"Employer status updated to {status_action}")
            return Response(
                {
                    "success": True,
                    "message": f"Employer status updated to {status_action}",
                },
                status=200,
            )

        return Response({"success": False, "error": "Invalid status"}, status=400)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def user_activity_list(request):
    activities = UserActivity.objects.all().order_by("-timestamp")

    paginator = StandardPagination()
    page = paginator.paginate_queryset(activities, request)

    data = [
        {"user": act.user.username, "action": act.action, "time": act.timestamp}
        for act in page
    ]

    return paginator.get_paginated_response({"success": True, "activities": data})
