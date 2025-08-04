from django.db import models
from django.conf import settings
from jobs.models import Job


class JobRecommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_recommendations')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='recommended_to')
    recommended_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(blank=True, null=True)  # optional, misal skor relevansi rekomendasi
    matched_skills = models.JSONField(default=list, blank=True)  # list of skills that matched with the job
    reason = models.TextField(blank=True, null=True)  # alasan rekomendasi, bisa diisi manual atau otomatis

    class Meta:
        unique_together = ('user', 'job')  # supaya user tidak dapat rekomendasi job yang sama berulang

    def __str__(self):
        return f"Recommendation for {self.user.username}: {self.job.job_title}"