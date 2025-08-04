from django.contrib import admin
from .models import JobRecommendation

# Register your models here.
@admin.register(JobRecommendation)
class JobRecommendationAdmin(admin.ModelAdmin):
    list_filter = ('user', 'job', 'recommended_at', 'score')
    search_fields = ('user__username', 'job__job_title', 'score', 'matched_skills')
