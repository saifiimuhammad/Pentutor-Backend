from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.


class Subject(models.Model):
    name = models.CharField(max_length=100)


class TutorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField()
    subjects = models.ManyToManyField(Subject)
    city = models.CharField(max_length=100)


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)


class JobPost(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    subjects = models.ManyToManyField(Subject)
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


CHOICES = [("pending", "Pending"), ("accepted", "Accepted"), ("rejected", "Rejected")]


class Application(models.Model):
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    tutor = models.ForeignKey(TutorProfile, on_delete=models.CASCADE)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=CHOICES, default="pending")
    applied_at = models.DateTimeField(auto_now_add=True)
