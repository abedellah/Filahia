# crops/urls.py
from django.urls import path
from . import views

app_name = 'crops'

urlpatterns = [
    # Main pages
    path('', views.welcome, name='welcome'),
    path('predict/', views.index, name='index'),
    path('welcome/', views.welcome, name='welcome'),
    
    # Prediction functionality
    path('predict-crop/', views.predict_crop, name='predict'),
    
    # OCR functionality
    path('ocr-upload/', views.ocr_upload, name='ocr_upload'),
    path('extract-data/', views.extract_data, name='extract_data'),
    
    # History
    path('history/', views.prediction_history, name='history'),
]