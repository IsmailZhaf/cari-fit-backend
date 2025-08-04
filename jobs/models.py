from django.db import models
import uuid

class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=30, blank=True, null=True)
    job_title = models.CharField(max_length=255)
    company_industry = models.CharField(max_length=255, blank=True, null=True)
    company_desc = models.TextField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_employee_size = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    company_logo = models.URLField(max_length=500, blank=True, null=True)
    url = models.URLField(max_length=500, unique=True)
    job_type = models.TextField(blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    job_description = models.TextField(blank=True, null=True)
    experience_level = models.TextField(blank=True, null=True)
    education_level = models.TextField(blank=True, null=True)
    salary = models.TextField(blank=True, null=True)
    skills_required = models.TextField(blank=True, null=True)
    date_posted = models.TextField(blank=True, null=True)
    uploaded_to_vector_db = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"