from pathlib import Path
import dj_database_url
import os
import environ
import json

# Directory di base del progetto
BASE_DIR = Path(__file__).resolve().parent.parent

# Inizializza `environ`
env = environ.Env(
    # Imposta valori di default e forzature
    DEBUG=(bool, False)
)

# Leggi il file .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Carica le variabili d'ambiente dal file .env
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Carica il contenuto del file JSON per Google Calendar
google_calendar_service_account_file_path = os.getenv('GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE')
if google_calendar_service_account_file_path:
    try:
        with open(google_calendar_service_account_file_path) as f:
            GOOGLE_CALENDAR_SERVICE_ACCOUNT_INFO = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        raise ValueError(f"Errore nel leggere il file di configurazione Google Calendar: {e}")
else:
    raise ValueError("La variabile d'ambiente GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE non è configurata.")

# Carica il contenuto del file JSON per Google Sheets
google_sheets_service_account_file_path = os.getenv('GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE')
if google_sheets_service_account_file_path:
    try:
        with open(google_sheets_service_account_file_path) as f:
            GOOGLE_SHEETS_SERVICE_ACCOUNT_INFO = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        raise ValueError(f"Errore nel leggere il file di configurazione Google Sheets: {e}")
else:
    raise ValueError("La variabile d'ambiente GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE non è configurata.")

LOGIN_URL = '/prenotazioni/login/'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'prenotazioni',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'calendario_prenotazioni.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'prenotazioni/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'calendario_prenotazioni.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{os.path.join(BASE_DIR, "db.sqlite3")}'
    )
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

TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
