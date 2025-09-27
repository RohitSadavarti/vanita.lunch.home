# Step 1: Delete any existing 0002_*.py migration files in OrderMaster/OrderMaster/migrations/

# Step 2: Create this file as OrderMaster/OrderMaster/migrations/0002_register_vlhadmin.py

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('OrderMaster', '0001_initial'),
    ]

    # This migration tells Django about the existing vlh_admin table
    # without trying to create it again
    operations = [
        migrations.CreateModel(
            name='VlhAdmin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mobile', models.CharField(max_length=10, unique=True)),
                ('password_hash', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'vlh_admin',
            },
        ),
    ]

# Step 3: Run this command to fake-apply this migration:
# python manage.py migrate OrderMaster --fake
