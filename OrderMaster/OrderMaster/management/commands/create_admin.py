# Create this directory structure and file:
# OrderMaster/OrderMaster/management/__init__.py
# OrderMaster/OrderMaster/management/commands/__init__.py  
# OrderMaster/OrderMaster/management/commands/create_admin.py

import bcrypt
from django.core.management.base import BaseCommand
from OrderMaster.models import VlhAdmin


class Command(BaseCommand):
    help = 'Create admin user for VLH system'

    def add_arguments(self, parser):
        parser.add_argument('mobile', type=str, help='Mobile number (10 digits)')
        parser.add_argument('password', type=str, help='Password for admin')

    def handle(self, *args, **options):
        mobile = options['mobile']
        password = options['password']
        
        # Validate mobile number
        if not mobile.isdigit() or len(mobile) != 10:
            self.stdout.write(
                self.style.ERROR('Mobile number must be exactly 10 digits')
            )
            return
        
        # Check if admin already exists
        if VlhAdmin.objects.filter(mobile=mobile).exists():
            self.stdout.write(
                self.style.ERROR(f'Admin with mobile {mobile} already exists')
            )
            return
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create admin
        VlhAdmin.objects.create(
            mobile=mobile,
            password_hash=password_hash
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created admin user with mobile: {mobile}')
        )
