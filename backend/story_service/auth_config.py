"""Configuracion del grupo de usuarios de Cognito y lista de correos permitidos (u4, BR4.3, BR4.7).

Solo valores de configuracion, sin secretos: el emisor y la direccion de las claves publicas
se derivan unicamente de la region y del identificador del grupo (security-design.md), nunca
de un valor del token.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from story_service.models import AllowedAccount

MAX_ALLOWED_EMAILS = 50
_REGION_SHAPE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_POOL_SHAPE = re.compile(r"^[A-Za-z0-9]+(?:[_-][A-Za-z0-9]+)*$")
_ALLOWED_SEPARATOR = ","


@dataclass(frozen=True)
class IdentityProviderConfig:
    region: str
    user_pool_id: str
    app_client_id: str

    def __post_init__(self) -> None:
        for name, value in (
            ("region", self.region),
            ("user_pool_id", self.user_pool_id),
            ("app_client_id", self.app_client_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"El campo obligatorio '{name}' no puede estar vacío")
        if not _REGION_SHAPE.match(self.region):
            raise ValueError("La región del grupo de usuarios tiene un formato no válido")
        if not _POOL_SHAPE.match(self.user_pool_id):
            raise ValueError("El identificador del grupo de usuarios tiene un formato no válido")

    @property
    def issuer(self) -> str:
        return f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"

    @property
    def jwks_url(self) -> str:
        return f"{self.issuer}/.well-known/jwks.json"

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> IdentityProviderConfig | None:
        """Los tres valores, o None si falta alguno (el servicio falla cerrado, BR4.5)."""
        region = (env.get("COGNITO_REGION") or "").strip()
        pool = (env.get("COGNITO_USER_POOL_ID") or "").strip()
        client = (env.get("COGNITO_APP_CLIENT_ID") or "").strip()
        if not (region and pool and client):
            return None
        return cls(region, pool, client)


def parse_allowed_emails(raw: str | None) -> frozenset[str]:
    """Correos separados por comas, en minúsculas. Más de 50 o una entrada rota: ValueError."""
    entries = [part for part in (raw or "").split(_ALLOWED_SEPARATOR) if part.strip()]
    if len(entries) > MAX_ALLOWED_EMAILS:
        raise ValueError(f"La lista de correos permitidos no puede superar {MAX_ALLOWED_EMAILS}")
    return frozenset(AllowedAccount.create(entry).email for entry in entries)
