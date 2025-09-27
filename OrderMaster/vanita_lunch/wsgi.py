"""
WSGI config for vanita_lunch project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
import traceback

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanita_lunch.settings')

try:
    application = get_wsgi_application()
except Exception:
    # Print the full traceback to the console to see the real error
    print("!!! DJANGO FAILED TO START - TRACEBACK BELOW !!!", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    # Exit with a non-zero status code to indicate failure
    sys.exit(1)
