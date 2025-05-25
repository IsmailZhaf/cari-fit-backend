from django.db import models
import bson
from jobs.models import Job
from django.conf import settings
from cv.models import CV


def generate_id():
    return str(bson.ObjectId())

class Conversation(models.Model):
    id = models.CharField(max_length=10, primary_key=True, default=generate_id)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    role = models.CharField(max_length=255)
    message = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    cv = models.ForeignKey(CV, on_delete=models.SET_NULL, null=True) 
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True)
