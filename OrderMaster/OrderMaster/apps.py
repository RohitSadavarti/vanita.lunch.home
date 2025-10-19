from django.apps import AppConfig

class OrdermasterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Correct the name to just the app's name
    name = 'OrderMaster'
