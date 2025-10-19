# OrderMaster/OrderMaster/models.py
import bcrypt
from django.db import models
from django.utils import timezone


class MenuItem(models.Model):
    # Uses 'name', not 'item_name'. No 'category' field here unless you add a default.
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True) # Allow blank image

    # If you NEED a category, add it WITH a default, like this:
    # category = models.CharField(max_length=50, default='Uncategorized')

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Ready', 'Ready'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    order_id = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=100)
    items = models.JSONField()
    # Uses 'total_amount', not 'subtotal'
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(default=timezone.now)
    ready_time = models.DateTimeField(null=True, blank=True)
    payment_id = models.CharField(max_length=100, blank=True, default='COD')

    def __str__(self):
        return self.order_id

    class Meta:
        ordering = ['-created_at']


class VlhAdmin(models.Model):
    mobile = models.CharField(max_length=10, unique=True)
    password_hash = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def check_password(self, raw_password):
        return bcrypt.checkpw(raw_password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def __str__(self):
        return self.mobile