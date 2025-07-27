from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.


class Subject(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)


# Upload paths
def upload_to_profile(instance, filename):
    return f"tutors/profile_images/{instance.user.username}/{filename}"


def upload_to_degree(instance, filename):
    return f"tutors/degree_images/{instance.user.username}/{filename}"


def upload_to_cnic_front(instance, filename):
    return f"tutors/cnic_front/{instance.user.username}/{filename}"


def upload_to_cnic_back(instance, filename):
    return f"tutors/cnic_back/{instance.user.username}/{filename}"


class JobPost(models.Model):
    JOB_TYPE_CHOICES = [
        ("online", "Online Tuition"),
        ("regular", "Regular Job"),
        ("home", "Home Tuition"),
    ]

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("any", "Any"),
    ]

    STUDY_MODE_CHOICES = [
        ("individual", "Individual"),
        ("group", "Group"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("blocked", "Blocked"),
    ]

    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    student = models.ForeignKey(
        "StudentProfile", on_delete=models.CASCADE, null=True, blank=True
    )
    employer = models.ForeignKey(
        "EmployerProfile", on_delete=models.CASCADE, null=True, blank=True
    )

    expires_at = models.DateTimeField(null=True, blank=True)
    subjects = models.ManyToManyField(Subject)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    # New fields
    job_type = models.CharField(
        max_length=10, choices=JOB_TYPE_CHOICES, default="online"
    )
    classes = models.CharField(
        max_length=200,
        help_text="Comma-separated class levels (e.g. '9th,10th')",
        null=True,
    )
    days_to_study = models.CharField(
        max_length=100, help_text="e.g. Mon,Wed,Fri", default="Mon to Fri"
    )
    time_to_study = models.CharField(
        max_length=100, help_text="e.g. 4pm-6pm", null=True
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="any")
    budget = models.PositiveIntegerField(default=0)
    qualification_required = models.CharField(max_length=200, default="Bachelors")
    experience_required = models.CharField(max_length=100, null=True, blank=True)
    contact = models.CharField(
        max_length=100, help_text="Contact number or email", null=True, blank=True
    )
    study_mode = models.CharField(
        max_length=20, choices=STUDY_MODE_CHOICES, default="individual"
    )

    def __str__(self):
        return self.title


class TutorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    saved_jobs = models.ManyToManyField(JobPost, blank=True, related_name="saved_by")
    cnic = models.CharField(max_length=15, null=True, blank=True)
    cnic_front_image = models.ImageField(
        upload_to=upload_to_cnic_front, blank=True, null=True
    )
    cnic_back_image = models.ImageField(
        upload_to=upload_to_cnic_back, blank=True, null=True
    )

    profile_image = models.ImageField(
        upload_to=upload_to_profile, blank=True, null=True
    )
    degree_image = models.ImageField(upload_to=upload_to_degree, blank=True, null=True)

    level = models.CharField(max_length=50, null=True, blank=True)
    member_since = models.DateField(null=True, blank=True)

    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile_number_1 = models.CharField(max_length=20, null=True, blank=True)
    mobile_number_2 = models.CharField(max_length=20, blank=True, null=True)

    organization_name = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    salary_package = models.CharField(max_length=100, blank=True, null=True)
    timings_required = models.CharField(max_length=100, blank=True, null=True)

    bio = models.TextField(null=True, blank=True)
    subjects = models.ManyToManyField("Subject", blank=True)
    qualifications = models.ManyToManyField("Qualification", blank=True)
    experience = models.CharField(max_length=255, null=True, blank=True)
    areas_to_teach = models.TextField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    can_teach_online = models.BooleanField(default=False)

    minimum_qualification_required = models.CharField(
        max_length=255, blank=True, null=True
    )
    experience_required = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.level})"


class TutorPayment(models.Model):
    PLAN_CHOICES = [
        ("FREE", "Free"),
        ("BASIC", "Basic"),
        ("PREMIUM", "Premium"),
    ]

    tutor = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="payment_profile"
    )
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default="FREE")
    is_active = models.BooleanField(default=False)  # if subscription is active
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.tutor.username} - {self.plan}"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(
        max_length=100, default="Pakistan", null=True, blank=True
    )
    city = models.CharField(max_length=100, null=True, blank=True)
    area = models.CharField(max_length=100, null=True, blank=True)
    highest_qualification = models.CharField(max_length=100, null=True, blank=True)
    qualifications = models.ManyToManyField("Qualification", blank=True)
    subjects = models.ManyToManyField("Subject", blank=True)
    institute = models.CharField(max_length=150, null=True, blank=True)
    preffered_method = models.CharField(max_length=100, null=True, blank=True)
    days_to_study = models.CharField(max_length=100, null=True, blank=True)
    timing_to_study = models.CharField(max_length=100, null=True, blank=True)
    cnic = models.CharField(max_length=20, null=True, blank=True)
    cnic_or_form_b_pic = models.ImageField(
        upload_to="documents/", null=True, blank=True
    )
    degree = models.ImageField(upload_to="documents/", null=True, blank=True)
    profile = models.ImageField(upload_to="profiles/", null=True, blank=True)
    otp_code = models.CharField(max_length=6, null=True, blank=True)

    joined_date = models.DateField(auto_now_add=True)
    scheduled_classes = models.ManyToManyField("ScheduledClass", blank=True)
    purchased_video_courses = models.ManyToManyField("VideoCourse", blank=True)
    purchased_online_resources = models.ManyToManyField("OnlineResource", blank=True)
    payments = models.ManyToManyField("TutorPayment", blank=True)
    attendance = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.user.username}"


class Application(models.Model):
    CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("withdrawn", "Withdrawn"),
    ]

    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    tutor = models.ForeignKey(TutorProfile, on_delete=models.CASCADE)
    message = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=CHOICES, default="pending")
    applied_at = models.DateTimeField(auto_now_add=True)
    timestamp = models.DateTimeField(auto_now=True)
    status_history = models.JSONField(default=list, blank=True)


class ScheduledClass(models.Model):
    tutor = models.ForeignKey(TutorProfile, on_delete=models.CASCADE)
    student = models.ForeignKey("StudentProfile", on_delete=models.CASCADE)

    subject = models.ForeignKey("Subject", on_delete=models.CASCADE)
    mode = models.CharField(
        max_length=20, choices=[("online", "Online"), ("home", "Home")]
    )
    class_level = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("scheduled", "Scheduled"), ("completed", "Completed")],
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.tutor.user.username} - {self.subject.name}"


class VideoCourse(models.Model):
    tutor = models.ForeignKey(TutorProfile, on_delete=models.CASCADE)
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(null=True, blank=True)


class OnlineResource(models.Model):
    tutor = models.ForeignKey(TutorProfile, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=50,
        choices=[
            ("keybook", "Key Book"),
            ("notes", "Notes"),
            ("pastpapers", "Past Papers"),
        ],
    )
    file = models.FileField(upload_to="resources/", null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)


class Qualification(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    institute = models.CharField(max_length=255, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.institute} ({self.year})"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"


class EmployerProfile(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to="company_logos/")
    description = models.TextField()
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return self.company_name


# For user activity and logs


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"
