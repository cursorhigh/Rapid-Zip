from django.contrib import admin
from .models import CompressionRecord

@admin.register(CompressionRecord)
class CompressionRecordAdmin(admin.ModelAdmin):
    list_display = ('original_name', 'quality', 'down', 'compression_ratio', 'created_at')
    search_fields = ('original_name', 'file_hash')
    list_filter = ('quality', 'down', 'created_at')
