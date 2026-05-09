import os
import secrets


def _env(key, default=None):
    """读取环境变量，不存在则返回默认值"""
    return os.environ.get(key, default)


class Config:
    # ---- 数据库 ----
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{_env('MYSQL_USER', 'root')}"
        f":{_env('MYSQL_PASSWORD', 'root')}"
        f"@{_env('MYSQL_HOST', 'localhost')}"
        f":{_env('MYSQL_PORT', '3306')}"
        f"/{_env('MYSQL_DB', 'flaskhousesystem')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Flask ----
    SECRET_KEY = _env('SECRET_KEY') or secrets.token_hex(32)
    JSON_AS_ASCII = False
    STRICT_SLASH = False

    # ---- Redis ----
    REDIS_URL = _env('REDIS_URL', 'redis://@localhost:6379/0')

    # ---- Celery ----
    CELERY_BROKER_URL = _env('CELERY_BROKER_URL', 'redis://@localhost:6379/1')
    CELERY_RESULT_BACKEND = _env('CELERY_RESULT_BACKEND', 'redis://@localhost:6379/1')
    CELERY_ACCEPT_CONTENT = ['application/json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'Asia/Shanghai'
    CELERY_WORKER_AUTOSCALE = (5, 1)

    # ---- GitHub OAuth ----
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    GITHUB_CLIENT_ID = _env('GITHUB_CLIENT_ID', '')
    GITHUB_CLIENT_SECRET = _env('GITHUB_CLIENT_SECRET', '')
    GITHUB_AUTHORIZE_URL = 'https://github.com/login/oauth/authorize'
    GITHUB_ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token'
    GITHUB_API_BASE_URL = 'https://api.github.com/'
    GITHUB_CALLBACK_URL = _env('GITHUB_CALLBACK_URL', 'http://127.0.0.1:5000/github/callback')

    # ---- 阿里云 OSS ----
    OSS_ACCESS_KEY_ID = _env('OSS_ACCESS_KEY_ID', '')
    OSS_ACCESS_KEY_SECRET = _env('OSS_ACCESS_KEY_SECRET', '')
    OSS_BUCKET_NAME = _env('OSS_BUCKET_NAME', 'flaskhousesystem')
    OSS_ENDPOINT = _env('OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')
    OSS_REGION = _env('OSS_REGION', 'cn-hangzhou')
    OSS_CNAME_URL = _env('OSS_CNAME_URL') or None

    # ---- 允许上传的文件扩展名 ----
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # ---- AI (DashScope / 千问) ----
    DASHSCOPE_API_KEY = _env('DASHSCOPE_API_KEY', '')

    # ---- 高德地图 ----
    GaoDeWeatherKey = _env('GAODE_WEATHER_KEY', '')
    GaoDeMapKey = _env('GAODE_MAP_KEY', '')
    GaoDeMapSafeKey = _env('GAODE_MAP_SAFE_KEY', '')

    # ---- QQ 邮箱 SMTP ----
    QQ_SMTP_EMAIL = _env('QQ_SMTP_EMAIL', '')
    QQ_SMTP_AUTH_CODE = _env('QQ_SMTP_AUTH_CODE', '')
