"""
Django settings for Proyecto project.
"""

from pathlib import Path
import os
import pymysql

pymysql.install_as_MySQLdb()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-xrsy$r_rb62jwx^ltlf7)w8^-xqb=@tbmq)$@aloks4$b=!p@k'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# ==============================================================================
# APPLICATION DEFINITION
# ==============================================================================

INSTALLED_APPS = [
    # Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Requerido por allauth
    
    # Allauth - Debe ir después de django.contrib.sites
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    
    # Tus Apps
    'usuarios',
    'proveedor',
    'administrador',
    'soporte',
    'proyect',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # Solo una vez
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Requerido por allauth
]

ROOT_URLCONF = 'proyect.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # Requerido por allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'proveedor.context_processors.proveedor_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'proyect.wsgi.application'


# ==============================================================================
# DATABASE
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'club_db',
        'USER': 'root',
        'PASSWORD': '12345678',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}


# ==============================================================================
# PASSWORD VALIDATION
# ==============================================================================

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


# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = 'es-cl'  # Español de Chile
TIME_ZONE = 'America/Santiago'  # Zona horaria de Chile
USE_I18N = True
USE_TZ = True


# ==============================================================================
# STATIC FILES (CSS, JavaScript, Images)
# ==============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Solo incluir si el directorio existe
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
] if os.path.exists(os.path.join(BASE_DIR, 'static')) else []


# ==============================================================================
# MEDIA FILES (User Uploaded Files)
# ==============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Imagen de perfil por defecto
DEFAULT_PROFILE_IMAGE = 'usuarios/img/default_profile.png'


# ==============================================================================
# AUTHENTICATION & AUTHORIZATION
# ==============================================================================

# Site Framework (requerido por allauth)
SITE_ID = 1

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Django default
    'allauth.account.auth_backends.AuthenticationBackend',  # Allauth
]

# Login/Logout URLs
LOGIN_URL = '/cuenta/'
LOGIN_REDIRECT_URL = '/dashboard/'  # Redirigir después de login exitoso
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'


# ==============================================================================
# DJANGO-ALLAUTH CONFIGURATION
# ==============================================================================

# Métodos de Login (SIN DEPRECACIONES)
ACCOUNT_LOGIN_METHODS = {'email'}  # Solo email (antes: ACCOUNT_AUTHENTICATION_METHOD)

# Campos de Registro (SIN DEPRECACIONES)
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']  # Antes: ACCOUNT_EMAIL_REQUIRED, ACCOUNT_USERNAME_REQUIRED

# Verificación de Email
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # optional, mandatory, none

# Social Account Settings
SOCIALACCOUNT_AUTO_SIGNUP = False  # Mostrar formulario personalizado después de login social
SOCIALACCOUNT_LOGIN_ON_GET = True  # Permitir login directo con GET
SOCIALACCOUNT_QUERY_EMAIL = True  # Obtener email del proveedor social

# Adapter Personalizado (si lo tienes)
SOCIALACCOUNT_ADAPTER = 'usuarios.adapters.MySocialAccountAdapter'  # Ajusta el path según tu estructura

# Formulario Personalizado (si lo tienes)
SOCIALACCOUNT_FORMS = {
    'signup': 'usuarios.forms.SocialSignupForm',  # Ajusta el path según tu estructura
}


# ==============================================================================
# SOCIAL PROVIDERS CONFIGURATION
# ==============================================================================
# IMPORTANTE: Las credenciales (client_id, secret) se configuran en Django Admin,
# NO aquí en settings.py. Esta sección solo define el comportamiento de cada proveedor.

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'VERIFIED_EMAIL': True,
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {
            'auth_type': 'reauthenticate'
        },
        'INIT_PARAMS': {
            'cookie': True
        },
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'verified',
        ],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
        'VERSION': 'v18.0',  # Versión actualizada de Facebook Graph API
    }
}


# ==============================================================================
# DEFAULT PRIMARY KEY FIELD TYPE
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==============================================================================
# CUSTOM SETTINGS (Opcionales)
# ==============================================================================

# Configuración de Email (para producción)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'tu-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'tu-contraseña'
# DEFAULT_FROM_EMAIL = 'Club Almacén <noreply@clubalmacen.cl>'

# Para desarrollo, usar console backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


