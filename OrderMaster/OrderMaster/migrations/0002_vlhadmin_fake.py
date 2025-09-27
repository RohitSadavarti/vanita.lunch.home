# Create this as: OrderMaster/OrderMaster/migrations/0002_vlhadmin_fake.py

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('OrderMaster', '0001_initial'),
    ]

    operations = [
        # This migration represents the existing vlh_admin table
        # We use a fake operation that doesn't actually create the table
        migrations.RunSQL(
            sql="SELECT 1;",  # Dummy SQL that does nothing
            reverse_sql="SELECT 1;",
            state_operations=[
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
        ),
    ]
