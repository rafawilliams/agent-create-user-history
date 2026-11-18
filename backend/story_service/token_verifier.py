"""Verificador real de la sesion con tokens de identidad de Amazon Cognito (C3, BR4.2 a BR4.5).

El orden de los pasos es el fijo de security-design.md; el primero que falla corta y devuelve su
motivo. Todo error inesperado falla cerrado con el motivo `unknown`, sin traza ni datos del token.
"""

from __future__ import annotations

import json
import math
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import jwt
from jwt.api_jws import decode_complete

from story_service.account_allowlist import AccountAllowlist, email_in, is_verified_email
from story_service.auth_config import IdentityProviderConfig
from story_service.jwks_store import JwksStore, KeyNotFoundError, KeysUnavailableError
from story_service.models import Session, SessionInvalid, SessionInvalidReason

REQUIRED_ALGORITHM = "RS256"
CLOCK_TOLERANCE_SECONDS = 60
MAX_SESSION_SECONDS = 8 * 3600
_TOKEN_PARTS = 3

_R = SessionInvalidReason


def _invalid(reason: SessionInvalidReason) -> SessionInvalid:
    return SessionInvalid(reason=reason)


def _number(value: object) -> float | None:
    """Fecha numérica de un claim; un booleano o un texto no cuentan."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    number = float(value)
    # json.loads accepts NaN and Infinity: a comparison with NaN is always false and would
    # silently skip the expiry checks.
    return number if math.isfinite(number) else None


def _provider(claims: dict[str, Any]) -> str | None:
    identities = claims.get("identities")
    if not isinstance(identities, list) or not identities:
        return None
    first = identities[0]
    name = first.get("providerName") if isinstance(first, dict) else None
    if not isinstance(name, str):
        return None
    lowered = name.strip().lower()
    # Exact names only: u6-infrastructure must name the Cognito identity providers this way.
    return lowered if lowered in ("google", "microsoft") else None


def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(int(epoch_seconds), UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class CognitoSessionVerifier:
    """Implementa SessionVerifier (C3). Sin estado propio: la copia de claves vive en JwksStore."""

    def __init__(
        self,
        config: IdentityProviderConfig,
        jwks: JwksStore,
        allowlist: AccountAllowlist,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._config = config
        self._jwks = jwks
        self._allowlist = allowlist
        self._clock = clock

    def verify_session(self, credential: str | None) -> Session | SessionInvalid:
        try:
            return self._verify(credential)
        except Exception:  # falla cerrado: nunca una traza ni un detalle interno (NFR1.6)
            return _invalid(_R.UNKNOWN)

    def _verify(self, credential: str | None) -> Session | SessionInvalid:
        # 1. Configuración presente (la región, el grupo y el cliente ya vienen validados).
        try:
            allowed = self._allowlist.emails()
        except ValueError:
            return _invalid(_R.NOT_CONFIGURED)
        if not allowed:
            return _invalid(_R.NOT_CONFIGURED)

        # 2. Credencial presente y con forma de token.
        token = (credential or "").strip()
        if not token:
            return _invalid(_R.MISSING)
        if len(token.split(".")) != _TOKEN_PARTS:
            return _invalid(_R.MALFORMED)

        # 3. Encabezado: RS256 y kid, decidido antes de buscar ninguna clave.
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError:
            return _invalid(_R.MALFORMED)
        kid = header.get("kid")
        if header.get("alg") != REQUIRED_ALGORITHM or not isinstance(kid, str) or not kid:
            return _invalid(_R.BAD_SIGNATURE)
        if "crit" in header:  # RFC 7515: unknown critical extensions must be rejected
            return _invalid(_R.BAD_SIGNATURE)

        # 4. Clave del kid (regla única).
        try:
            key = self._jwks.get_key(kid)
        except KeyNotFoundError:
            return _invalid(_R.BAD_SIGNATURE)
        except KeysUnavailableError:
            return _invalid(_R.KEYS_UNAVAILABLE)

        # 5. Firma, con el algoritmo fijado aquí y la clave pasada por separado.
        try:
            decoded = decode_complete(token, key, algorithms=[REQUIRED_ALGORITHM])
        except jwt.InvalidSignatureError:
            return _invalid(_R.BAD_SIGNATURE)
        except jwt.DecodeError:
            return _invalid(_R.MALFORMED)
        except jwt.PyJWTError:
            return _invalid(_R.BAD_SIGNATURE)
        try:
            claims = json.loads(decoded["payload"])
        except ValueError:
            return _invalid(_R.MALFORMED)
        if not isinstance(claims, dict):
            return _invalid(_R.MALFORMED)

        # 6. Claims.
        claims_verdict = self._check_claims(claims)
        if isinstance(claims_verdict, SessionInvalid):
            return claims_verdict
        expires_at = claims_verdict

        # 7. Cuenta.
        email = claims.get("email")
        if not (is_verified_email(claims.get("email_verified")) and email_in(allowed, email)):
            return _invalid(_R.ACCOUNT_NOT_ALLOWED)

        # 8. Resultado.
        provider = _provider(claims)
        if provider is None:
            return _invalid(_R.UNKNOWN)
        sub = claims["sub"]
        jti = claims.get("jti")
        return Session(
            session_id=jti if isinstance(jti, str) and jti else sub,
            account_id=sub,
            provider=provider,
            expires_at=_iso(expires_at),
        )

    def _check_claims(self, claims: dict[str, Any]) -> float | SessionInvalid:
        """Valida emisor, audiencia, tipo y fechas; devuelve el vencimiento efectivo."""
        if claims.get("iss") != self._config.issuer:
            return _invalid(_R.WRONG_ISSUER)
        if claims.get("aud") != self._config.app_client_id:
            return _invalid(_R.WRONG_AUDIENCE)
        if claims.get("token_use") != "id":
            return _invalid(_R.WRONG_TOKEN_USE)
        sub = claims.get("sub")
        if not isinstance(sub, str) or not sub:
            return _invalid(_R.MALFORMED)

        now = self._clock()
        exp, iat, nbf = (_number(claims.get(name)) for name in ("exp", "iat", "nbf"))
        if exp is None or (iat is None and nbf is None):
            return _invalid(_R.EXPIRED)
        # A date claim that is present but not a finite number is a defect, not "absent".
        if ("iat" in claims and iat is None) or ("nbf" in claims and nbf is None):
            return _invalid(_R.EXPIRED)
        if now > exp + CLOCK_TOLERANCE_SECONDS:
            return _invalid(_R.EXPIRED)
        for start in (iat, nbf):
            if start is not None and start > now + CLOCK_TOLERANCE_SECONDS:
                return _invalid(_R.EXPIRED)
        started = _number(claims.get("auth_time"))
        if started is None:
            started = iat if iat is not None else nbf
        limit = started + MAX_SESSION_SECONDS
        if now > limit:
            return _invalid(_R.EXPIRED)
        return min(exp, limit)
