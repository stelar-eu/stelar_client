from urllib.parse import urlparse

import s3fs
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
        self._minio_client_provider = provider
        self._minio_client = Minio(minio_host, secure=secure, credentials=provider)

    @property
    def s3(self) -> Minio:
        return self._minio_client

    def s3fs(self) -> s3fs.S3FileSystem:
        """Return a file-system handler for the data lake.

        This method returns an instance of the `s3fs.S3FileSystem` class
        that can be used to interact with the data lake.

        Please see <https://github.com/fsspec/s3fs/> for more information.
        """
        return s3fs.S3FileSystem(**self.s3_access_data())

    def open(self, path: str, mode: str = "rb", **kwargs):
        """Open a file in the data lake.

        This method returns a file-like object that can be used to read or
        write data from the data lake.

        Parameters
        ----------
        path : str
            The path to the file in the data lake.
        mode : str
            The mode in which to open the file. This can be one of the
            following: 'r', 'rb', 'w', 'wb', 'a', 'ab'.
        kwargs : dict
            Additional keyword arguments to pass to the file system.

        Returns
        -------
        file-like
            A file-like object that can be used to read or write data.
        """
        fs = self.s3fs()
        return fs.open(path, mode, **kwargs)

    def s3_access_data(self) -> dict:
        """Return a dict with options for accessing the S3 API."""

        u = urlparse(self.klms_info.s3_api)
        # minio_host = u.netloc
        use_ssl = u.scheme == "https"

        acc = self._minio_client_provider.retrieve()
        return {
            "key": acc.access_key,
            "secret": acc.secret_key,
            "token": acc.session_token,
            "client_kwargs": {
                "endpoint_url": self.klms_info.s3_api,
                "secure": use_ssl,
                "verify": self._tls_verify,
                # "region": "us-east-1",
                # "signature_version": "s3v4",
            },
        }

    def _boto3_client(self):
        """Return a boto3 client for S3 API."""
        import boto3

        acc = self._minio_client_provider.retrieve()
        return boto3.client(
            "s3",
            endpoint_url=self.klms_info.s3_api,
            # region_name="us-east-1",
            aws_access_key_id=acc.access_key,
            aws_secret_access_key=acc.secret_key,
            aws_session_token=acc.session_token,
            config=boto3.session.Config(signature_version="s3v4"),
            verify=False,
        )
