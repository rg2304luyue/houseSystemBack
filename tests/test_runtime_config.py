"""Production configuration rejects credentialed wildcard CORS origins."""

import pytest

from app.core.config import Settings


@pytest.mark.parametrize("origins", ["*", "https://example.com, *", "https://*.example.com", " , "])
def test_production_rejects_non_explicit_origins(origins):
    """Wildcard or empty origin lists must fail before payment key loading."""
    with pytest.raises(ValueError, match="CORS_ORIGINS must list explicit origins"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="test-production-secret-value",
            DEBUG=False,
            PAYMENT_MOCK_ENABLED=False,
            CORS_ORIGINS=origins,
        )
