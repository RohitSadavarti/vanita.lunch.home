# OrderMaster/models.py

from django.db import models
from django.utils import timezone
import bcrypt
import random

class MenuItem(models.Model):
    item_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50)
    veg_nonveg = models.CharField(max_length=20)
    meal_type = models.CharField(max_length=50)
    availability_time = models.CharField(max_length=100, blank=True, null=True)
    # --- ADDED: New field for the image URL ---
    image_url = models.URLField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.item_name
    class Meta:
        db_table = 'menu_items'

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),  # Added
        ('Preparing', 'Preparing'),
        ('Ready', 'Ready'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),    # Added
        ('Cancelled', 'Cancelled'),
    ]
    order_id = models.CharField(max_length=50, unique=True, blank=True)
    customer_name = models.CharField(max_length=200)
    customer_mobile = models.CharField(max_length=15)
    items = models.JSONField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending') # Updated
    payment_method = models.CharField(max_length=50)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    order_status = models.CharField(max_length=50, default='open')
    ready_time = models.DateTimeField(blank=True, null=True)
    pickup_time = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = str(random.randint(10000000, 99999999))
        super(Order, self).save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_id} - {self.customer_name}"
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']


class VlhAdmin(models.Model):
    mobile = models.CharField(max_length=10, unique=True)
    password_hash = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    class Meta:
        db_table = 'vlh_admin'
    def set_password(self, raw_password):
        self.password_hash = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    def check_password(self, raw_password):
        return bcrypt.checkpw(raw_password.encode('utf-8'), self.password_hash.encode('utf-8'))
    def __str__(self):
        return self.mobile


