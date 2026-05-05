from .settings import *


DEBUG = False

if SECRET_KEY == 'dev-secret-key-change-me':
    raise RuntimeError('Define BAR_SECRET_KEY para usar bar.settings_prod.')

if ALLOWED_HOSTS == ['*']:
    raise RuntimeError('Define BAR_ALLOWED_HOSTS para usar bar.settings_prod.')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    *[middleware for middleware in MIDDLEWARE if middleware != 'django.middleware.security.SecurityMiddleware'],
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'