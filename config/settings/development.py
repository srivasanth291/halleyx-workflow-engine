"""
Development settings — extends base.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ['*']

# Additional development apps
INSTALLED_APPS += ['debug_toolbar']  # noqa: F405

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa: F405

INTERNAL_IPS = ['127.0.0.1', '::1']

# Development email — outputs to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS — allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Looser password validation for dev
AUTH_PASSWORD_VALIDATORS = []  # noqa: F405
