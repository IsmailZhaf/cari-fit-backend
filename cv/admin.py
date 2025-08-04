from django.contrib import admin
from .models import CV

@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('id', 'user_id')
    readonly_fields = ('id', 'uploaded_at')