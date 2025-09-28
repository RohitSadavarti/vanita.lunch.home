# OrderMaster/models.py

from django.db import models
from django.utils import timezone
import bcrypt

class MenuItem(models.Model):
    item_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=20)
    veg_nonveg = models.CharField(max_length=10)
    meal_type = models.CharField(max_length=20)
    availability_time = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.item_name
    class Meta:
        db_table = 'menu_items'


class Order(models.Model):
    order_id = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200)
    customer_mobile = models.CharField(max_length=15) # Added from your SQL
    items = models.JSONField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2) # Added from your SQL
    discount = models.DecimalField(max_digits=10, decimal_places=2) # Added from your SQL
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='confirmed')
    payment_method = models.CharField(max_length=50, default='Cash') # Added from your SQL
    payment_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True) # Added from your SQL
    order_status = models.CharField(max_length=20, default='open') # Added from your SQL
    # The 'ready_time' field has been removed as it does not exist in your SQL table.

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
