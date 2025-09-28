# OrderMaster/models.py

import bcrypt
import json
from django.db import models
from django.utils import timezone

class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snacks', 'Snacks'),
        ('beverages', 'Beverages'),
    ]
    VEG_CHOICES = [
        ('veg', 'Vegetarian'),
        ('non_veg', 'Non-Vegetarian'),
    ]
    MEAL_TYPE_CHOICES = [
        ('main_course', 'Main Course'),
        ('starter', 'Starter'),
        ('dessert', 'Dessert'),
        ('beverage', 'Beverage'),
    ]

    item_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    veg_nonveg = models.CharField(max_length=10, choices=VEG_CHOICES)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    availability_time = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.item_name

    class Meta:
        db_table = 'menu_items'


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Preparing', 'Preparing'),
        ('Ready', 'Ready'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    order_id = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200)
    items = models.JSONField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100, blank=True, default='COD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(default=timezone.now)
    ready_time = models.DateTimeField(blank=True, null=True)

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
