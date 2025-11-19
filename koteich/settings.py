import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-change-in-production')

DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

allowed_hosts_str = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,koteichhost.ru,www.koteichhost.ru')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_str.split(',')]

AUTH_USER_MODEL = 'accounts.CustomUser'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth', 
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'crispy_forms',
    'crispy_bootstrap4',
    'corsheaders',
    
    # Local apps - ВАЖНО: accounts должно быть ПЕРВЫМ
    'apps.accounts',
    'apps.dashboard', 
    'apps.chat',
    'apps.servers',
    'apps.auction', 
    'apps.forum',
    'apps.monitoring',
    'apps.promo',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'apps.security.middleware.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'koteich.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.servers.context_processors.api_status',
                'apps.forum.context_processors.forum_categories',
                'apps.chat.context_processors.restriction_status',
            ],
        },
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'gameap.log',
            'formatter': 'verbose',
            'encoding': 'utf8',
        },
    },
    'loggers': {
        'apps.servers': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        '': {  # root logger
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

WSGI_APPLICATION = 'koteich.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'host',           # Имя вашей базы данных
        'USER': 'host',                 # Ваш MySQL пользователь
        'PASSWORD': '4fHRkYbYAkHjpCa7', # Ваш пароль
        'HOST': '91.142.73.52',         # IP MySQL сервера
        'PORT': '3306',                 # Обычно 3306
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}


# Password validation
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
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = 'dashboard:dashboard'
LOGOUT_REDIRECT_URL = '/'

# Custom user model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# ==================== API Configuration ====================



GAMEAP_URL = 'http://109.172.85.115'  # Без слеша в конце!
GAMEAP_API_TOKEN = '1|FPOaSFmLQZuTul1p4TSDU19sUPJorxIi30qRDMw1'


DEFAULT_GAME_ID = 1
DEFAULT_DS_ID = 1  
DEFAULT_SERVER_IP = '109.172.85.115'  # IP где будут создаваться серверы
DEFAULT_SERVER_PORT = 'auto'

# API для управления серверами (тот самый API_BASE_URL который ты настраивал)
# JWT настройки для безопасного общения с API серверов
#JWT_SECRET = os.getenv('JWT_SECRET', 'admin')
#SERVER_ID = os.getenv('SERVER_ID', 'password')
#API_BASE_URL = os.getenv('API_BASE_URL', 'https://testlink.koteichhost.ru')  # Твой FastAPI с Docker

# ==================== Ollama Configuration ====================
# Нейросеть - НЕ ТРОГАТЬ
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'https://koteichcatalog.ru/ollama')
OLLAMA_USERNAME = os.getenv('OLLAMA_USERNAME', 'ollama')
OLLAMA_PASSWORD = os.getenv('OLLAMA_PASSWORD', 'secret123')
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'llama3.2:3b')
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '120'))  # Таймаут в секундах

CSRF_TRUSTED_ORIGINS = [
    'https://koteichhost.ru',
    'https://www.koteichhost.ru',
    'http://koteichhost.ru',
    'http://www.koteichhost.ru',
]

PROMO_API_URL = 'https://your-promo-api.com/api'
PROMO_API_KEY = 'your-secret-api-key'

# Для работы за прокси
CSRF_COOKIE_DOMAIN = '.koteichhost.ru'
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False

# Session settings
SESSION_COOKIE_DOMAIN = '.koteichhost.ru'
SESSION_COOKIE_SECURE = False  # True если есть HTTPS
SESSION_COOKIE_HTTPONLY = True

# Для reverse proxy
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Дополнительные настройки безопасности
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_AGE = 31449600 
CSRF_COOKIE_NAME = 'csrftoken'