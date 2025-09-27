"""
Django settings for vanita_lunch project.
"""
import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-b9j01@*vxpl=+zr2@3uq)*=0&o7q7&t1cncn9en*(atpb+9*8o')

# SECURITY WARNING: don't run with debug turned on in production!
# Render will automatically set DEBUG to False.
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS is configured to work with Render's deployment environment.
ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'OrderMaster',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Whitenoise for serving static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vanita_lunch.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # It's good practice to have a project-level templates directory
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


# ==============================================================================
# DATABASE CONFIGURATION (Corrected for Render)
# ==============================================================================
# This configuration uses dj-database-url to parse the DATABASE_URL 
# environment variable provided by Render. This is the recommended approach.
# The 'default' value is a fallback for local development if DATABASE_URL is not set.
DATABASES = {
    'default': dj_database_url.config(
        # The DATABASE_URL environment variable will be used automatically in production.
        # This default value is used for local development or as a fallback.
        default='postgresql://postgres.avqpzwgdylnklbkyqukp:asBjLmDfKfoZPVt9@aws-0-ap-south-1.pooler.supabase.com:6543/postgres',
        conn_max_age=600 # Keeps database connections alive for 10 minutes
    )
}

# ==============================================================================

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
# This tells Django to put all collected static files into a directory named 'staticfiles'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# This tells Django where to look for static files in your project
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Use Whitenoise to serve static files efficiently in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (user-uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URLs
LOGIN_URL = 'login' # Use the name of the URL pattern
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# CSRF Settings for production
# This automatically trusts the Render domain
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
]
# OrderMaster/vanita_lunch/settings.py

STATICFILES_DIRS = [BASE_DIR / "static"]

