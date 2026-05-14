from .settings import *


def env_list(name):
    value = os.environ.get(name, '')
    return [item.strip() for item in value.split(',') if item.strip()]


DEBUG = False

SECRET_KEY = os.environ.get('BAR_SECRET_KEY', '').strip()
if not SECRET_KEY:
    raise RuntimeError('Define BAR_SECRET_KEY para usar bar.settings_prod.')

ALLOWED_HOSTS = env_list('BAR_ALLOWED_HOSTS')
if not ALLOWED_HOSTS:
    raise RuntimeError('Define BAR_ALLOWED_HOSTS para usar bar.settings_prod.')

csrf_trusted_origins = env_list('BAR_CSRF_TRUSTED_ORIGINS')
if csrf_trusted_origins:
    CSRF_TRUSTED_ORIGINS = csrf_trusted_origins

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = env_bool('BAR_SECURE_SSL_REDIRECT', default=True)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    *[middleware for middleware in MIDDLEWARE if middleware != 'django.middleware.security.SecurityMiddleware'],
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
SESSION_COOKIE_SECURE = env_bool('BAR_SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env_bool('BAR_CSRF_COOKIE_SECURE', default=True)
SECURE_HSTS_SECONDS = int(os.environ.get('BAR_SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('BAR_SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env_bool('BAR_SECURE_HSTS_PRELOAD', default=True)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'