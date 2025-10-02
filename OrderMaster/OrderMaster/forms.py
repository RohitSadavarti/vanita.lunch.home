# OrderMaster/OrderMaster/forms.py
from django import forms
from .models import MenuItem, Order

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

# --- THIS IS THE CORRECTED PART ---
class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        # These fields now correctly match the fields in your models.py file
        fields = ['name', 'description', 'price', 'category', 'image', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
# ------------------------------------

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_status']
        widgets = {
            'order_status': forms.Select(attrs={'class': 'form-control'}),
        }
