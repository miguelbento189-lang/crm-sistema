# ================= SESSÃO E COOKIES ======================
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True
"""
Django settings for the portfolio CRM project.
Configurado para banco relacional e Cloudinary.
"""

from pathlib import Path
import json
import os
import dj_database_url
import decouple
import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.core.exceptions import ImproperlyConfigured

config = decouple.config
DECOUPLE_UNDEFINED_VALUE_ERROR = getattr(decouple, 'UndefinedValueError', KeyError)

# ==============================================================================
# 1. CAMINHOS BASE (CRÍTICO: Deve estar no topo)
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent


def env_str(name, default=''):
    raw_value = os.getenv(name)
    if raw_value is not None:
        return str(raw_value)
    try:
        value = config(name, default=default)
    except (KeyError, DECOUPLE_UNDEFINED_VALUE_ERROR):
        value = default
    return str(value if value is not None else '')


def env_bool(name, default=False):
    raw_value = os.getenv(name)
    if raw_value is not None:
        return str(raw_value).strip().lower() in {'1', 'true', 'yes', 'on'}
    try:
        return config(name, default=default, cast=bool)
    except (KeyError, DECOUPLE_UNDEFINED_VALUE_ERROR):
        return default


def csv_env(name, default=''):
    raw_value = env_str(name, default=default)
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(',') if item.strip()]


def json_env(name, default='{}'):
    raw_value = env_str(name, default=default).strip()
    if not raw_value:
        return {}
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def build_database_config(database_url, *, require_ssl=True):
    return dj_database_url.parse(
        database_url,
        conn_max_age=600,
        ssl_require=require_ssl,
    )

# ==============================================================================
# 2. SEGURANÇA
# ==============================================================================
SECRET_KEY = env_str('SECRET_KEY', default='')
DEBUG = env_bool('DEBUG', default=True)
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-portfolio-crm-dev-only'
    else:
        raise ImproperlyConfigured('Configure SECRET_KEY no ambiente antes de iniciar a aplicação com DEBUG=False.')

if not DEBUG and SECRET_KEY.startswith('troque-esta-chave'):
    raise ImproperlyConfigured('Defina uma SECRET_KEY real no ambiente antes de publicar a aplicação.')

ALLOWED_HOSTS = csv_env(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1'
)
if env_bool('ALLOW_ALL_HOSTS', default=False):
    if DEBUG:
        ALLOWED_HOSTS = ['*']
    else:
        raise ImproperlyConfigured('ALLOW_ALL_HOSTS só pode ser habilitado com DEBUG=True.')
CSRF_TRUSTED_ORIGINS = csv_env('CSRF_TRUSTED_ORIGINS')
RENDER_EXTERNAL_HOSTNAME = env_str('RENDER_EXTERNAL_HOSTNAME', default='').strip()
if RENDER_EXTERNAL_HOSTNAME:
    if RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    render_origin = f'https://{RENDER_EXTERNAL_HOSTNAME}'
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)
VERCEL_URL = env_str('VERCEL_URL', default='').strip()
if VERCEL_URL:
    if VERCEL_URL not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(VERCEL_URL)
    vercel_origin = f'https://{VERCEL_URL}'
    if vercel_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(vercel_origin)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = env_bool('USE_X_FORWARDED_HOST', default=True)
SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', default=False)
SESSION_COOKIE_SECURE = env_bool('SESSION_COOKIE_SECURE', default=not DEBUG)
CSRF_COOKIE_SECURE = env_bool('CSRF_COOKIE_SECURE', default=not DEBUG)
DEBUG_PROPAGATE_EXCEPTIONS = env_bool('DEBUG_PROPAGATE_EXCEPTIONS', default=False)
DISABLE_STATIC_MANIFEST = env_bool('DISABLE_STATIC_MANIFEST', default=True)

# ==============================================================================
# 3. APLICAÇÕES INSTALADAS
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
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

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'core.wsgi.application'

# ==============================================================================
# 4. BANCO DE DADOS
# ==============================================================================
DATABASE_URL = env_str('DATABASE_URL', default='')
USE_SQLITE = env_bool('USE_SQLITE', default=False)
TENANT_DATABASE_URLS = json_env('TENANT_DATABASE_URLS')
TENANT_CONTROL_DATABASE_ALIAS = 'default'
TENANT_QUERY_PARAM = env_str('TENANT_QUERY_PARAM', default='tenant')
TENANT_HEADER = env_str('TENANT_HEADER', default='X-Tenant')
TENANT_ALLOW_QUERY_OVERRIDE = env_bool('TENANT_ALLOW_QUERY_OVERRIDE', default=False)
TENANT_FALLBACK_HOSTS = csv_env('TENANT_FALLBACK_HOSTS', default='localhost,127.0.0.1')
TENANT_ENFORCE_SYSTEM_TENANT = env_bool('TENANT_ENFORCE_SYSTEM_TENANT', default=bool(TENANT_DATABASE_URLS))
ASAAS_API_URL = env_str('ASAAS_API_URL', default='https://sandbox.asaas.com/api/v3')
ASAAS_API_KEY = env_str('ASAAS_API_KEY', default='')
GOOGLE_MAPS_BROWSER_API_KEY = env_str('GOOGLE_MAPS_BROWSER_API_KEY', default='')
GOOGLE_MAPS_MAP_ID = env_str('GOOGLE_MAPS_MAP_ID', default='')

if USE_SQLITE or not DATABASE_URL:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': build_database_config(DATABASE_URL)
    }

for alias, tenant_database_url in TENANT_DATABASE_URLS.items():
    clean_alias = str(alias).strip()
    clean_url = str(tenant_database_url).strip()
    if not clean_alias or not clean_url or clean_alias == TENANT_CONTROL_DATABASE_ALIAS:
        continue
    DATABASES[clean_alias] = build_database_config(clean_url)

DATABASE_ROUTERS = []

# ==============================================================================
# 5. VALIDAÇÃO DE SENHA
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# 6. INTERNACIONALIZAÇÃO
# ==============================================================================
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True
USE_I18N = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True # Isso ativa o ponto no milhar

# ======================================================================
# 7. DASHBOARD (METAS PADRAO)
# ======================================================================
DASHBOARD_TARGETS = {
    'leads': 80,
    'vendas': 12,
    'projetos': 6,
    'tarefas': 80,
    'os': 30,
    'rh': 4,
}
DECIMAL_SEPARATOR = ','
THOUSAND_SEPARATOR = '.'
# ==============================================================================
# 7. ARQUIVOS ESTÁTICOS
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

if DISABLE_STATIC_MANIFEST:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    WHITENOISE_USE_FINDERS = True
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# 8. MÍDIA E CLOUDINARY (FOTOS) - CORRIGIDO
# ==============================================================================

# Configuração para o Django Cloudinary Storage
cloudinary_cloud_name = env_str('CLOUDINARY_STORAGE_CLOUD_NAME', default='').strip()
cloudinary_api_key = env_str('CLOUDINARY_STORAGE_API_KEY', default='').strip()
cloudinary_api_secret = env_str('CLOUDINARY_STORAGE_API_SECRET', default='').strip()

CLOUDINARY_STORAGE = {
        'CLOUD_NAME': cloudinary_cloud_name,
        'API_KEY': cloudinary_api_key,
        'API_SECRET': cloudinary_api_secret,
}

# Inicialização da biblioteca apenas quando as credenciais existem.
if cloudinary_cloud_name and cloudinary_api_key and cloudinary_api_secret:
    cloudinary.config(
        cloud_name=cloudinary_cloud_name,
        api_key=cloudinary_api_key,
        api_secret=cloudinary_api_secret,
        secure=True,
    )

    # Define armazenamento padrão
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ==============================================================================
# 9. OUTRAS CONFIGURAÇÕES
# ==============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'product_login'
LOGIN_REDIRECT_URL = 'crm:crm_dashboard'
LOGOUT_REDIRECT_URL = 'product_login'

# ============================================================================== 
# 9.1 EMAIL (SMTP)
# ==============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='')
EMAIL_SENDER_DOMAIN = config('EMAIL_SENDER_DOMAIN', default='example.com')

# =================================================
# CONFIGURAÇÃO PWA (APP TÉCNICO)
# =================================================

# Diretório onde o Service Worker ficará (raiz do static)
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static/js', 'serviceworker.js')

PWA_APP_NAME = 'CRM Tecnico'
PWA_APP_DESCRIPTION = 'Central de Operacoes do CRM'
PWA_APP_THEME_COLOR = '#0f172a' # A cor do Header (Slate-900)
PWA_APP_BACKGROUND_COLOR = '#f0f4f8' # A cor do fundo da tela
PWA_APP_DISPLAY = 'standalone' # Remove a barra do navegador
PWA_APP_SCOPE = '/sistema/app/'
PWA_APP_ORIENTATION = 'portrait' # Força modo retrato
PWA_APP_START_URL = '/sistema/app/' # A URL que abre quando clica no ícone
PWA_APP_STATUS_BAR_COLOR = 'default'

# Ícones (Você precisará criar esses arquivos depois)
PWA_APP_ICONS = [
    {
        'src': '/static/icons/logo.png',
        'sizes': '160x160'
    },
    {
        'src': '/static/icons/logo.png',
        'sizes': '512x512'
    }
]
PWA_APP_ICONS_APPLE = [
    {
        'src': '/static/icons/logo.png',
        'sizes': '160x160'
    }
]
PWA_APP_SPLASH_SCREEN = [
    {
        'src': '/static/icons/logo.png',
        'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'
    }
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'pt-BR'