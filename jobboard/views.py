from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator

from .forms import JobPostForm
from .models import StudentProfile, JobPost, TutorProfile, Application
from .serializers import ApplicationSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_job(request):
    try:
        form = JobPostForm(request)

        if form.is_valid():
            job = form.save(commit=False)
            job.student = StudentProfile.objects.get(user=request.user)
            job.save()
            form.save_m2m()

            return Response({"success": True, "message": "Job posted successfully"})
        else:
            return Response({"success": False, "errors": form.errors})
    except Exception as e:
        return Response({"success": False, "message": str(e)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def job_list(request):
    try:
        city = request.GET.get("city")
        subject = request.GET.get("subject")
        page_number = request.GET.get("page", 1)

        jobs = JobPost.objects.all().order_by("-created_at")

        if city:
            jobs = jobs.filter(city__icontains=city)

        if subject:
            jobs = jobs.filter(subjects__id=subject)

        paginator = Paginator(jobs, 10)
        page = paginator.get_page(page_number)

        job_data = []
        for job in page:
            job_data.append(
                {
                    "id": job.id,
                    "title": job.title,
                    "description": job.description,
                    "city": job.city,
                    "subjects": [s.name for s in job.subjects.all()],
                    "student": job.student.user.username,
                    "created_at": job.created_at.strftime("%Y-%m-%d %H:%M"),
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
