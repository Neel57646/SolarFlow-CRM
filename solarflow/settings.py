import os
import tempfile
import urllib.parse
from pathlib import Path
from importlib.util import find_spec

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_DATA_DIR = Path(os.getenv("SOLARFLOW_DATA_DIR", str(Path(tempfile.gettempdir()) / "SolarFlowCRM")))
LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-solarflow-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host]
CSRF_TRUSTED_ORIGINS = [origin for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin]
PLANNER_ONLY = os.getenv("PLANNER_ONLY", "0") == "1"
WHITENOISE_AVAILABLE = find_spec("whitenoise") is not None

if ".vercel.app" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".vercel.app")


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crm',
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

if WHITENOISE_AVAILABLE:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = 'solarflow.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'crm.context_processors.app_shell',
            ],
        },
    },
]

WSGI_APPLICATION = 'solarflow.wsgi.application'


def parse_database_url(database_url):
    parsed = urllib.parse.urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("DATABASE_URL must use postgres:// or postgresql://.")

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": urllib.parse.unquote(parsed.path.lstrip("/")),
        "USER": urllib.parse.unquote(parsed.username or ""),
        "PASSWORD": urllib.parse.unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": parsed.port or 5432,
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "0")),
        "OPTIONS": {
            "sslmode": os.getenv("DB_SSLMODE", "require"),
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
        },
    }


if os.getenv("DATABASE_URL"):
    DATABASES = {"default": parse_database_url(os.environ["DATABASE_URL"])}
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv("DB_ENGINE", 'django.db.backends.sqlite3'),
            'NAME': os.getenv("DB_NAME", str(LOCAL_DATA_DIR / 'db.sqlite3')),
        }
    }


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


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Australia/Sydney'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
if WHITENOISE_AVAILABLE:
    WHITENOISE_USE_FINDERS = os.getenv("WHITENOISE_USE_FINDERS", "1") == "1"
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": os.getenv(
                "DJANGO_STATICFILES_STORAGE",
                "django.contrib.staticfiles.storage.StaticFilesStorage",
            ),
        },
    }

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "investment-planner" if PLANNER_ONLY else "dashboard"
LOGOUT_REDIRECT_URL = "login"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "1") == "1"
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
