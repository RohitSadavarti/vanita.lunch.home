# OrderMaster/vanita_lunch/settings.py

import os
from pathlib import Path
import dj_database_url
from decouple import config

# --- CORE PATHS ---
# This defines the base directory of your Django project.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SECURITY SETTINGS ---
# It's crucial to keep your secret key secure.
SECRET_KEY = config('SECRET_KEY')

# Debug should be False in a production environment.
DEBUG = config('DEBUG', default=False, cast=bool)

# Allows all host headers. For better security, you might want to restrict this.
ALLOWED_HOSTS = ['*']

# --- INSTALLED APPS ---
# Defines all the Django applications that are activated in this project.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'OrderMaster',  # Your primary application
]

# --- MIDDLEWARE ---
# Hooks into Django's request/response processing.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For serving static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# --- URLS ---
# The root URL configuration for your project.
ROOT_URLCONF = 'vanita_lunch.urls'

# --- TEMPLATES ---
# Configuration for Django's template engine.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # This path is now corrected to point to your app's templates directory.
        'DIRS': [os.path.join(BASE_DIR, 'OrderMaster/templates')],
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

# --- WSGI ---
# The entry-point for WSGI-compatible web servers to serve your project.
WSGI_APPLICATION = 'vanita_lunch.wsgi.application'

# --- DATABASE ---
# Configured to use dj_database_url to parse the DATABASE_URL environment variable.
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL')
    )
}

# --- PASSWORD VALIDATION ---
# Helps ensure that users choose strong passwords.
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- INTERNATIONALIZATION ---
# Language, time zone, and other localization settings.
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- STATIC FILES (CSS, JAVASCRIPT, IMAGES) ---
# This is the section that was causing the most significant issues.

STATIC_URL = '/static/'

# This is the corrected path where Django will look for your static files.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'OrderMaster/static'),
]

# This is where Django will collect all static files for production.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Using WhiteNoise for efficient static file serving.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- MISCELLANEOUS ---
# Default primary key field type.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
