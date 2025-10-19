# OrderMaster/forms.py

from django import forms
from .models import MenuItem

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        # --- ADDED: 'image_url' to the fields list ---
        fields = ['item_name', 'description', 'price', 'category', 'veg_nonveg', 'meal_type', 'availability_time', 'image_url']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Chicken Biryani'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'A short description of the item'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 250.00'}),
            'category': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('Main Course', 'Main Course'),
                ('Starters', 'Starters'),
                ('Beverages', 'Beverages'),
                ('Desserts', 'Desserts'),
            ]),
            'veg_nonveg': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('Veg', 'Veg'),
                ('Non-Veg', 'Non-Veg'),
                ('Contains Egg', 'Contains Egg'),
            ]),
            'meal_type': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('Breakfast', 'Breakfast'),
                ('Lunch', 'Lunch'),
                ('Dinner', 'Dinner'),
                ('All Day', 'All Day'),
            ]),
            'availability_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 12 PM - 10 PM'}),
            # --- ADDED: Widget for the new image_url field ---
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/image.jpg'}),
        }
