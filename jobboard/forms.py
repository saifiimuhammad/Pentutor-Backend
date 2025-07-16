from django import forms
from .models import JobPost







class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobPost
        fields = ['title', 'description', 'subjects', 'city']
        