"""
WSGI config for myshop project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')

application = get_wsgi_application()

try:
    from .management_hooks import create_live_admin
    create_live_admin()
except Exception as e:
    print(f"Hook failed to run: {e}")