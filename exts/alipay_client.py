import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from pathlib import Path

from app.core.config import settings
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
from alipay.aop.api.request.AlipaySystemOauthTokenRequest import AlipaySystemOauthTokenRequest
from alipay.aop.api.request.AlipayUserInfoShareRequest import AlipayUserInfoShareRequest


class AlipayClient:
    def __init__(self):
        root = Path(__file__).resolve().parents[1]
        private_path = Path(settings.ALIPAY_PRIVATE_KEY_PATH)
        public_path = Path(settings.ALIPAY_PUBLIC_KEY_PATH)
        private_path = private_path if private_path.is_absolute() else root / private_path
        public_path = public_path if public_path.is_absolute() else root / public_path
        private_key = private_path.read_text(encoding="utf-8")
        public_key = public_path.read_text(encoding="utf-8")
        config = AlipayClientConfig()
        config.server_url = settings.ALIPAY_GATEWAY
        config.app_id = settings.ALIPAY_APP_ID
        config.app_private_key = private_key
        config.alipay_public_key = public_key
        self._public_key = public_key
        self.client = DefaultAlipayClient(alipay_client_config=config)

    def generate_payment_url(self, out_trade_no, total_amount, subject):
        model = AlipayTradePagePayModel()
        model.out_trade_no = out_trade_no
        model.total_amount = f"{float(total_amount):.2f}"
        model.subject = subject
        model.product_code = "FAST_INSTANT_TRADE_PAY"

        request = AlipayTradePagePayRequest()
        request.biz_model = model
        request.notify_url = settings.ALIPAY_NOTIFY_URL
        request.return_url = settings.ALIPAY_RETURN_URL

        return self.client.page_execute(request, http_method="GET")

    def verify(self, data: dict, signature: str) -> bool:
        """Verify Alipay callback signature using RSA-SHA256.

        Performs RSA signature verification using the Alipay public key.
        Local development uses the authenticated ``mock-confirm`` endpoint;
        public callbacks are never allowed to bypass signature verification.
        """
        try:
            # Build the sign content (sorted params, excluding sign/sign_type)
            sign_content = '&'.join(
                f'{k}={v}' for k, v in sorted(data.items())
                if v is not None and v != ''
            )

            # Load Alipay public key
            public_key = serialization.load_pem_public_key(
                self._public_key.encode('utf-8'),
                backend=default_backend()
            )

            # Decode the base64 signature
            signature_bytes = base64.b64decode(signature)

            # Verify using RSA-SHA256
            public_key.verify(
                signature_bytes,
                sign_content.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def get_auth_token(self, auth_code: str) -> dict:
        request = AlipaySystemOauthTokenRequest()
        request.grant_type = "authorization_code"
        request.code = auth_code
        response = self.client.execute(request)
        return response.to_dict()

    def get_user_info(self, access_token: str) -> dict:
        request = AlipayUserInfoShareRequest()
        response = self.client.execute(request, auth_token=access_token)
        return response.to_dict()
