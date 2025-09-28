# OrderMaster/forms.py

from django import forms
from .models import MenuItem

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            'item_name',
            'description',
            'price',
            'category',
            'veg_nonveg',
            'meal_type',
            'availability_time',
            'image',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
