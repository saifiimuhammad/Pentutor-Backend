from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import model_to_dict
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from datetime import date
from django.shortcuts import get_object_or_404

from .models import (
    StudentProfile,
    JobPost,
    TutorProfile,
    Application,
    ContactMessage,
    Subject,
    EmployerProfile,
)
from .serializers import ApplicationSerializer, EmployerProfileSerializer


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
        jobs = JobPost.objects.filter(is_draft=False).filter(expiration_date__gte=today)
    elif status == "expired":
        jobs = JobPost.objects.filter(is_draft=False).filter(expiration_date__lt=today)
    elif status == "draft":
        jobs = JobPost.objects.filter(is_draft=True)
    else:
        return Response({"success": False, "message": "Invalid status"})

    return Response({"success": True, "jobs": jobs})


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
        return Response({"success": True, "message": "Job unsaved."})
    else:
        profile.saved_jobs.add(job)
        return Response({"success": True, "message": "Job saved."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_saved_jobs(request):
    saved_jobs = request.user.saved_jobs.all()  # Assuming ManyToManyField in User model
    data = [
        {
            "id": job.id,
            "title": job.title,
            "location": job.location,
            "posted_at": job.created_at,
        }
        for job in saved_jobs
    ]
    return Response({"success": True, "jobs": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_applied_jobs(request):
    applications = Application.objects.filter(applicant=request.user)
    data = [
        {
            "job_id": app.job.id,
            "title": app.job.title,
            "status": app.status,
            "applied_on": app.created_at,
        }
        for app in applications
    ]
    return Response({"success": True, "applied_jobs": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def track_application_history(request, application_id):
    try:
        application = Application.objects.get(id=application_id, applicant=request.user)
        history = (
            application.status_history.all()
        )  # Assuming related model with status + timestamp

        data = [
            {
                "status": record.status,
                "timestamp": record.timestamp,
                "note": record.note,
            }
            for record in history.order_by("-timestamp")
        ]

        return Response(
            {
                "success": True,
                "application_id": application.id,
                "job_title": application.job.title,
                "history": data,
            }
        )

    except Application.DoesNotExist:
        return Response(
            {"success": False, "message": "Application not found."}, status=404
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def withdraw_application(request, application_id):
    try:
        application = Application.objects.get(id=application_id, user=request.user)

        if application.status == "withdrawn":
            return Response(
                {"success": False, "message": "Application already withdrawn."}
            )

        application.status = "withdrawn"
        application.save()

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
        page_number = request.GET.get("page", 1)

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

        paginator = Paginator(jobs, 10)
        page = paginator.get_page(page_number)

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
                    "student": job.student.user.username,
                    "created_at": job.created_at.strftime("%Y-%m-%d %H:%M"),
                    "study_mode": job.study_mode,
                }
            )

        return Response(
            {
                "success": True,
                "jobs": job_data,
                "page": page.number,
                "total_pages": paginator.num_pages,
                "total_jobs": paginator.count,
            }
        )

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

        applications = Application.objects.filter(job__in=jobs).select_related(
            "tutor", "job", "tutor__user"
        )

        data = []
        for app in applications:
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

        return Response({"success": True, "applications": data})

    except StudentProfile.DoesNotExist:
        return Response(
            {"success": False, "message": "Student profile not found."}, status=404
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tutor_applications(request):
    try:
        tutor_profile = TutorProfile.objects.get(user=request.user)
        applications = Application.objects.filter(tutor=tutor_profile).select_related(
            "job", "job__student", "job__student__user"
        )

        data = []
        for app in applications:
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

        return Response({"success": True, "applications": data})

    except TutorProfile.DoesNotExist:
        return Response(
            {"success": False, "message": "Tutor profile not found."}, status=404
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_application_status(request, application_id):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        application = Application.objects.select_related("job", "job__student").get(
            id=application_id
        )

        if application.job.student != student_profile:
            return Response(
                {"success": False, "message": "Unauthorized access."}, status=403
            )

        new_status = request.data.get("status")
        if new_status not in ["accepted", "rejected"]:
            return Response(
                {"success": False, "message": "Invalid status."}, status=400
            )

        application.status = new_status
        application.save()

        return Response({"success": True, "message": f"Application {new_status}."})

    except Application.DoesNotExist:
        return Response(
            {"success": False, "message": "Application not found."}, status=404
        )

    except StudentProfile.DoesNotExist:
        return Response(
            {"success": False, "message": "Student profile not found."}, status=404
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_application_statuses(request):
    try:
        # Get all job applications for the current user
        applications = Application.objects.filter(user=request.user)

        serializer = ApplicationSerializer(applications, many=True)

        return Response({"success": True, "applications": serializer.data})

    except Exception as e:
        return Response({"success": False, "message": str(e)})


@api_view(["GET"])
def get_registered_tutors(request):
    try:
        tutors = TutorProfile.objects.select_related("payment").all()

        plan_priority = {"premium": 1, "basic": 2, "free": 3}
        tutors = sorted(tutors, key=lambda t: plan_priority.get(t.payment.plan, 4))

        page_number = request.GET.get("page", 1)
        paginator = Paginator(tutors, 10)
        page = paginator.get_page(page_number)

        data = []
        for tutor in page:
            data.append(
                {
                    "username": tutor.user.username,
                    "bio": tutor.bio,
                    "subjects": [s.name for s in tutor.subjects.all()],
                    "plan": tutor.payment.plan,
                }
            )

        return Response(
            {
                "success": True,
                "tutors": data,
                "total_pages": paginator.num_pages,
                "current_page": page.number,
            }
        )

    except Exception as e:
        return Response({"success": False, "message": str(e)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_jobs(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        jobs = JobPost.objects.filter(student=student_profile).order_by("-created_at")

        page_number = request.GET.get("page", 1)
        paginator = Paginator(jobs, 10)
        page = paginator.get_page(page_number)

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

        return Response(
            {
                "success": True,
                "jobs": job_data,
                "total_pages": paginator.num_pages,
                "current_page": page.number,
            }
        )
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

        tutor = TutorProfile.objects.get(username=username)
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
        name = request.data.get("name")
        email = request.data.get("email")
        phone = request.data.get("phone")
        date_of_birth = request.data.get("date_of_birth")
        country = request.data.get("country")
        city = request.data.get("city")
        area = request.data.get("area")
        cnic = request.data.get("cnic")
        cnic_front = request.data.get("cnic_front")
        cnic_back = request.data.get("cnic_back")
        degree_image = request.data.get("degree_image")
        profile_image = request.data.get("profile_image")

        if (
            not name
            or not email
            or not phone
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

        tutor = TutorProfile.objects.create(
            name=name,
            email=email,
            phone=phone,
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
    username = request.data.get("username")
    otp = request.data.get("otp")

    try:
        tutor = TutorProfile.objects.get(username=username)
        if tutor:
            if tutor.otp_code == otp:
                tutor.otp_code = None
                tutor.save()
                return Response(
                    {
                        "success": True,
                        "message": "OTP verified. Login successful.",
                        "tutor": model_to_dict(tutor),
                    }
                )
            else:
                return Response({"success": False, "message": "Invalid OTP."})
        else:
            student = StudentProfile.objects.get(username=username)
            if student.otp_code == otp:
                student.otp_code = None
                student.save()
                return Response(
                    {
                        "success": True,
                        "message": "OTP verified. Login successful.",
                        "student": model_to_dict(student),
                    }
                )
            else:
                return Response({"success": False, "message": "Invalid OTP."})

    except TutorProfile.DoesNotExist:
        return Response({"success": False, "message": "Tutor not found."})
    except StudentProfile.DoesNotExist:
        return Response({"success": False, "message": "Student not found."})
    except Exception as err:
        return Response({"success": False, "message": str(err)})


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


@api_view(["POST"])
def login_student(request):
    try:
        username = request.data.get("username")
        password = request.data.get("password")

        student = StudentProfile.objects.get(username=username)
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

        subject_ids = data.getlist("subjects")  # expects list of ids
        if subject_ids:
            student_profile.subjects.set(Subject.objects.filter(id__in=subject_ids))

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


@api_view(["POST"])
def create_employer_profile(request):
    try:
        if EmployerProfile.objects.filter(user=request.user).exists():
            return Response(
                {"success": False, "message": "Employer profile already exists."},
                status=400,
            )

        serializer = EmployerProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
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


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_employer_profile(request):
    try:
        profile = EmployerProfile.objects.get(user=request.user)
        serializer = EmployerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
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
