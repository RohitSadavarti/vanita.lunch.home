# Create this as: OrderMaster/OrderMaster/migrations/0002_vlhadmin.py

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('OrderMaster', '0001_initial'),
    ]

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
