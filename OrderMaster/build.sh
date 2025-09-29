#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status.
set -o errexit

# Install all dependencies from requirements.txt
pip install -r requirements.txt

# Run collectstatic to gather all static files into STATIC_ROOT
python manage.py collectstatic --no-input

# Create new database migrations based on model changes
python manage.py makemigrations OrderMaster

# Apply all database migrations
python manage.py migrate
