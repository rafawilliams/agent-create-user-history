"""Ayudas de las pruebas de u4: claves RSA de prueba, tokens firmados y servidor de claves simulado.

Nunca se llama a Cognito ni a AWS: el par de claves se genera aqui y el servidor de claves es un
doble. Los correos y los identificadores son inventados.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Callable, Mapping

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from story_service.auth_config import IdentityProviderConfig
from story_service.jwks_store import JwksStore

REGION = "us-east-1"
POOL = "us-east-1_TestPool1"
CLIENT = "test-client-id"
CONFIG = IdentityProviderConfig(REGION, POOL, CLIENT)
KID = "kid-principal"
EMAIL = "ana.perez@ejemplo.com"
NOW = 1_800_000_000.0  # reloj fijo de las pruebas (segundos desde 1970)
EIGHT_HOURS = 8 * 3600


def generate_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


PRIVATE_KEY = generate_key()
OTHER_PRIVATE_KEY = generate_key()


def jwk_for(private_key: rsa.RSAPrivateKey, kid: str = KID, **overrides: object) -> dict:
    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"kid": kid, "alg": "RS256", "use": "sig", **overrides})
    return jwk


def jwks_bytes(*jwks: dict) -> bytes:
    return json.dumps({"keys": list(jwks)}).encode()


def valid_claims(**overrides: object) -> dict:
    claims: dict[str, object] = {
        "iss": CONFIG.issuer,
        "aud": CLIENT,
        "token_use": "id",
        "sub": "sub-de-prueba-1",
        "jti": "jti-de-prueba-1",
        "email": EMAIL,
        "email_verified": True,
        "identities": [{"providerName": "Google", "userId": "1"}],
        "iat": int(NOW) - 60,
        "auth_time": int(NOW) - 120,
        "exp": int(NOW) + 3600,
    }
    claims.update(overrides)
    return {key: value for key, value in claims.items() if value is not None}


def sign(
    claims: Mapping[str, object] | None = None,
    key: rsa.RSAPrivateKey = PRIVATE_KEY,
    kid: str | None = KID,
    algorithm: str = "RS256",
) -> str:
    headers = {"kid": kid} if kid is not None else {}
    return jwt.encode(dict(claims or valid_claims()), key, algorithm=algorithm, headers=headers)


def b64(data: dict) -> str:
    raw = json.dumps(data).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def unsigned_token(claims: Mapping[str, object] | None = None) -> str:
    """Token con algoritmo 'none' y sin firma."""
    return (
        f"{b64({'alg': 'none', 'typ': 'JWT', 'kid': KID})}.{b64(dict(claims or valid_claims()))}."
    )


def hs256_token(secret: str = "secreto-de-prueba-largo-para-hs256-0123456789") -> str:
    return jwt.encode(valid_claims(), secret, algorithm="HS256", headers={"kid": KID})


class FakeClock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeKeyServer:
    """Servidor de claves simulado: cuenta las descargas y puede fallar o devolver basura."""

    def __init__(self, body: bytes | None = None) -> None:
        self.body = body if body is not None else jwks_bytes(jwk_for(PRIVATE_KEY))
        self.error: Exception | None = None
        self.urls: list[str] = []
        self.on_fetch: Callable[[], None] | None = None

    @property
    def calls(self) -> int:
        return len(self.urls)

    def __call__(self, url: str) -> bytes:
        self.urls.append(url)
        if self.on_fetch is not None:
            self.on_fetch()
        if self.error is not None:
            raise self.error
        return self.body


def make_store(server: FakeKeyServer | None = None, clock: FakeClock | None = None) -> JwksStore:
    return JwksStore(CONFIG.jwks_url, fetcher=server or FakeKeyServer(), clock=clock or FakeClock())
