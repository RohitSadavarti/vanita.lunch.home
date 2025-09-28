pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --fake OrderMaster
python manage.py migrate
