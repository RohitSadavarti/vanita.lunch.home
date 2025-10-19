#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
# Remove potentially conflicting old migration history for the OrderMaster app
rm -rf OrderMaster/OrderMaster/migrations/
mkdir -p OrderMaster/OrderMaster/migrations/
touch OrderMaster/OrderMaster/migrations/__init__.py

# Now create and apply fresh migrations
python manage.py makemigrations OrderMaster
python manage.py migrate
echo "Building React frontend..."
cd OrderMaster/frontend
npm install
npm run build
cd ../.. 


