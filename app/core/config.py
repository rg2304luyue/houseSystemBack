"""FastAPI application configuration using Pydantic Settings."""
from pathlib import Path
from urllib.parse import urlparse

from cryptography.hazmat.primitives import serialization
from pydantic import model_validator
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

    # ---- AI chat (DeepSeek OpenAI-compatible API) ----
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    AI_CHAT_MODEL: str = "deepseek-v4-flash"
    AI_DEEPSEEK_CONNECT_TIMEOUT_SECONDS: float = 5.0
    AI_DEEPSEEK_READ_TIMEOUT_SECONDS: float = 45.0

    # ---- RAG embeddings (DashScope) ----
    DASHSCOPE_API_KEY: str = ""
    AI_EMBEDDING_MODEL: str = "qwen3.7-text-embedding"
    AI_DASHSCOPE_TIMEOUT_SECONDS: float = 30.0

    # ---- AI reliability (single-process local deployment) ----
    AI_PROVIDER_MAX_ATTEMPTS: int = 3
    AI_RETRY_BASE_DELAY_SECONDS: float = 0.5
    AI_RETRY_MAX_DELAY_SECONDS: float = 8.0
    AI_AGENT_MAX_CONCURRENT: int = 4
    AI_AGENT_MAX_CONCURRENT_PER_USER: int = 1
    AI_RUN_MAX_ATTEMPTS: int = 3
    AI_RUN_LEASE_SECONDS: int = 180
    AI_PROVIDER_MAX_CONCURRENT: int = 3
    AI_CIRCUIT_FAILURE_THRESHOLD: int = 5
    AI_CIRCUIT_OPEN_SECONDS: float = 30.0

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
    ALIPAY_PRIVATE_KEY_PATH: str = "exts/app_private_key.txt"
    ALIPAY_PUBLIC_KEY_PATH: str = "exts/alipay_public_key.txt"
    ALIPAY_GATEWAY: str = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
    ALIPAY_NOTIFY_URL: str = "http://127.0.0.1:8000/api/v1/payments/notify"
    ALIPAY_RETURN_URL: str = "http://127.0.0.1:4399/alipay/payment-result"
    PAYMENT_MOCK_ENABLED: bool = True

    # ---- CORS ----
    CORS_ORIGINS: str = "http://localhost:4173,http://127.0.0.1:4173,http://localhost:4399"

    # ---- App ----
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    @model_validator(mode="after")
    def validate_runtime_safety(self):
        if self.ENVIRONMENT.lower() in {"production", "prod"}:
            if self.SECRET_KEY == "house-system-local-development-secret":
                raise ValueError("SECRET_KEY must be configured in production")
            if self.DEBUG:
                raise ValueError("DEBUG must be disabled in production")
            if self.PAYMENT_MOCK_ENABLED:
                raise ValueError("PAYMENT_MOCK_ENABLED must be disabled in production")
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
            if "*" in origins:
                raise ValueError("CORS_ORIGINS must list explicit origins in production")
            if not origins or any("*" in origin for origin in origins):
                raise ValueError("CORS_ORIGINS must list explicit origins in production")
            required = {
                "ALIPAY_APP_ID": self.ALIPAY_APP_ID,
                "ALIPAY_SELLER_ID": self.ALIPAY_SELLER_ID,
                "ALIPAY_PRIVATE_KEY_PATH": self.ALIPAY_PRIVATE_KEY_PATH,
                "ALIPAY_PUBLIC_KEY_PATH": self.ALIPAY_PUBLIC_KEY_PATH,
                "ALIPAY_GATEWAY": self.ALIPAY_GATEWAY,
                "ALIPAY_NOTIFY_URL": self.ALIPAY_NOTIFY_URL,
                "ALIPAY_RETURN_URL": self.ALIPAY_RETURN_URL,
            }
            missing = [name for name, value in required.items() if not str(value).strip()]
            if missing:
                raise ValueError(f"Missing production Alipay settings: {', '.join(missing)}")
            for name, value in {
                "ALIPAY_NOTIFY_URL": self.ALIPAY_NOTIFY_URL,
                "ALIPAY_RETURN_URL": self.ALIPAY_RETURN_URL,
            }.items():
                parsed = urlparse(value)
                if parsed.scheme != "https" or not parsed.netloc:
                    raise ValueError(f"{name} must be an absolute HTTPS URL in production")
            root = Path(__file__).resolve().parents[2]
            private_path = Path(self.ALIPAY_PRIVATE_KEY_PATH)
            public_path = Path(self.ALIPAY_PUBLIC_KEY_PATH)
            private_path = private_path if private_path.is_absolute() else root / private_path
            public_path = public_path if public_path.is_absolute() else root / public_path
            try:
                serialization.load_pem_private_key(private_path.read_bytes(), password=None)
                serialization.load_pem_public_key(public_path.read_bytes())
            except (OSError, ValueError, TypeError) as exc:
                raise ValueError("Alipay key files must exist and contain valid PEM keys") from exc
        return self

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "allow"}


settings = Settings()
