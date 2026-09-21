# crops/ocr_processor.py
import pytesseract
import cv2
import numpy as np
from PIL import Image
import fitz  # PyMuPDF
import re
import json
import logging
import io  # Missing import
from langdetect import detect
from django.conf import settings
import os

logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self):
        # Set Tesseract path if specified in settings
        if hasattr(settings, 'TESSERACT_CMD'):
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
    def process_file(self, file_path):
        """
        Process uploaded file (image or PDF) and extract text
        Returns: (extracted_text, detected_language, confidence)
        """
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                return self._process_pdf(file_path)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                return self._process_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            logger.error(f"OCR processing error: {str(e)}")
            raise
    
    def _process_pdf(self, file_path):
        """Extract text from PDF file"""
        text_content = ""
        doc = fitz.open(file_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Try text extraction first
            page_text = page.get_text()
            if page_text.strip():
                text_content += page_text + "\n"
            else:
                # If no text, convert page to image and use OCR
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                ocr_text = self._ocr_image(image)
                text_content += ocr_text + "\n"
        
        doc.close()
        
        # Detect language
        try:
            detected_lang = detect(text_content) if text_content.strip() else 'en'
        except:
            detected_lang = 'en'
        
        return text_content, detected_lang, None
    
    def _process_image(self, file_path):
        """Extract text from image file using OCR"""
        # Load and preprocess image
        image = cv2.imread(file_path)
        processed_image = self._preprocess_image(image)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(processed_image)
        
        # Perform OCR
        extracted_text = self._ocr_image(pil_image)
        
        # Detect language
        try:
            detected_lang = detect(extracted_text) if extracted_text.strip() else 'en'
        except:
            detected_lang = 'en'
        
        return extracted_text, detected_lang, None
    
    def _preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply thresholding to get binary image
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return processed
    
    def _ocr_image(self, image):
        """Perform OCR on PIL Image"""
        # Configure OCR for multiple languages
        lang_config = '+'.join(settings.OCR_LANGUAGES) if hasattr(settings, 'OCR_LANGUAGES') else 'eng'
        
        # OCR configuration
        custom_config = f'--oem 3 --psm 6 -l {lang_config}'
        
        # Extract text
        text = pytesseract.image_to_string(image, config=custom_config)
        
        return text
    
    def extract_crop_data(self, text, language='en'):
        """
        Extract crop-related numerical data from text
        Returns: dict with extracted values
        """
        extracted_data = {
            'nitrogen': None,
            'phosphorus': None,
            'potassium': None,
            'temperature': None,
            'humidity': None,
            'ph_level': None,
            'rainfall': None
        }
        
        # La détection de langue est peu fiable sur un texte court et surtout numérique :
        # on essaie d'abord la langue détectée, puis les autres pour les champs restants.
        languages = [language] + [lang for lang in ('en', 'fr', 'ar') if lang != language]
        for lang in languages:
            patterns = self._get_extraction_patterns(lang)
            normalized = self._normalize_text(text, lang)
            for field, field_patterns in patterns.items():
                if extracted_data[field] is not None:
                    continue
                for pattern in field_patterns:
                    for match in re.finditer(pattern, normalized, re.IGNORECASE | re.MULTILINE):
                        try:
                            value = float(match.group(1))
                        except (ValueError, IndexError):
                            continue
                        if self._validate_value(field, value):
                            extracted_data[field] = value
                            break
                    if extracted_data[field] is not None:
                        break

        return extracted_data
    
    def _get_extraction_patterns(self, language):
        """Get regex patterns for different languages"""
        patterns = {
            'en': {
                'nitrogen': [
                    r'nitrogen[:\s]*(\d+\.?\d*)',
                    r'n[:\s]*(\d+\.?\d*)',
                    r'n\s*=\s*(\d+\.?\d*)',
                ],
                'phosphorus': [
                    r'phosphorus[:\s]*(\d+\.?\d*)',
                    r'p[:\s]*(\d+\.?\d*)',
                    r'p\s*=\s*(\d+\.?\d*)',
                ],
                'potassium': [
                    r'potassium[:\s]*(\d+\.?\d*)',
                    r'k[:\s]*(\d+\.?\d*)',
                    r'k\s*=\s*(\d+\.?\d*)',
                ],
                'temperature': [
                    r'temperature[:\s]*(\d+\.?\d*)',
                    r'temp[:\s]*(\d+\.?\d*)',
                    r'°c[:\s]*(\d+\.?\d*)',
                ],
                'humidity': [
                    r'humidity[:\s]*(\d+\.?\d*)',
                    r'humid[:\s]*(\d+\.?\d*)',
                    r'%\s*humidity[:\s]*(\d+\.?\d*)',
                ],
                'ph_level': [
                    r'ph[:\s]*(\d+\.?\d*)',
                    r'ph\s*level[:\s]*(\d+\.?\d*)',
                    r'acidity[:\s]*(\d+\.?\d*)',
                ],
                'rainfall': [
                    r'rainfall[:\s]*(\d+\.?\d*)',
                    r'rain[:\s]*(\d+\.?\d*)',
                    r'precipitation[:\s]*(\d+\.?\d*)',
                ]
            },
            'fr': {
                'nitrogen': [
                    r'azote[:\s]*(\d+\.?\d*)',
                    r'n[:\s]*(\d+\.?\d*)',
                    r'nitrogène[:\s]*(\d+\.?\d*)',
                ],
                'phosphorus': [
                    r'phosphore[:\s]*(\d+\.?\d*)',
                    r'p[:\s]*(\d+\.?\d*)',
                ],
                'potassium': [
                    r'potassium[:\s]*(\d+\.?\d*)',
                    r'k[:\s]*(\d+\.?\d*)',
                    r'potasse[:\s]*(\d+\.?\d*)',
                ],
                'temperature': [
                    r'température[:\s]*(\d+\.?\d*)',
                    r'temp[:\s]*(\d+\.?\d*)',
                    r'°c[:\s]*(\d+\.?\d*)',
                ],
                'humidity': [
                    r'humidité[:\s]*(\d+\.?\d*)',
                    r'humid[:\s]*(\d+\.?\d*)',
                ],
                'ph_level': [
                    r'ph[:\s]*(\d+\.?\d*)',
                    r'acidité[:\s]*(\d+\.?\d*)',
                ],
                'rainfall': [
                    r'pluie[:\s]*(\d+\.?\d*)',
                    r'précipitation[:\s]*(\d+\.?\d*)',
                    r'pluviométrie[:\s]*(\d+\.?\d*)',
                ]
            },
            'ar': {
                'nitrogen': [
                    r'نيتروجين[:\s]*(\d+\.?\d*)',
                    r'ن[:\s]*(\d+\.?\d*)',
                    r'آزوت[:\s]*(\d+\.?\d*)',
                ],
                'phosphorus': [
                    r'فوسفور[:\s]*(\d+\.?\d*)',
                    r'ف[:\s]*(\d+\.?\d*)',
                ],
                'potassium': [
                    r'بوتاسيوم[:\s]*(\d+\.?\d*)',
                    r'ب[:\s]*(\d+\.?\d*)',
                ],
                'temperature': [
                    r'درجة\s*الحرارة[:\s]*(\d+\.?\d*)',
                    r'حرارة[:\s]*(\d+\.?\d*)',
                    r'°م[:\s]*(\d+\.?\d*)',
                ],
                'humidity': [
                    r'رطوبة[:\s]*(\d+\.?\d*)',
                    r'نسبة\s*الرطوبة[:\s]*(\d+\.?\d*)',
                ],
                'ph_level': [
                    r'حموضة[:\s]*(\d+\.?\d*)',
                    r'درجة\s*الحموضة[:\s]*(\d+\.?\d*)',
                ],
                'rainfall': [
                    r'أمطار[:\s]*(\d+\.?\d*)',
                    r'هطول[:\s]*(\d+\.?\d*)',
                    r'تساقط[:\s]*(\d+\.?\d*)',
                ]
            }
        }
        
        # Return patterns for the specified language, fallback to English
        return patterns.get(language, patterns['en'])
    
    def _normalize_text(self, text, language):
        """Normalize text for better pattern matching"""
        # Convert to lowercase for non-Arabic text
        if language != 'ar':
            text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Replace common separators
        text = text.replace(':', ' : ').replace('=', ' = ')
        
        return text
    
    def _validate_value(self, field, value):
        """Validate extracted values are within reasonable ranges"""
        ranges = {
            'nitrogen': (0, 300),
            'phosphorus': (0, 200),
            'potassium': (0, 400),
            'temperature': (-20, 60),
            'humidity': (0, 100),
            'ph_level': (0, 14),
            'rainfall': (0, 2000)
        }
        
        if field in ranges:
            min_val, max_val = ranges[field]
            return min_val <= value <= max_val
        
        return True