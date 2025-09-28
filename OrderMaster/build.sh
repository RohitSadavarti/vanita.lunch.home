#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Create and apply database migrations for the OrderMaster app
python manage.py makemigrations OrderMaster
python manage.py migrate
