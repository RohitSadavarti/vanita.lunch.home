# THIS IS THE CORRECT CODE
# OrderMaster/forms.py

from django import forms
from .models import MenuItem

class MenuItemForm(forms.ModelForm):
    # --- ADD THIS LINE ---
    # Explicitly define the price field to override localization
    price = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        localize=False,  # <-- This is the important fix
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': 'e.g., 250.00',
            'step': '0.01'
        })
    )

    class Meta:
        model = MenuItem
        fields = ['item_name', 'description', 'price', 'category', 'veg_nonveg', 'meal_type', 'availability_time', 'image_url']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Chicken Biryani'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'A short description of the item'}),
            
            # --- REMOVE THIS WIDGET DEFINITION FOR 'price' ---
            # 'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 250.00'}),
            
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
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/image.jpg'}),
        }
