import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Sécurisé par défaut : le mode debug se règle par variable d'environnement (DJANGO_DEBUG=1).
DEBUG = os.environ.get('DJANGO_DEBUG', '0') == '1'
# Sans clé fournie, une clé aléatoire est générée à chaque démarrage (les sessions ne survivent pas à un redémarrage).
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or ('dev-only-insecure-key' if DEBUG else secrets.token_urlsafe(50))
ALLOWED_HOSTS = [h for h in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1],testserver').split(',') if h]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crops',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # fichiers statiques hors mode debug
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Pour la traduction
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'crop_recommendation.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'crop_recommendation.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

STATIC_URL = '/static/'
STATICFILES_DIRS = [d for d in [BASE_DIR / 'static'] if d.exists()]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ML Model paths
ML_MODEL_PATH = BASE_DIR / 'ml_models'
CROP_MODEL_FILE = ML_MODEL_PATH / 'crop_recommendation_model.joblib'
LABEL_ENCODER_FILE = ML_MODEL_PATH / 'label_encoder.joblib'

# Internationalization
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
    ('fr', 'Français'),
    ('ar', 'العربية'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# OCR Configuration
# Chemin de Tesseract : variable TESSERACT_CMD, sinon l'exécutable trouvé dans le PATH,
# sinon l'emplacement Linux habituel.
import shutil
TESSERACT_CMD = os.environ.get('TESSERACT_CMD') or shutil.which('tesseract') or '/usr/bin/tesseract'
OCR_LANGUAGES = ['eng', 'fra', 'ara']
