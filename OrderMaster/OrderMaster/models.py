# OrderMaster/models.py
from django.db import models
from django.utils import timezone
import bcrypt
import random
import pytz

def get_ist_now():
    """Returns current time in IST (Asia/Kolkata) timezone"""
    ist_tz = pytz.timezone('Asia/Kolkata')
    return timezone.now().astimezone(ist_tz)

class MenuItem(models.Model):
    # ... All MenuItem fields ...
    item_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50)
    veg_nonveg = models.CharField(max_length=20)
    meal_type = models.CharField(max_length=50)
    availability_time = models.CharField(max_length=100, blank=True, null=True)
    image_url = models.URLField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(default=get_ist_now)

    def __str__(self):
        return self.item_name

    class Meta:
        db_table = 'menu_items'


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Preparing', 'Preparing'),
        ('Ready', 'Ready'), ('Completed', 'Completed'), ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]
    order_id = models.CharField(max_length=50, unique=True, blank=True, null=True) # Needs unique=True, null=True
    customer_name = models.CharField(max_length=200)
    customer_mobile = models.CharField(max_length=15)
    items = models.JSONField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=50)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=get_ist_now)
    updated_at = models.DateTimeField(default=get_ist_now)
    order_status = models.CharField(max_length=50, default='open')
    ready_time = models.DateTimeField(blank=True, null=True)
    pickup_time = models.DateTimeField(blank=True, null=True)
    order_placed_by = models.CharField(
        max_length=10,
        choices=[('customer', 'Customer'), ('counter', 'Counter')],
        default='customer'
    )

    # NO CUSTOM SAVE METHOD HERE

    def __str__(self):
        display_id = self.order_id if self.order_id else f"(PK:{self.pk})"
        return f"Order {display_id} - {self.customer_name}"

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']


class VlhAdmin(models.Model):
    # ... VlhAdmin fields and methods ...
    mobile = models.CharField(max_length=10, unique=True)
    password_hash = models.TextField()
    created_at = models.DateTimeField(default=get_ist_now)

    class Meta:
        db_table = 'vlh_admin'

    def set_password(self, raw_password):
        self.password_hash = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, raw_password):
        if self.password_hash:
             return bcrypt.checkpw(raw_password.encode('utf-8'), self.password_hash.encode('utf-8'))
        return False

    def __str__(self):
        return self.mobile
