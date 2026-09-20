# crops/ml_predictor.py
import joblib
import numpy as np
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CropPredictor:
    _instance = None
    _model = None
    _label_encoder = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_models()
        return cls._instance
    
    def _load_models(self):
        try:
            model_path = settings.CROP_MODEL_FILE
            encoder_path = settings.LABEL_ENCODER_FILE
            
            if os.path.exists(model_path) and os.path.exists(encoder_path):
                self._model = joblib.load(model_path)
                self._label_encoder = joblib.load(encoder_path)
                logger.info("ML models loaded successfully")
            else:
                logger.error("Model files not found")
                raise FileNotFoundError("ML model files not found")
                
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            self._model = None
            self._label_encoder = None
    
    def predict(self, features):
        """
        Predict crop based on input features
        features: [N, P, K, temperature, humidity, ph, rainfall]
        Returns: (predicted_crop, confidence_score)
        """
        if self._model is None or self._label_encoder is None:
            raise ValueError("Models not loaded properly")
        
        try:
            # Prepare input data
            X_new = np.array([features])
            
            # Get prediction
            prediction = self._model.predict(X_new)[0]
            
            # Get prediction probabilities for confidence score
            if hasattr(self._model, 'predict_proba'):
                proba = self._model.predict_proba(X_new)[0]
                confidence = float(np.max(proba))
            else:
                confidence = None
            
            # Convert prediction back to crop name
            crop_name = self._label_encoder.inverse_transform([prediction])[0]
            
            return crop_name, confidence
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise ValueError(f"Prediction failed: {str(e)}")
    
    def is_loaded(self):
        return self._model is not None and self._label_encoder is not None