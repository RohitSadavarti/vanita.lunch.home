#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py makemigrations
python manage.py migrate

echo "Building React frontend..."
cd OrderMaster/frontend
npm install
npm run build
cd ../.. 

