"""
ASGI config for bitnile_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

import sys

try:
    from django.core.asgi import get_asgi_application
except ImportError:
    print("Django is not installed. Please install Django to run this application.")
    sys.exit(1)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitnile_backend.settings')

application = get_asgi_application()
