import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import CV
from .serializers import CVUploadSerializer
from .tasks import process_cv_in_background


class CVUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            file = request.FILES.get('file')
            if not file:
                return Response({"error": "No file was uploaded"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not file.name.lower().endswith(('.pdf', '.docx')):
                return Response({"error": "Only PDF and DOCX files are allowed"}, status=status.HTTP_400_BAD_REQUEST)
            
            filename = f"{uuid.uuid4()}_{file.name}"
            file_path = os.path.join('cv_files', filename)
            
            os.makedirs(os.path.join(settings.MEDIA_ROOT, 'cv_files'), exist_ok=True)
            
            saved_path = default_storage.save(file_path, ContentFile(file.read()))
            
            absolute_file_path = os.path.join(settings.MEDIA_ROOT, saved_path)
            
            user_id = request.user.id if request.user.is_authenticated else "anonymous"
            cv_obj = CV.objects.create(
                user_id=user_id,
                file_url=absolute_file_path
            )
            
            # Queue the background task with Huey
            process_cv_in_background(cv_obj.id)
            
            serializer = CVUploadSerializer(cv_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


