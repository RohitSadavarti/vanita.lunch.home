# OrderMaster/models.py

from django.db import models
from django.utils import timezone
import bcrypt
import random
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    category = models.ForeignKey(Category, related_name='menu_items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('pickedup', 'Picked Up'),
        ('cancelled', 'Cancelled'),
    )
    
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    order_id = models.CharField(max_length=10, unique=True, blank=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True) # Keep this line
    
    # -- ADD THIS LINE --
    is_acknowledged = models.BooleanField(default=False)
    # -------------------

    def save(self, *args, **kwargs):
        if not self.order_id:
            last_order = Order.objects.all().order_by('id').last()
            if last_order:
                self.order_id = str(int(last_order.order_id) + 1)
            else:
                self.order_id = '1000'
        super(Order, self).save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_id} - {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} for Order {self.order.order_id}"

class BusinessSettings(models.Model):
    is_open = models.BooleanField(default=True)

    def __str__(self):
        return "Business Settings"
