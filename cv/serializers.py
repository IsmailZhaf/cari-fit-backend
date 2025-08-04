from rest_framework import serializers
from .models import CV

class CVUploadSerializer(serializers.ModelSerializer):
    cv_id = serializers.UUIDField(source='id', read_only=True)
    message = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField(read_only=True)
    
    def get_message(self, obj):
        return "CV uploaded successfully"
    
    def get_status(self, obj):
        return 'pending'
    
    class Meta:
        model = CV
        fields = ('message', 'cv_id', 'status')
        read_only_fields = ('message', 'cv_id', 'status')
