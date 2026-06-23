import json
import ssl
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cached_property
from types import MappingProxyType
from typing import Optional
from urllib import request, parse


@dataclass
class KeycloakAuthClient:
    # Seconds shaved off the server-reported token lifetime to avoid
    # using a token that expires mid-request. Bump to 10-30 if clock
    # skew between this host and the Keycloak server is a concern.
    TOKEN_EXPIRY_SAFETY_MARGIN_SECONDS = 5

    server_url: str
    client_id: str
    realm_name: str
    client_secret_key: str
    cert_path: Optional[str] = None

    def __post_init__(self):
        self.server_url = self.server_url.rstrip("/")
        self.token = None
        self.expiry = datetime.now()

    @cached_property
    def ssl_context(self):
        ctx = None
        if self.cert_path:
            ctx = ssl.create_default_context()
            ctx.load_verify_locations(cafile=self.cert_path)
        return ctx

    @cached_property
    def openid_auth_url(self):
        return (
            f"{self.server_url}/realms/{self.realm_name}/protocol/openid-connect/token"
        )

    @cached_property
    def post_data(self):
        return MappingProxyType(
            {
                "grant_type": "client_credentials",
                "client_secret": self.client_secret_key,
                "client_id": self.client_id,
                "scope": "openid",
            }
        )

    def _post(self, url, data):
        d = parse.urlencode(data)
        res = request.urlopen(
            request.Request(url, method="POST", data=d.encode("utf-8"), headers={}),
            context=self.ssl_context,
        )
        return json.load(res)

    @property
    def expired(self):
        return datetime.now() >= self.expiry

    def get_auth_token(self):
        if self.token is None or self.expired:
            self.token_response = self._post(self.openid_auth_url, self.post_data)
            self.token = self.token_response["access_token"]
            self.expiry = datetime.now() + timedelta(
                seconds=self.token_response.get("expires_in", 0)
                - self.TOKEN_EXPIRY_SAFETY_MARGIN_SECONDS
            )

        return f"Bearer {self.token}"
