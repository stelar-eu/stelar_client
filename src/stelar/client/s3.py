from urllib.parse import urlparse

from minio import Minio
from minio.credentials.providers import WebIdentityProvider


from .base import BaseAPI


class S3API(BaseAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get the MinIO client
        u = urlparse(self._info.s3_api)
        minio_host = u.netloc
        secure = u.scheme == "https"

        def get_jwt():
            if self.token_expired():
                self.refresh_tokens()
            return {"access_token": self._token, "expires_in": self._expires_in}

        provider = WebIdentityProvider(
            jwt_provider_func=get_jwt, sts_endpoint=self._info.s3_api
        )
        self._minio_client = Minio(minio_host, secure=secure, credentials=provider)

    @property
    def s3(self):
        return self._minio_client
