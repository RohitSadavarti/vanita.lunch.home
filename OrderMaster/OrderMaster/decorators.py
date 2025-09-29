# OrderMaster/decorators.py

from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    """
    Decorator that checks if a user is authenticated in the session.
    Redirects to the login page if not authenticated.
    """
    def wrapper(request, *args, **kwargs):
        # Check if 'is_authenticated' is True in the session
        if not request.session.get('is_authenticated'):
            messages.warning(request, 'You must be logged in to view this page.')
            return redirect('login')
        # If authenticated, proceed with the original view function
        return view_func(request, *args, **kwargs)
    return wrapper
