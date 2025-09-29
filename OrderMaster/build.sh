#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files into the STATIC_ROOT directory
python manage.py collectstatic --no-input

# Create database migrations for your models
python manage.py makemigrations OrderMaster

# Apply the migrations to the database
python manage.py migrate
