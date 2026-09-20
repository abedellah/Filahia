
# crops/models.py
from django.db import models
from django.utils import timezone

class CropPrediction(models.Model):
    # Input features
    nitrogen = models.FloatField()
    phosphorus = models.FloatField()  
    potassium = models.FloatField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    ph_level = models.FloatField()
    rainfall = models.FloatField()
    
    # Prediction result
    recommended_crop = models.CharField(max_length=100)
    confidence_score = models.FloatField(null=True, blank=True)
    
    # OCR and source information
    source_type = models.CharField(
        max_length=20,
        choices=[('manual', 'Manual Entry'), ('ocr', 'OCR Extraction')],
        default='manual'
    )
    uploaded_file = models.FileField(upload_to='uploads/', null=True, blank=True)
    extracted_text = models.TextField(null=True, blank=True)
    language_detected = models.CharField(max_length=10, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recommended_crop} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class OCRExtraction(models.Model):
    """Store OCR extraction results for debugging and improvement"""
    uploaded_file = models.FileField(upload_to='ocr_files/')
    extracted_text = models.TextField()
    detected_language = models.CharField(max_length=10)
    extraction_confidence = models.FloatField(null=True, blank=True)
    extracted_data = models.JSONField(null=True, blank=True)  # Store parsed values
    success = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']