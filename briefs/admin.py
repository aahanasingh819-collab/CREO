from django.contrib import admin
from .models import Brief

@admin.register(Brief)
class BriefAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'status', 'deadline', 'source']
    list_filter = ['status', 'content_type', 'commercial_use']
    readonly_fields = ['source', 'created_at', 'updated_at']
