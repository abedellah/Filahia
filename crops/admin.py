from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CropPrediction, OCRExtraction

@admin.register(CropPrediction)
class CropPredictionAdmin(admin.ModelAdmin):
    list_display = ('recommended_crop', 'confidence_score', 'created_at')
    list_filter = ('created_at', 'source_type')
    search_fields = ('recommended_crop',)

@admin.register(OCRExtraction)
class OCRExtractionAdmin(admin.ModelAdmin):
    list_display = ('uploaded_file', 'detected_language', 'extraction_confidence', 'success', 'created_at')
    list_filter = ('success', 'detected_language', 'created_at')
    search_fields = ('extracted_text',)
