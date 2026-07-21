"""FastAPI application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ---- Database ----
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: str = "3306"
    MYSQL_DB: str = "flaskhousesystem"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )

    # ---- App ----
    # Stable local default: tokens remain valid across auto-reload/restarts.
    # Production deployments must override this through the environment.
    SECRET_KEY: str = "house-system-local-development-secret"
    JSON_AS_ASCII: bool = False

    # ---- Redis ----
    REDIS_URL: str = "redis://@localhost:6379/0"

    # ---- OSS ----
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET_NAME: str = "flaskhousesystem"
    OSS_ENDPOINT: str = "oss-cn-hangzhou.aliyuncs.com"
    OSS_REGION: str = "cn-hangzhou"
    OSS_CNAME_URL: str | None = None

    # ---- AI (DashScope) ----
    DASHSCOPE_API_KEY: str = ""
    AI_CHAT_MODEL: str = "qwen-plus"
    AI_EMBEDDING_MODEL: str = "text-embedding-v3"

    # ---- Gaode Maps ----
    GAODE_WEATHER_KEY: str = ""
    GAODE_MAP_KEY: str = ""
    GAODE_MAP_SAFE_KEY: str = ""

    # ---- QQ Email SMTP ----
    QQ_SMTP_EMAIL: str = ""
    QQ_SMTP_AUTH_CODE: str = ""

    # ---- Alipay ----
    ALIPAY_SELLER_ID: str = ""
    ALIPAY_APP_ID: str = "2021000148684222"
    PAYMENT_MOCK_ENABLED: bool = True

    # ---- CORS ----
    CORS_ORIGINS: str = "http://localhost:4173,http://127.0.0.1:4173,http://localhost:4399"

    # ---- App ----
    DEBUG: bool = True

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "allow"}


settings = Settings()
