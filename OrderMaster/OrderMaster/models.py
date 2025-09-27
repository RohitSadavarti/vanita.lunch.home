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
    
    item_name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    veg_nonveg = models.CharField(max_length=10, choices=VEG_CHOICES)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    availability_time = models.CharField(max_length=100)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.item_name
    
    class Meta:
        db_table = 'menu_items'


class Order(models.Model):
    STATUS_CHOICES = [
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
    ]
    
    order_id = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200)
    items = models.TextField()  # JSON string of ordered items
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='preparing')
    order_time = models.DateTimeField(default=timezone.now)
    ready_time = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Order {self.order_id} - {self.customer_name}"
    
    class Meta:
        db_table = 'orders'
        ordering = ['-order_time']