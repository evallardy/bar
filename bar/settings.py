import os


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}

SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 31536000
SESSION_SAVE_EVERY_REQUEST = True

EMAIL_BACKEND = os.environ.get('BAR_EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('BAR_EMAIL_HOST', 'sandbox.smtp.mailtrap.io')
EMAIL_HOST_USER = os.environ.get('BAR_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('BAR_EMAIL_HOST_PASSWORD', '')
EMAIL_PORT = int(os.environ.get('BAR_EMAIL_PORT', '2525'))
EMAIL_USE_TLS = env_bool('BAR_EMAIL_USE_TLS', default=True)

from operator import truediv
from pathlib import Path
from django.forms.utils import flatatt

from django.template.defaultfilters import truncatechars
from django.utils import timezone

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('BAR_SECRET_KEY', 'django-insecure-local-dev-key-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool('BAR_DEBUG', default=True)

ALLOWED_HOSTS = [
    'bar.iagmexico.com',
    'www.bar.iagmexico.com',
    '108.175.4.49',
    '127.0.0.1',
    'localhost',
    '0.0.0.0',
]

CSRF_TRUSTED_ORIGINS = ['https://bar.iagmexico.com','https://www.bar.iagmexico.com']

DECIMAL_SEPARATOR = ',' 
USE_THOUSAND_SEPARATOR = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.navigation_access',
            ],
        },
    },
]

WSGI_APPLICATION = 'bar.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('BAR_DB_ENGINE', 'django.db.backends.mysql'),
        'NAME': os.environ.get('BAR_DB_NAME', 'bar_db'),
        'USER': os.environ.get('BAR_DB_USER', 'root'),
        'PASSWORD': os.environ.get('BAR_DB_PASSWORD', 'root'),
        'HOST': os.environ.get('BAR_DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('BAR_DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('BAR_DB_NAME', BASE_DIR / 'db.sqlite3'),
    }


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'es-mx'

TIME_ZONE = 'America/Mexico_City'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

#SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
#SESSION_COOKIE_SECURE = env_bool('BAR_SESSION_COOKIE_SECURE', default=not DEBUG)
#CSRF_COOKIE_SECURE = env_bool('BAR_CSRF_COOKIE_SECURE', default=not DEBUG)

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
