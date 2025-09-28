# OrderMaster/models.py

from django.db import models
from django.utils import timezone
import bcrypt

class MenuItem(models.Model):
    # This model now matches your menu_items table exactly
    item_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50)
    veg_nonveg = models.CharField(max_length=20)
    meal_type = models.CharField(max_length=50)
    availability_time = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    # The 'image' field is not in your SQL file, so it's commented out.
    # If you want to add images later, you will need to add this column to your table.
    # image = models.ImageField(upload_to='menu_images/', blank=True, null=True)

    def __str__(self):
        return self.item_name

    class Meta:
        db_table = 'menu_items'


class Order(models.Model):
    # This model now matches your orders table exactly
    order_id = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200)
    customer_mobile = models.CharField(max_length=15)
    items = models.JSONField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50) # e.g., 'confirmed'
    payment_method = models.CharField(max_length=50)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    order_status = models.CharField(max_length=50, default='open') # e.g., 'open', 'ready', 'pickedup'

    def __str__(self):
        return f"Order {self.order_id} - {self.customer_name}"

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']


class VlhAdmin(models.Model):
    # This model now matches your vlh_admin table exactly
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
