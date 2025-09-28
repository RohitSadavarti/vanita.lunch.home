# OrderMaster/forms.py

from django import forms
from .models import MenuItem

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        # The 'image' field has been removed from this list to match your model
        fields = [
            'item_name',
            'description',
            'price',
            'category',
            'veg_nonveg',
            'meal_type',
            'availability_time',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
