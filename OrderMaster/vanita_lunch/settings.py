# OrderMaster/vanita_lunch/settings.py

import os
from pathlib import Path
import dj_database_url
from decouple import config

# This is the correct BASE_DIR for your project structure.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security Settings ---
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = ['*']

# --- Application Definition ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',  # Handles static files in development
    'django.contrib.staticfiles',
    'OrderMaster',
]

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Serves static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vanita_lunch.urls'

# --- Templates ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Correctly points to your app's templates folder
        'DIRS': [os.path.join(BASE_DIR, 'OrderMaster', 'templates')],
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

WSGI_APPLICATION = 'vanita_lunch.wsgi.application'

# --- Database ---
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL')
    )
}

# --- Password Validation ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internationalization ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Static Files (THE FINAL CORRECTION) ---
STATIC_URL = '/static/'

# This is the single most important line to fix. It tells Django where to find your CSS, JS, and vendor files.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'OrderMaster', 'static'),
]

# This is where 'collectstatic' will copy all files for production.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# The storage engine that handles compression and caching.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# --- Default Primary Key ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
