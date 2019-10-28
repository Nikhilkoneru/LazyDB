"""
WSGI config for cloudbackend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""
#!/usr/bin/python3
import os,sys
from django.core.wsgi import get_wsgi_application
sys.path.append('/var/www/html/LazyDB/cloudbackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cloudbackend.settings')

application = get_wsgi_application()
