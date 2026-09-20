# crops/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import logging
import os

from .forms import CropPredictionForm, OCRUploadForm
from .models import CropPrediction, OCRExtraction
from .ml_predictor import CropPredictor
from .ocr_processor import OCRProcessor

logger = logging.getLogger(__name__)

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def welcome(request):
    return render(request, 'crops/welcome.html')

def index(request):
    """Main page with prediction form and OCR upload"""
    form = CropPredictionForm()
    ocr_form = OCRUploadForm()
    
    # Get recent predictions for display
    recent_predictions = CropPrediction.objects.all()[:5]
    
    context = {
        'form': form,
        'ocr_form': ocr_form,
        'recent_predictions': recent_predictions,
    }
    
    return render(request, 'crops/index.html', context)

def predict_crop(request):
    """Handle crop prediction"""
    if request.method == 'POST':
        form = CropPredictionForm(request.POST)
        
        if form.is_valid():
            try:
                # Get predictor instance
                predictor = CropPredictor()
                
                if not predictor.is_loaded():
                    messages.error(request, _('ML models are not loaded. Please contact administrator.'))
                    return redirect('crops:index')
                
                # Extract features
                features = [
                    form.cleaned_data['nitrogen'],
                    form.cleaned_data['phosphorus'],
                    form.cleaned_data['potassium'],
                    form.cleaned_data['temperature'],
                    form.cleaned_data['humidity'],
                    form.cleaned_data['ph_level'],
                    form.cleaned_data['rainfall'],
                ]
                
                # Make prediction
                crop_name, confidence = predictor.predict(features)
                
                # Save prediction to database
                prediction = CropPrediction.objects.create(
                    nitrogen=form.cleaned_data['nitrogen'],
                    phosphorus=form.cleaned_data['phosphorus'],
                    potassium=form.cleaned_data['potassium'],
                    temperature=form.cleaned_data['temperature'],
                    humidity=form.cleaned_data['humidity'],
                    ph_level=form.cleaned_data['ph_level'],
                    rainfall=form.cleaned_data['rainfall'],
                    recommended_crop=crop_name,
                    confidence_score=confidence,
                    source_type='manual',
                    ip_address=get_client_ip(request)
                )
                
                # Success message
                confidence_text = f" (Confidence: {confidence:.2%})" if confidence else ""
                messages.success(
                    request, 
                    _('Recommended crop: %(crop)s%(confidence)s') % {
                        'crop': crop_name.title(),
                        'confidence': confidence_text
                    }
                )
                
                # For AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'crop': crop_name,
                        'confidence': confidence,
                        'prediction_id': prediction.id
                    })
                
            except Exception as e:
                logger.error(f"Prediction error: {str(e)}")
                error_msg = _('Prediction failed: %(error)s') % {'error': str(e)}
                messages.error(request, error_msg)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    })
        else:
            # Form validation errors
            error_msg = _('Please correct the form errors.')
            messages.error(request, error_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg,
                    'form_errors': form.errors
                })
    
    return redirect('crops:index')

def ocr_upload(request):
    """Handle OCR file upload and processing"""
    if request.method == 'POST':
        form = OCRUploadForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                uploaded_file = form.cleaned_data['file']
                ocr_language = form.cleaned_data['ocr_language']

                # Save uploaded file temporarily
                file_path = default_storage.save(
                    f'temp/{uploaded_file.name}',
                    ContentFile(uploaded_file.read())
                )
                full_path = default_storage.path(file_path)

                # Process with OCR
                processor = OCRProcessor()
                extracted_text, detected_lang, confidence = processor.process_file(full_path)

                # Use detected language if auto-detect was selected
                if ocr_language == 'auto':
                    ocr_language = detected_lang

                # Extract crop data
                extracted_data = processor.extract_crop_data(extracted_text, ocr_language)

                # Save OCR extraction record
                ocr_extraction = OCRExtraction.objects.create(
                    uploaded_file=uploaded_file,
                    extracted_text=extracted_text,
                    detected_language=detected_lang,
                    extraction_confidence=confidence,
                    extracted_data=extracted_data,
                    success=any(v is not None for v in extracted_data.values())
                )

                # Clean up temporary file
                try:
                    default_storage.delete(file_path)
                except:
                    pass

                # Return extracted data
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'extracted_data': extracted_data,
                        'detected_language': detected_lang,
                        'extraction_id': ocr_extraction.id,
                        'message': _('Data extracted successfully!')
                    })
                else:
                    messages.success(request, _('File processed successfully!'))
                    return redirect('crops:extract_data')

            except Exception as e:
                logger.error(f"OCR processing error: {str(e)}")
                error_msg = _('OCR processing failed: %(error)s') % {'error': str(e)}

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    })
                else:
                    messages.error(request, error_msg)
                    form = OCRUploadForm()  # réinitialise formulaire vierge
                    return render(request, 'crops/ocr_upload.html', {'form': form})

        else:
            error_msg = _('Please correct the form errors.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg,
                    'form_errors': form.errors
                })
            else:
                messages.error(request, error_msg)
                return render(request, 'crops/ocr_upload.html', {'form': form})

    # GET request: afficher le formulaire vide
    form = OCRUploadForm()
    return render(request, 'crops/ocr_upload.html', {'form': form})


def extract_data(request):
    """Show extracted data and allow editing before prediction"""
    # Get the latest OCR extraction for this session
    latest_extraction = OCRExtraction.objects.filter(success=True).first()
    
    form = CropPredictionForm()
    
    # Pre-fill form with extracted data if available
    if latest_extraction and latest_extraction.extracted_data:
        initial_data = {}
        for field, value in latest_extraction.extracted_data.items():
            if value is not None:
                initial_data[field] = value
        
        form = CropPredictionForm(initial=initial_data)
    
    context = {
        'form': form,
        'extraction': latest_extraction,
        'show_extraction': True
    }
    
    return render(request, 'crops/extract_data.html', context)

def prediction_history(request):
    """Afficher l'historique des prédictions faites depuis cette adresse IP"""
    client_ip = get_client_ip(request)

    # Filtrer les prédictions correspondant à cette adresse IP
    predictions = CropPrediction.objects.filter(ip_address=client_ip).order_by('-id')
    
    # Pagination
    paginator = Paginator(predictions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'predictions': page_obj,
    }
    
    return render(request, 'crops/history.html', context)
