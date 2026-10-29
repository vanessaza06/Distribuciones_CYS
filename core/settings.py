import os
from importlib.util import find_spec
from pathlib import Path
import pymysql
from dotenv import load_dotenv

pymysql.install_as_MySQLdb()
load_dotenv()

# Evitar comprobación de versión de MySQL (permite usar MySQL 8.0 con Django 6.1)
import django.db.backends.base.base
django.db.backends.base.base.BaseDatabaseWrapper.check_database_version_supported = lambda self: None


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# SEGURIDAD
# ---------------------------------------------------------------------------
# Por defecto DEBUG está APAGADO (seguro). Para desarrollar, en tu .env pon:
#   DJANGO_DEBUG=True
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true'

# La clave secreta sale del .env. Solo en desarrollo se permite una de respaldo.
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-solo-para-desarrollo-local'
    else:
        raise RuntimeError(
            'Falta DJANGO_SECRET_KEY en el archivo .env (obligatoria con DEBUG=False).'
        )

# Hosts permitidos, separados por coma en el .env:
#   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,midominio.com
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://0.0.0.0:8000',
    'http://localhost',
    'http://127.0.0.1',
]

CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True

# Si algún día sirves el sistema con HTTPS, pon DJANGO_USE_HTTPS=True en el .env
if os.getenv('DJANGO_USE_HTTPS', 'False').lower() == 'true':
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'


# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'usuarios',
    'app',
    'django.contrib.humanize',
]

MIDDLEWARE = [
    'app.perf_middleware.PerfLogMiddleware',  # TEMPORAL: diagnóstico de lentitud (escribe perf.log)
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'app.middleware.LoginRequiredMiddleware',  # exige sesión en todas las rutas (crear app/middleware.py)
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# WhiteNoise sirve los estáticos con DEBUG=False. Se activa solo si está instalado:
#   pip install whitenoise
if find_spec('whitenoise') is not None:
    MIDDLEWARE.insert(
        MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
        'whitenoise.middleware.WhiteNoiseMiddleware',
    )

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',      # aquí van 404.html, 403.html y 500.html
            BASE_DIR / 'app',
            BASE_DIR / 'app' / 'partials',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app.context_processors.aside_stats',
                "app.context_processors.config_empresa",
            ],
        },
    },
]


WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'distribuciones_cys'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'CONN_MAX_AGE': 60,           # reutiliza la conexión (~40 ms menos por petición)
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES', NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'",
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'es-co'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'   # destino de: python manage.py collectstatic


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    # Envío real por Gmail
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_TIMEOUT = 15
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
else:
    # Sin credenciales: el correo solo se imprime en la terminal
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'no-reply@cysltda.com'

AUTH_USER_MODEL = 'usuarios.Usuario'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'principal'
LOGOUT_REDIRECT_URL = 'login'

# Rutas (prefijos) accesibles SIN iniciar sesión. Agrega aquí las de tu app
# de usuarios, por ejemplo recuperar contraseña.
LOGIN_EXEMPT_URLS = [
    '/static/',
    '/media/',
    '/admin/',
    '/logout/',
    '/recuperar/',
    '/password-reset/',
]