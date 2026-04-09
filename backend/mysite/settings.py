"""
Django settings for mysite project.
"""

import os
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# [공통] 환경파일 선택
# ---------------------------------------------------------
# [개발용] docker-compose.yml 에서 .env.dev 를 사용하므로
#          DJANGO_ENV=development 로 동작하게 설정 가능
#
# [배포용] docker-compose.prod.yml 에서 .env 를 사용하므로
#          DJANGO_ENV=production 으로 동작하게 설정 가능
# =========================================================
env = environ.Env()
DJANGO_ENV = os.getenv("DJANGO_ENV", "development")

if DJANGO_ENV == "production":
    # [배포용] .env 읽기
    environ.Env.read_env(BASE_DIR / ".env")
else:
    # [개발용] .env.dev 읽기
    environ.Env.read_env(BASE_DIR / ".env.dev")


# =========================================================
# [공통] 기본 보안 / 실행 설정
# =========================================================
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-secret-key")

# [개발용] 보통 True
# [배포용] 반드시 False
DEBUG = env.bool("DJANGO_DEBUG", default=(DJANGO_ENV != "production"))

# [개발용] 127.0.0.1, localhost
# [배포용] 도메인, EC2 IP 등
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])


# =========================================================
# [공통] Application
# =========================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # DRF
    "rest_framework",
    # apps
    "apps.accounts",
    "apps.products",
    "apps.reviews",
    "apps.interactions",
    "apps.ai_gateway",
    "apps.crawling",
    # pgvector
    "pgvector.django",
    # [배포용/개발용 공통]
    "storages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# [배포용] HTTPS 프록시 뒤라면 필요할 수 있음
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

ROOT_URLCONF = "mysite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mysite.wsgi.application"


# =========================================================
# [공통] Database
# ---------------------------------------------------------
# [개발용] DB_HOST=db / DB_PORT=5432
# [배포용] DB_HOST=db / DB_PORT=5432
#          (컨테이너끼리는 내부 네트워크로 통신)
# =========================================================
DB_NAME = env("DB_NAME", default="product_review_db")
DB_USER = env("DB_USER", default="product_review_user")
DB_PASSWORD = env("DB_PASSWORD", default="product_review_password")
DB_HOST = env("DB_HOST", default="db")
DB_PORT = env("DB_PORT", default="5432")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}


# =========================================================
# [공통] Password validation
# =========================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# =========================================================
# [공통] Internationalization
# =========================================================
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True


# =========================================================
# [공통] User model
# =========================================================
AUTH_USER_MODEL = "accounts.User"


# =========================================================
# [공통] DRF / JWT
# =========================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# =========================================================
# [공통] FastAPI
# =========================================================
FASTAPI_BASE_URL = env("FASTAPI_BASE_URL", default="http://fastapi:8001")


# =========================================================
# [공통] Redis / Celery
# =========================================================
REDIS_URL = env("REDIS_URL", default="redis://redis:6379/0")

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = "Asia/Seoul"
CELERY_RESULT_EXPIRES = 3600
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 60 * 10
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 8

# [개발용] 필요 시 True로 켜서 즉시 실행 테스트 가능
# [배포용] False 유지
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = True


# =========================================================
# [공통] Static / Media
# ---------------------------------------------------------
# [개발용] 로컬 static, media 사용
# [배포용] S3 사용
# =========================================================
USE_S3 = env.bool("USE_S3", default=False)

if USE_S3:
    # =====================================================
    # [배포용] S3 설정
    # =====================================================
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default=None)
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default=None)
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="ap-northeast-2")

    AWS_STORAGE_BUCKET_NAME_STATIC = env("AWS_STORAGE_BUCKET_NAME_STATIC", default=None)
    AWS_STORAGE_BUCKET_NAME_MEDIA = env("AWS_STORAGE_BUCKET_NAME_MEDIA", default=None)

    AWS_DEFAULT_ACL = None

    STATIC_URL = (
        f"https://{AWS_STORAGE_BUCKET_NAME_STATIC}.s3."
        f"{AWS_S3_REGION_NAME}.amazonaws.com/static/"
    )
    MEDIA_URL = (
        f"https://{AWS_STORAGE_BUCKET_NAME_MEDIA}.s3."
        f"{AWS_S3_REGION_NAME}.amazonaws.com/media/"
    )

    STORAGES = {
        "default": {
            "BACKEND": "mysite.storage.MediaStorage",
        },
        "staticfiles": {
            "BACKEND": "mysite.storage.StaticStorage",
        },
    }

else:
    # =====================================================
    # [개발용] 로컬 파일 저장
    # =====================================================
    STATIC_URL = "/static/"
    STATICFILES_DIRS = [
        BASE_DIR / "static",
    ]
    STATIC_ROOT = BASE_DIR / "staticfiles"

    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"


# =========================================================
# [배포용] 추가 보안 옵션
# ---------------------------------------------------------
# [개발용] DEBUG=True 상태에서는 보통 꺼둠
# [배포용] DEBUG=False 일 때 활성화 권장
# =========================================================
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
