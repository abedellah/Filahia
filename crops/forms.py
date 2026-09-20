# crops/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
import os

class CropPredictionForm(forms.Form):
    nitrogen = forms.FloatField(
        label=_('Nitrogen (N)'),
        min_value=0,
        max_value=200,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter nitrogen content (0-200)'),
            'step': '0.1'
        })
    )
    
    phosphorus = forms.FloatField(
        label=_('Phosphorus (P)'),
        min_value=0,
        max_value=150,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter phosphorus content (0-150)'),
            'step': '0.1'
        })
    )
    
    potassium = forms.FloatField(
        label=_('Potassium (K)'),
        min_value=0,
        max_value=300,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter potassium content (0-300)'),
            'step': '0.1'
        })
    )
    
    temperature = forms.FloatField(
        label=_('Temperature (°C)'),
        min_value=-10,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter temperature in Celsius'),
            'step': '0.1'
        })
    )
    
    humidity = forms.FloatField(
        label=_('Humidity (%)'),
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter humidity percentage (0-100)'),
            'step': '0.1'
        })
    )
    
    ph_level = forms.FloatField(
        label=_('pH Level'),
        min_value=0,
        max_value=14,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter pH level (0-14)'),
            'step': '0.1'
        })
    )
    
    rainfall = forms.FloatField(
        label=_('Rainfall (mm)'),
        min_value=0,
        max_value=500,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter rainfall in mm'),
            'step': '0.1'
        })
    )

class OCRUploadForm(forms.Form):
    SUPPORTED_FORMATS = [
        ('image', _('Image (JPG, PNG, BMP, TIFF)')),
        ('pdf', _('PDF Document')),
    ]
    
    file = forms.FileField(
        label=_('Upload File'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.jpg,.jpeg,.png,.bmp,.tiff,.pdf',
        }),
        help_text=_('Supported formats: JPG, PNG, BMP, TIFF, PDF (Max size: 10MB)')
    )
    
    ocr_language = forms.ChoiceField(
        label=_('OCR Language'),
        choices=[
            ('auto', _('Auto-detect')),
            ('en', _('English')),
            ('fr', _('French')),
            ('ar', _('Arabic')),
        ],
        initial='auto',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(_('File size must be less than 10MB'))
            
            # Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf']
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(_('Unsupported file format'))
        
        return file
    from django import forms
from django.utils.translation import gettext_lazy as _

class CropPredictionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamic field configuration with translations
        field_configs = {
            'nitrogen': {
                'label': _('Nitrogen (N)'),
                'help_text': _('Nitrogen content in soil (ppm)'),
                'widget_attrs': {'placeholder': _('Enter nitrogen value')},
            },
            'phosphorus': {
                'label': _('Phosphorus (P)'),
                'help_text': _('Phosphorus content in soil (ppm)'),
                'widget_attrs': {'placeholder': _('Enter phosphorus value')},
            },
            'potassium': {
                'label': _('Potassium (K)'),
                'help_text': _('Potassium content in soil (ppm)'),
                'widget_attrs': {'placeholder': _('Enter potassium value')},
            },
            'ph_level': {
                'label': _('pH Level'),
                'help_text': _('Soil pH level (0-14)'),
                'widget_attrs': {'placeholder': _('Enter pH value')},
            },
            'temperature': {
                'label': _('Temperature (°C)'),
                'help_text': _('Average temperature in Celsius'),
                'widget_attrs': {'placeholder': _('Enter temperature')},
            },
            'humidity': {
                'label': _('Humidity (%)'),
                'help_text': _('Relative humidity percentage'),
                'widget_attrs': {'placeholder': _('Enter humidity')},
            },
            'rainfall': {
                'label': _('Rainfall (mm)'),
                'help_text': _('Annual rainfall in millimeters'),
                'widget_attrs': {'placeholder': _('Enter rainfall')},
            },
        }
        
        # Apply configurations to fields
        for field_name, config in field_configs.items():
            if field_name in self.fields:
                field = self.fields[field_name]
                field.label = config['label']
                if 'help_text' in config:
                    field.help_text = config['help_text']
                if 'widget_attrs' in config:
                    field.widget.attrs.update(config['widget_attrs'])
                    
                # Add CSS classes
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500'
                })

    nitrogen = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=0,
        max_value=1000
    )
    phosphorus = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=0,
        max_value=1000
    )
    potassium = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=0,
        max_value=1000
    )
    ph_level = forms.DecimalField(
        max_digits=4, 
        decimal_places=2,
        min_value=0,
        max_value=14
    )
    temperature = forms.DecimalField(
        max_digits=5, 
        decimal_places=2,
        min_value=-50,
        max_value=60
    )
    humidity = forms.DecimalField(
        max_digits=5, 
        decimal_places=2,
        min_value=0,
        max_value=100
    )
    rainfall = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=0,
        max_value=5000
    )