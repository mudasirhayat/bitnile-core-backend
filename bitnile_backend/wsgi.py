"""
import sys

def application(environ, start_response):
    status = '200 OK'
    output = b'Hello, World!'

    try:
        start_response(status, [('Content-type', 'text/plain')])
        return [
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitnile_backend.settings')

application = get_wsgi_application()
