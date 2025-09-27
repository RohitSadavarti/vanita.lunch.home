#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate OrderMaster 0002_add_payment_id --fake
python manage.py migrate
