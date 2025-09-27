# OrderMaster/OrderMaster/migrations/0002_vlhadmin.py

from django.db import migrations, models
import django.utils.timezone
import bcrypt

def create_initial_admin(apps, schema_editor):
    VlhAdmin = apps.get_model('OrderMaster', 'VlhAdmin')
    mobile = "9999999999"
    password = "admin"
    
    # Check if admin already exists
    if not VlhAdmin.objects.filter(mobile=mobile).exists():
        # Hash the password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        VlhAdmin.objects.create(
            mobile=mobile,
            password_hash=hashed_password.decode('utf-8')
        )

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
        migrations.RunPython(create_initial_admin),
    ]
