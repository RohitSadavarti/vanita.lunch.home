# OrderMaster/models.py

from django.db import models
from django.utils import timezone
import bcrypt
import random
# Removed json import as it's not needed directly in models after correction
# Removed all view-related imports and function definitions

class MenuItem(models.Model):
    item_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50)
    veg_nonveg = models.CharField(max_length=20)
    meal_type = models.CharField(max_length=50)
    availability_time = models.CharField(max_length=100, blank=True, null=True)
    image_url = models.URLField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.item_name

    class Meta:
        db_table = 'menu_items'


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Preparing', 'Preparing'),
        ('Ready', 'Ready'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]
    order_id = models.CharField(max_length=50, unique=True, blank=True)
    customer_name = models.CharField(max_length=200)
    customer_mobile = models.CharField(max_length=15)
    items = models.JSONField() # Stores list of items as JSON
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending') # Customer-facing status
    payment_method = models.CharField(max_length=50)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    order_status = models.CharField(max_length=50, default='open') # Internal kitchen status: 'open', 'ready', 'pickedup', 'cancelled'
    ready_time = models.DateTimeField(blank=True, null=True)
    pickup_time = models.DateTimeField(blank=True, null=True)
    order_placed_by = models.CharField(
        max_length=10,
        choices=[('customer', 'Customer'), ('counter', 'Counter')],
        default='customer'
    )

    def save(self, *args, **kwargs):
        if not self.order_id:
            # Generate a unique order ID
            timestamp = timezone.now().strftime('%y%m%d%H%M%S')
            random_part = random.randint(100, 999)
            self.order_id = f"VLH-{timestamp}-{random_part}" # Added prefix
        super(Order, self).save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_id} - {self.customer_name}"

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']


class VlhAdmin(models.Model):
    mobile = models.CharField(max_length=10, unique=True)
    password_hash = models.TextField() # Store hashed password
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'vlh_admin' # Explicit table name

    def set_password(self, raw_password):
        # Hash the password using bcrypt
        self.password_hash = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, raw_password):
        # Check if the provided password matches the hash
        if self.password_hash:
             return bcrypt.checkpw(raw_password.encode('utf-8'), self.password_hash.encode('utf-8'))
        return False # No hash stored means password cannot be checked

    def __str__(self):
        return self.mobile
